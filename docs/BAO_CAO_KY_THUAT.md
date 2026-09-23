# Báo Cáo Kỹ Thuật — Agri Price Blockchain

**Tên đề tài:** Hệ thống xác thực và truy xuất dữ liệu giá nông sản bằng Blockchain  
**Nhóm:** TrongLeBa111 / Agri-cul_Blockchain  
**Repo:** https://github.com/TrongLeBa111/Agri-cul_Blockchain

---

## 1. Bối cảnh và vấn đề

Dữ liệu giá nông sản (lúa gạo, cà phê, ca cao, bông vải...) được thu thập từ nhiều nguồn khác nhau như World Bank, Yahoo Finance, FAO. Khi dữ liệu này được lưu trong database thông thường, nảy sinh các vấn đề:

- **Ai đó có thể sửa giá** trong database mà không để lại dấu vết.
- **Không có cách nào** để người dùng bên ngoài kiểm chứng dữ liệu có đúng với bản gốc hay không.
- Thiếu **tính minh bạch** về nguồn gốc và thời điểm ghi nhận.

**Giải pháp:** Không cần đưa toàn bộ dữ liệu lên blockchain (tốn kém, chậm). Chỉ cần **lưu "dấu vân tay số" (hash) của mỗi bản ghi** lên smart contract. Sau đó bất kỳ ai cũng có thể tạo lại hash từ dữ liệu hiện tại và so sánh với hash đã lưu trên blockchain để biết dữ liệu có bị sửa hay không.

---

## 2. Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────────┐
│                         OFF-CHAIN                               │
│                                                                 │
│  World Bank API ──► price_records_seed.csv ──► backend/app.py  │
│                              (140 bản ghi)         (HTTP API)  │
│                                    │                    │       │
│                          backend/hashing.py             │       │
│                        (tạo canonical JSON              │       │
│                          + SHA-256 hash)                │       │
└────────────────────────────────────┼────────────────────┼───────┘
                                     │                    │
                        ┌────────────▼────────────────────▼────┐
                        │           ON-CHAIN (Blockchain)       │
                        │                                       │
                        │   contracts/AgriPriceRegistry.sol     │
                        │   ┌─────────────────────────────┐    │
                        │   │  mapping(recordId => Proof)  │    │
                        │   │  Proof {                      │    │
                        │   │    dataHash  (bytes32)        │    │
                        │   │    source    (string)         │    │
                        │   │    createdBy (address)        │    │
                        │   │    createdAt (uint256)        │    │
                        │   │  }                            │    │
                        │   └─────────────────────────────┘    │
                        └───────────────────────────────────────┘
```

**Nguyên tắc thiết kế:**
- **Off-chain:** Lưu toàn bộ thông tin chi tiết giá → Database/CSV
- **On-chain:** Chỉ lưu `recordId`, `dataHash`, `source`, `createdBy`, `createdAt` → Smart Contract

---

## 3. Cơ chế Hash — "Dấu vân tay số"

### 3.1. Hash là gì và tại sao dùng hash?

Hash (SHA-256) là hàm **một chiều**: cùng một nội dung đầu vào **luôn** cho ra cùng một chuỗi 64 ký tự hex đầu ra. Chỉ cần thay đổi **một ký tự** trong dữ liệu, hash sẽ thay đổi **hoàn toàn**.

```
"rice, 0.471 USD/kg, 2026-08-01"  →  SHA-256  →  0xc1eba559...
"rice, 0.472 USD/kg, 2026-08-01"  →  SHA-256  →  0x9f3a7c2b...  (hoàn toàn khác)
```

**Không thể giải ngược:** Có hash không có nghĩa là biết được giá gốc. Hash chỉ dùng để **so sánh**, không phải để lưu trữ thông tin.

### 3.2. Canonical JSON — Chuẩn hóa trước khi hash

Vấn đề: Nếu không chuẩn hóa, cùng một bản ghi có thể tạo ra hash khác nhau chỉ vì:
- `"Rice"` vs `"rice"` (chữ hoa/thường)
- `0.47` vs `0.470000` (số chữ số thập phân)
- Thứ tự key trong JSON thay đổi

**Giải pháp — Canonical JSON** (xem [`backend/hashing.py`](../backend/hashing.py)):

```python
# Bước 1: Lấy đúng các trường cần hash (không lấy id, tx_hash, status)
HASH_FIELDS = (
    "commodity",      # "rice"
    "price_date",     # "2026-08-01"
    "region",         # "global"
    "country",        # "global"
    "price_usd_per_kg",  # "0.471000"
    "currency",       # "USD"
    "unit",           # "kg"
    "source",         # "WORLD_BANK"
    "is_imputed",     # false
)

# Bước 2: Chuẩn hóa từng trường
canonical = {
    "commodity": "rice",          # lowercase
    "price_date": "2026-08-01",   # YYYY-MM-DD
    "region": "global",           # lowercase
    "country": "global",
    "price_usd_per_kg": "0.471000",  # 6 chữ số sau dấu phẩy
    "currency": "USD",            # UPPERCASE
    "unit": "kg",                 # lowercase
    "source": "WORLD_BANK",       # UPPERCASE
    "is_imputed": false,          # boolean thật, không phải string
}

# Bước 3: Bọc thêm domain và version (để hash của hệ thống này không trùng với hệ thống khác)
payload = {
    "domain": "AGRI_PRICE_BLOCKCHAIN",
    "version": "v1",
    "record": canonical
}

# Bước 4: Serialize thành JSON không khoảng trắng, key theo thứ tự cố định
json_str = json.dumps(payload, ensure_ascii=True, separators=(',', ':'), sort_keys=False)

# Bước 5: SHA-256
data_hash = "0x" + hashlib.sha256(json_str.encode("utf-8")).hexdigest()
# → "0xc1eba5590372359566fb8e5e13c7b8b5691ca9d58620e45949ba4944ed116f5d"
```

### 3.3. Fingerprint — Rút gọn cho hiển thị

Hash 64 ký tự dài khó nhìn. Hệ thống tạo thêm **fingerprint** để hiển thị trên UI:

```
AGR-v1-C1EBA559
│   │   └── 8 ký tự đầu của hash (chỉ dùng hiển thị)
│   └── phiên bản hash rule
└── prefix nhận biết hệ thống
```

**Lưu ý:** Fingerprint chỉ để hiển thị. Xác minh phải dùng hash đầy đủ.

### 3.4. Những trường KHÔNG đưa vào hash

| Trường | Lý do không hash |
|---|---|
| `price_id` / `id` | Là mã tra cứu kỹ thuật, không phải nội dung cần bảo vệ |
| `ingested_at` | Có thể thay đổi khi re-import dữ liệu |
| `blockchain_tx_hash` | Chỉ xuất hiện SAU khi ghi blockchain |
| `blockchain_status` | Trạng thái kỹ thuật, thay đổi liên tục |

---

## 4. Smart Contract — AgriPriceRegistry

**File:** [`contracts/AgriPriceRegistry.sol`](../contracts/AgriPriceRegistry.sol)  
**Ngôn ngữ:** Solidity 0.8.20  
**Blockchain:** Hardhat local (chainId 31337), tương thích mọi EVM chain

### 4.1. Cấu trúc dữ liệu on-chain

```solidity
struct PriceRecordProof {
    string  recordId;    // ID bản ghi (price_id từ database)
    bytes32 dataHash;    // SHA-256 hash của canonical JSON
    string  source;      // Nguồn dữ liệu: "WORLD_BANK", "YAHOO_FINANCE"
    address createdBy;   // Địa chỉ ví ghi bản ghi
    uint256 createdAt;   // Unix timestamp lúc anchor
    bool    exists;      // Kiểm tra record có tồn tại không
}

mapping(string => PriceRecordProof) private records;
```

### 4.2. Ba hàm chính

#### `anchorPriceRecord` — Ghi hash lên blockchain

```solidity
function anchorPriceRecord(
    string calldata recordId,   // "21c34ff9245babdff5526929752bdbd9"
    bytes32 dataHash,           // 0xc1eba559...
    string calldata source      // "WORLD_BANK"
) external
```

**Quy tắc nghiệp vụ:**
- `recordId` không được rỗng → revert `EmptyRecordId`
- `dataHash` không được là zero → revert `EmptyHash`
- Mỗi `recordId` chỉ được anchor **một lần** → revert `RecordAlreadyAnchored`

**Tại sao chỉ anchor một lần?** Đảm bảo hash gốc không bị ghi đè. Nếu dữ liệu cần cập nhật, tạo bản ghi mới với recordId mới.

#### `verifyPriceRecord` — Xác minh dữ liệu

```solidity
function verifyPriceRecord(
    string calldata recordId,
    bytes32 dataHash
) external view returns (bool)
```

So sánh `dataHash` truyền vào với `dataHash` đã lưu. Trả về `true` nếu khớp, `false` nếu khác (đã bị sửa).

#### `getPriceRecordProof` — Đọc bằng chứng

```solidity
function getPriceRecordProof(string calldata recordId)
    external view returns (
        bytes32 dataHash,
        string memory source,
        address createdBy,
        uint256 createdAt,
        bool exists
    )
```

#### Lifecycle Events — Vòng đời bản ghi

```solidity
struct LifecycleEvent {
    string  recordId;
    string  eventType;    // "INGESTED", "VERIFIED", "UPDATED"...
    bytes32 eventHash;    // Hash của metadata event
    string  metadataUri;  // Link đến metadata chi tiết
    address createdBy;
    uint256 createdAt;
}
```

Cho phép ghi nhận các sự kiện xảy ra với bản ghi sau khi anchor (ví dụ: đã kiểm chứng, đã cập nhật, đã vận chuyển...).

### 4.3. Events (Sự kiện blockchain)

```solidity
event PriceRecordAnchored(
    string indexed recordId,
    bytes32 indexed dataHash,
    string source,
    address indexed createdBy,
    uint256 createdAt
);
```

Events được lưu vĩnh viễn trong log của blockchain, không thể xóa. Đây là bằng chứng không thể chối cãi về thời điểm hash được ghi.

### 4.4. Test kết quả

```
npx hardhat test
  AgriPriceRegistry
    ✓ anchors a price record successfully
    ✓ rejects duplicate anchors with RecordAlreadyAnchored
    ✓ rejects an empty record id with EmptyRecordId
    ✓ rejects an empty hash with EmptyHash
    ✓ returns the stored price record proof
    ✓ verifies true when the hash matches
    ✓ verifies false when the hash does not match
    ✓ adds a lifecycle event after the record is anchored
    ✓ reverts lifecycle events before anchor with RecordNotAnchored
    ✓ returns the stored lifecycle event

  10 passing (667ms)
```

---

## 5. Data Flow — Luồng dữ liệu

### 5.1. Luồng ANCHOR (Ghi bằng chứng)

```
Người dùng bấm "Anchor"
        │
        ▼
POST /api/prices/{id}/anchor
        │
        ▼
backend/hashing.py:
  canonical_record(row)         ← chuẩn hóa 9 trường
  canonical_payload(record)     ← thêm domain + version
  canonical_json(record)        ← serialize JSON
  SHA-256(json_str)             ← tạo dataHash
        │
        ▼
blockchain_service.py:
  [Nếu Hardhat đang chạy]
    anchorPriceRecord(recordId, dataHash, source)
    → nhận transactionHash từ blockchain thật
  [Nếu không]
    LocalProofLedger.anchor_price_record()
    → lưu vào proof_ledger.json (fallback)
        │
        ▼
Trả về response:
  {
    "data_hash": "0xc1eba559...",
    "transaction_hash": "0x57e254...",
    "blockchain_status": "ANCHORED"
  }
```

### 5.2. Luồng VERIFY (Xác minh)

```
Người dùng bấm "Verify"
        │
        ▼
GET /api/prices/{id}/verify
        │
        ▼
1. Lấy bản ghi hiện tại từ database/CSV
        │
        ▼
2. Tạo currentHash từ dữ liệu hiện tại
   (cùng quy tắc chuẩn hóa như lúc anchor)
        │
        ▼
3. Đọc storedHash từ smart contract
   getPriceRecordProof(recordId).dataHash
        │
        ▼
4. So sánh currentHash vs storedHash
        │
        ├── Khớp  → "verified": true,  "blockchain_status": "VERIFIED"
        ├── Khác  → "verified": false, "blockchain_status": "TAMPERED"
        └── Chưa anchor → "blockchain_status": "NOT_ANCHORED"
```

**Kịch bản demo "tampered":**
1. Anchor bản ghi rice với giá 0.471 USD/kg → hash H1 lưu trên blockchain
2. Sửa giá trong database thành 0.999 USD/kg
3. Verify → tạo hash H2 từ giá mới → H2 ≠ H1 → **TAMPERED**

---

## 6. Backend Service Layer

### 6.1. BlockchainService — Bridge Python → Hardhat

**File:** [`backend/blockchain_service.py`](../backend/blockchain_service.py)

```
BlockchainService.__init__()
    │
    ├── Đọc ABI từ artifacts/contracts/AgriPriceRegistry.sol/AgriPriceRegistry.json
    ├── Đọc địa chỉ contract từ deployments/localhost.json
    ├── Kết nối web3.py → http://127.0.0.1:8545
    │
    ├── [Kết nối được] → mode = "hardhat"  ← gọi contract thật
    └── [Không kết nối] → mode = "local"   ← dùng JSON ledger fallback
```

**Thiết kế graceful degradation:** Nếu Hardhat node không chạy, hệ thống tự động dùng `LocalProofLedger` (file JSON) thay thế — đảm bảo demo vẫn chạy được mà không cần setup phức tạp.

### 6.2. API Endpoints

| Endpoint | Mô tả |
|---|---|
| `GET /api/prices` | Danh sách giá, filter theo `?commodity=&source=&region=` |
| `GET /api/prices/{id}` | Chi tiết + `data_hash`, `fingerprint`, `blockchain_status` |
| `POST /api/prices/{id}/anchor` | Tạo hash → ghi blockchain |
| `GET /api/prices/{id}/verify` | Xác minh dữ liệu |
| `GET /api/prices/{id}/qr-payload` | Payload cho QR code |
| `GET /api/transactions` | Lịch sử giao dịch anchor |
| `GET /api/stats` | Tổng quan: tổng records, đã anchor, đã verify |
| `GET /verify/{id}` | Trang HTML xác minh (hiển thị sau quét QR) |

---

## 7. Dữ liệu Demo

**Nguồn:** World Bank Pink Sheet (công khai, không cần token)  
**Script fetch:** `scripts/fetch_public_blockchain_seed.py`

```
140 bản ghi
4 commodity: rice, coffee, cocoa, cotton
Khoảng thời gian: 10/2023 → 08/2026 (monthly)
Region: global / World Bank global price index
```

**Ví dụ bản ghi:**

| price_id | commodity | price_date | price_usd_per_kg | source |
|---|---|---|---|---|
| `21c34ff9...` | rice | 2026-08-01 | 0.471000 | WORLD_BANK |
| `a0a71143...` | cotton | 2026-08-01 | 2.110000 | WORLD_BANK |
| `8edb40dc...` | coffee | 2026-08-01 | 7.970000 | WORLD_BANK |

---

## 8. Kịch bản Demo cho Báo Cáo

### Bước 1: Mở Dashboard tổng quan
- `GET /api/stats` → Thấy 140 bản ghi, 0 đã anchor
- Mục tiêu: giải thích hệ thống có bao nhiêu dữ liệu, bao nhiêu đã được bảo vệ bằng blockchain

### Bước 2: Xem danh sách giá nông sản
- `GET /api/prices?commodity=rice` → Lọc chỉ thấy lúa gạo
- Chỉ ra cột `blockchain_status = NOT_ANCHORED` → dữ liệu chưa được bảo vệ

### Bước 3: Anchor một bản ghi
- Chọn bản ghi rice ngày 2026-08-01
- `POST /api/prices/21c34ff9.../anchor`
- **Giải thích với giám khảo:**
  > "Lúc này backend lấy 9 trường dữ liệu quan trọng của bản ghi, chuẩn hóa theo quy tắc cố định, serialize thành JSON, rồi tạo SHA-256 hash. Hash này được gửi lên smart contract `AgriPriceRegistry` và lưu vĩnh viễn trên blockchain. Chúng ta nhận về transaction hash để làm bằng chứng."
- Hiển thị: `data_hash = 0xc1eba559...`, `transaction_hash = 0x57e254...`

### Bước 4: Verify dữ liệu hợp lệ
- `GET /api/prices/21c34ff9.../verify`
- Kết quả: `"verified": true`, `"blockchain_status": "VERIFIED"`
- Hiển thị badge xanh ✅

### Bước 5: Demo giả lập tampered (dữ liệu bị sửa)
- Sửa giá trong CSV/database: `0.471` → `0.999`
- Verify lại → `"verified": false`, `"blockchain_status": "TAMPERED"`
- **Giải thích:**
  > "Hash được tạo từ dữ liệu mới (0.999) là `0x9f3a7c2b...`, khác hoàn toàn với hash `0xc1eba559...` đã lưu trên blockchain. Hệ thống phát hiện ngay dữ liệu đã bị sửa, dù chỉ thay đổi 1 con số nhỏ."

### Bước 6: QR Code (tùy chọn)
- `GET /api/prices/21c34ff9.../qr-payload` → URL xác minh
- Quét QR → mở trang `GET /verify/21c34ff9...` → hiển thị trạng thái

---

## 9. Giá trị kỹ thuật và học thuật

### 9.1. Tại sao không đưa toàn bộ dữ liệu lên blockchain?

| Tiêu chí | Lưu toàn bộ on-chain | Chỉ lưu hash (cách này) |
|---|---|---|
| Chi phí gas | Rất cao (~1000x) | Rất thấp (bytes32 cố định) |
| Tốc độ | Chậm | Nhanh |
| Bảo mật giá cả | Giá lộ hết | Giá vẫn off-chain, bảo mật |
| Khả năng xác minh | Có | Có (qua hash) |
| Phù hợp thực tế | Không | ✅ Phù hợp |

### 9.2. Hash vs Encryption

| | Encryption (Mã hóa) | Hashing (băm) |
|---|---|---|
| Chiều | Hai chiều (có thể giải mã) | Một chiều (không giải ngược) |
| Mục đích | Bảo mật nội dung | Xác minh tính toàn vẹn |
| Key | Cần key để mã hóa/giải mã | Không cần key |
| Trong project này | Không dùng | Dùng SHA-256 |

### 9.3. Tại sao cần chuẩn hóa (canonical JSON)?

Nếu không chuẩn hóa, cùng một bản ghi nhưng:
- Backend A dùng `"Rice"`, Backend B dùng `"rice"` → **hai hash khác nhau**
- Giá `0.47` vs `0.470000` → **hai hash khác nhau**

Canonical JSON đảm bảo: **cùng dữ liệu luôn → cùng hash**, bất kể hệ thống nào tạo.

---

## 10. Phân công và đóng góp

### Thành viên 1 (Quản lý, Data Flow & Blockchain)
- Thiết kế kiến trúc tổng thể
- Viết smart contract `AgriPriceRegistry.sol`
- Viết toàn bộ module hashing (`canonical JSON`, `SHA-256`, `fingerprint`)
- Xây `BlockchainService` bridge Python → Hardhat
- Thiết kế và implement 10 API endpoints
- Viết 10 Hardhat test cases (10/10 pass)
- Thu thập 140 bản ghi dữ liệu thực từ World Bank
- Viết tài liệu kỹ thuật và handoff

### Thành viên 2 (Visualization & Frontend)
- Dashboard tổng quan
- Danh sách và tìm kiếm giá
- Màn hình chi tiết + xác minh blockchain
- Lịch sử giao dịch
- Tích hợp QR code

### Thành viên 3 (Báo cáo & Kiểm thử)
- Đề cương, use case, sequence diagram
- Test plan và test case
- Ghi kết quả kiểm thử + ảnh minh chứng
- Slide thuyết trình

---

## 11. Stack công nghệ

| Layer | Công nghệ | Lý do chọn |
|---|---|---|
| Smart Contract | Solidity 0.8.20 | Ngôn ngữ chuẩn EVM, hỗ trợ custom error |
| Blockchain local | Hardhat (chainId 31337) | Nhanh, miễn phí, dễ reset |
| Contract bridge | web3.py | Giao tiếp Python → EVM RPC |
| Backend | Python stdlib HTTP | Không cần framework nặng cho MVP |
| Hashing | SHA-256 (Python hashlib) | Chuẩn công nghiệp, nhẹ, nhanh |
| Fallback ledger | JSON file | Demo được ngay cả không có Hardhat |
| Seed data | World Bank Pink Sheet | Dữ liệu thực, miễn phí, có API công khai |
| Test | Hardhat + Mocha + Chai | Ecosystem chuẩn cho Solidity |

---

## 12. Câu hỏi thường gặp từ giám khảo

**Q: "Tại sao không dùng IPFS hay Filecoin thay vì lưu trên contract?"**  
> IPFS phù hợp lưu file lớn. Trong project này hash chỉ là `bytes32` (32 bytes) — cực nhỏ, lưu thẳng trên contract là tối ưu nhất.

**Q: "Nếu bị mất file CSV, hash trên blockchain có còn dùng được không?"**  
> Blockchain chỉ lưu hash. Để verify phải có dữ liệu gốc. Đây là lý do hệ thống thực tế cần database đáng tin cậy. Trong demo, CSV là database.

**Q: "Hardhat khác Ethereum thật chỗ nào?"**  
> Hardhat là local EVM node cho development. Contract code viết bằng Solidity hoàn toàn tương thích — deploy lên Ethereum, Polygon, BSC mà không cần sửa code.

**Q: "SHA-256 có thể bị tấn công collision không?"**  
> Về mặt lý thuyết collision tồn tại, nhưng xác suất cực kỳ nhỏ (~1/2^256). Trong thực tế, SHA-256 được dùng trong Bitcoin và được coi là an toàn cho mục đích xác minh toàn vẹn.

**Q: "price_id được tạo như thế nào?"**  
> `price_id = MD5(source | commodity | price_date | region)` — tạo từ dbt model `gold.fact_price_daily`. Đây là ID tự nhiên, duy nhất theo nghiệp vụ.
