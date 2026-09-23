# Giai Doan 1 - Data Flow Va Smart Contract

Tai lieu nay la phan viec giai doan 1 cua thanh vien quan ly va lap trinh chinh phan luong du lieu, cach tao hash va hop dong thong minh.

## 1. Muc tieu giai doan 1

Trong giai doan nay da co code MVP de chot cach du lieu di qua he thong va cach blockchain xac minh du lieu.

Ket qua can co:

- Data flow end-to-end.
- Data model toi thieu cho ban ghi gia nong san.
- Quy tac tao hash.
- Thiet ke smart contract.
- API contract ban dau de ban lam UI/backend co the tich hop.
- Checklist cho giai doan code.

## 2. Pham vi phan cua ban

Ban phu trach cac phan sau:

- Xac dinh du lieu nao la du lieu goc can bao ve.
- Chuan hoa ban ghi truoc khi tao hash.
- Tao hash cho ban ghi gia nong san.
- Ghi hash va metadata len smart contract.
- Doc lai hash tu smart contract.
- Verify ban ghi trong database co khop voi blockchain khong.
- Cung cap format API/response cho ban lam visualization.

Dataset demo de khoi dong ma khong can MotherDuck token:

```text
data/sample/price_records_seed.csv
```

Luu y ve du lieu cu: `dbt/models` khong phai seed data truc tiep ma la cac SQL model tao Silver/Gold tables tu source MotherDuck `bronze.wb_prices_raw` va `bronze.yf_prices_raw`. Seed CSV cua blockchain dang map theo output `gold.fact_price_daily`; khi co MotherDuck token/runtime co the export `fact_price_daily` ra CSV de thay seed demo.

Export seed tu warehouse:

```bash
python scripts/export_blockchain_seed.py --limit 200
```

Neu MotherDuck token het han, co the crawl lai seed truc tiep tu nguon public:

```bash
python scripts/fetch_public_blockchain_seed.py --dry-run
python scripts/fetch_public_blockchain_seed.py --days 90 --commodity rice coffee cocoa cotton
```

Script nay lay World Bank Pink Sheet monthly prices va Yahoo Finance futures, sau do ghi cung schema CSV cho blockchain.

Neu chay qua Docker, can dam bao `.env` co `MOTHERDUCK_TOKEN` va pipeline da build xong `gold.fact_price_daily`, sau do co the chay export trong container co Python dependencies:

```bash
docker compose run --rm dbt dbt build --profiles-dir .
docker compose run --rm ingest python scripts/export_blockchain_seed.py --limit 200
```

## 3. Data flow tong the

```text
Nguoi dung nhap du lieu
        |
        v
Backend validate du lieu
        |
        v
Luu ban ghi vao database
        |
        v
Chuan hoa du lieu can bao ve
        |
        v
Tao dataHash
        |
        v
Goi smart contract de luu dataHash
        |
        v
Nhan transactionHash
        |
        v
Cap nhat database voi dataHash va transactionHash
        |
        v
UI hien thi trang thai blockchain
```

## 4. Data flow verify

```text
Nguoi dung bam Verify
        |
        v
Backend lay ban ghi tu database
        |
        v
Chuan hoa lai du lieu theo cung quy tac ban dau
        |
        v
Tao currentHash
        |
        v
Doc storedHash tu smart contract theo recordId
        |
        v
So sanh currentHash voi storedHash
        |
        v
Tra ve Verified hoac Tampered
```

## 5. Data model toi thieu

Sau khi xem project cu, data model nen dua tren bang gold `fact_price_daily` thay vi tu thiet ke moi hoan toan.

Bang `price_records` trong MVP blockchain co the map tu `gold.fact_price_daily`:

```text
id
price_id
commodity
price_date
region
country
price_usd_per_kg
currency
unit
source
is_imputed
ingested_at
data_hash
blockchain_tx_hash
blockchain_status
```

Bang `blockchain_transactions`:

```text
id
price_record_id
action
data_hash
tx_hash
contract_address
block_number
status
created_at
error_message
```

Trang thai `blockchain_status`:

```text
NOT_ANCHORED
PENDING
ANCHORED
VERIFIED
TAMPERED
FAILED
```

## 6. Du lieu dua vao hash

Chi hash cac truong dai dien cho noi dung nghiep vu, uu tien theo schema `fact_price_daily` cua project cu:

```text
commodity
price_date
region
country
price_usd_per_kg
currency
unit
source
is_imputed
```

Khong dua cac truong sau vao hash:

```text
id
price_id
ingested_at
data_hash
blockchain_tx_hash
blockchain_status
```

Ly do:

- `id`/`price_id` la ma dinh danh de tra cuu, khong nhat thiet la noi dung can bao ve trong MVP.
- `ingested_at` co the thay doi khi import lai du lieu.
- `tx_hash`, `blockchain_status` chi xuat hien sau khi ghi blockchain.

## 7. Quy tac chuan hoa du lieu

Truoc khi hash, backend phai tao object theo thu tu co dinh:

```json
{
  "commodity": "rice",
  "price_date": "2026-06-24",
  "region": "global",
  "country": "global",
  "price_usd_per_kg": "0.720000",
  "currency": "USD",
  "unit": "kg",
  "source": "WORLD_BANK",
  "is_imputed": false
}
```

Quy tac:

- Trim khoang trang dau/cuoi voi text.
- Chuyen commodity/source/currency ve dang thong nhat.
- Gia nen chuyen ve decimal co format on dinh, vi du 6 chu so sau dau phay.
- Ngay dung format `YYYY-MM-DD`.
- Cac key trong JSON giu dung thu tu nhu tren.

Hash de xuat:

```text
SHA-256(canonical_json)
```

Neu dung EVM/Solidity, co the chuyen hash nay thanh `bytes32` khi goi contract.

## 8. Thiet ke smart contract

Ten contract de xuat:

```text
AgriPriceRegistry
```

Struct luu on-chain:

```solidity
struct PriceRecordProof {
    string recordId;
    bytes32 dataHash;
    string source;
    address createdBy;
    uint256 createdAt;
    bool exists;
}
```

Mapping:

```solidity
mapping(string => PriceRecordProof) private records;
```

Event:

```solidity
event PriceRecordAnchored(
    string indexed recordId,
    bytes32 indexed dataHash,
    string source,
    address indexed createdBy,
    uint256 createdAt
);
```

Ham can co:

```solidity
function anchorPriceRecord(
    string calldata recordId,
    bytes32 dataHash,
    string calldata source
) external;

function getPriceRecordProof(
    string calldata recordId
) external view returns (
    bytes32 dataHash,
    string memory source,
    address createdBy,
    uint256 createdAt,
    bool exists
);

function verifyPriceRecord(
    string calldata recordId,
    bytes32 dataHash
) external view returns (bool);
```

Quy tac nghiep vu ban dau:

- Moi `recordId` chi duoc anchor mot lan.
- Neu du lieu thay doi sau khi anchor, verify phai tra ve false.
- Khong luu gia, ten nong san hoac thong tin chi tiet len blockchain trong MVP.

## 9. API contract ban dau

### Tao ban ghi gia

```text
POST /api/prices
```

Request:

```json
{
  "product_name": "lua",
  "market_location": "Can Tho",
  "price": 7200,
  "unit": "VND/kg",
  "recorded_date": "2026-09-22",
  "source": "agri-price-dwh"
}
```

Response:

```json
{
  "id": "price_001",
  "blockchain_status": "NOT_ANCHORED"
}
```

### Tim kiem/filter danh sach gia

```text
GET /api/prices?commodity=rice&source=WORLD_BANK&region=global
```

Tat ca query params deu optional. Backend filter theo partial text, khong phan biet hoa thuong.

### Ghi blockchain

```text
POST /api/prices/:id/anchor
```

Response:

```json
{
  "id": "price_001",
  "data_hash": "0x...",
  "transaction_hash": "0x...",
  "blockchain_status": "ANCHORED"
}
```

### Xac minh ban ghi

```text
GET /api/prices/:id/verify
```

Response hop le:

```json
{
  "id": "price_001",
  "current_hash": "0x...",
  "stored_hash": "0x...",
  "verified": true,
  "blockchain_status": "VERIFIED"
}
```

### Danh sach giao dich blockchain

```text
GET /api/transactions
```

Tra ve cac giao dich anchor va lifecycle ma backend da thuc hien trong local transaction cache/ledger.

### Thong ke dashboard

```text
GET /api/stats
```

Response:

```json
{
  "total_records": 20,
  "total_anchored": 1,
  "total_verified": 1,
  "total_unanchored": 19,
  "blockchain_backend": {
    "mode": "local",
    "rpc_url": "http://127.0.0.1:8545",
    "contract_address": null
  }
}
```

Response du lieu bi sua:

```json
{
  "id": "price_001",
  "current_hash": "0xabc...",
  "stored_hash": "0xdef...",
  "verified": false,
  "blockchain_status": "TAMPERED"
}
```

## 10. Diem ban giao cho ban lam visualization/backend

Ban phu trach visualization can cac truong sau de hien thi:

```text
id
product_name
market_location
price
unit
recorded_date
source
data_hash
blockchain_tx_hash
blockchain_status
verified
created_at
```

Trang thai UI nen hien thi:

- `NOT_ANCHORED`: chua ghi blockchain.
- `ANCHORED`: da ghi blockchain.
- `VERIFIED`: du lieu hop le.
- `TAMPERED`: du lieu khong khop blockchain.
- `FAILED`: ghi blockchain that bai.

## 11. Checklist hoan thanh giai doan 1 cua ban

- [x] Xac dinh du lieu on-chain va off-chain.
- [x] Xac dinh truong nao duoc dua vao hash.
- [x] Co data flow them moi va verify.
- [x] Co thiet ke smart contract.
- [x] Co API contract ban dau.
- [x] Kiem tra repo/dbt models de doi chieu schema that.
- [x] Chot stack code MVP: Hardhat, Python stdlib HTTP API, local JSON ledger fallback.
- [x] Tao skeleton source cho smart contract va blockchain service.
- [x] Viet Hardhat test cho smart contract.
- [x] Mo rong seed demo len 140 ban ghi thuc te tu World Bank Pink Sheet (2023-2026).
- [x] Them API filter/search, transactions va stats.

**Giai doan 1 HOAN THANH.** Toan bo API san sang, smart contract deploy duoc, 140 ban ghi seed that.
Buoc tiep theo: ban giao cho thanh vien 2 (Visualization) de xay dashboard va frontend.

## 13. Code MVP da tao

Phan khoi dong da co cac file:

```text
backend/hashing.py
backend/local_chain.py
backend/blockchain_service.py
backend/app.py
backend/demo_flow.py
contracts/AgriPriceRegistry.sol
data/sample/price_records_seed.csv
scripts/export_blockchain_seed.py
scripts/fetch_public_blockchain_seed.py
test/AgriPriceRegistry.test.cjs
requirements.txt
```

Chay API local:

```bash
python -m backend.app
```

Endpoint quan trong:

```text
GET  /api/prices
GET  /api/prices?commodity=&source=&region=
POST /api/prices/:id/anchor
GET  /api/prices/:id/verify
GET  /api/prices/:id/qr-payload
GET  /verify/:id
POST /api/prices/:id/lifecycle
GET  /api/prices/:id/lifecycle
GET  /api/transactions
GET  /api/stats
```

Chay test smart contract:

```bash
npx hardhat test
```

Chay backend voi local fallback:

```bash
python -m backend.app
```

Chay backend voi Hardhat RPC that:

```bash
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost
python -m pip install -r requirements.txt
python -m backend.app
```
