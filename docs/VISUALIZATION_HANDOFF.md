# Handoff: Giai Doan 1 → Visualization

Tai lieu nay danh cho **Thanh Vien 2 (Visualization)** de hieu ro nhung gi da xay xong va nhung gi can lam tiep.

---

## 1. Trang thai giai doan 1 (DA HOAN THANH)

### Nhung gi da co san

| File | Mo ta |
|---|---|
| `contracts/AgriPriceRegistry.sol` | Smart contract anchor + verify + lifecycle |
| `backend/hashing.py` | Tao canonical JSON va SHA-256 hash |
| `backend/local_chain.py` | File JSON lam ledger (fallback khi khong co Hardhat) |
| `backend/blockchain_service.py` | Bridge Python → Hardhat RPC (tu dong fallback) |
| `backend/app.py` | HTTP API server, chay local port 8000 |
| `backend/demo_flow.py` | Script demo nhanh |
| `test/AgriPriceRegistry.test.cjs` | 10/10 Hardhat test pass |
| `data/sample/price_records_seed.csv` | 140 ban ghi gia nong san thuc te, World Bank 2023-2026 |
| `scripts/export_blockchain_seed.py` | Export tu MotherDuck gold.fact_price_daily |
| `scripts/fetch_public_blockchain_seed.py` | Fetch truc tiep tu World Bank API |

### Du lieu seed hien tai

- **140 ban ghi** tu World Bank Pink Sheet
- **4 commodity**: rice, coffee, cocoa, cotton
- **Khoang thoi gian**: 2023-10 den 2026-08 (monthly)
- **Region/Country**: global / global
- **Source**: WORLD_BANK

---

## 2. Chay API local

### Buoc 1: Khoi dong backend

```bash
python -m backend.app
# → http://127.0.0.1:8000
```

### Buoc 2 (tuy chon - neu muon dung Hardhat that thay vi local fallback)

```bash
# Terminal 1:
npm run chain:hardhat

# Terminal 2:
npm run deploy:local

# Terminal 3:
python -m backend.app
# → In ra: Blockchain backend: hardhat
```

Neu chi test UI, **chay buoc 1 la du** (backend tu dong dung local JSON ledger fallback).

---

## 3. API Reference day du

Base URL: `http://127.0.0.1:8000`

### Lay danh sach gia (co filter)

```
GET /api/prices
GET /api/prices?commodity=rice
GET /api/prices?commodity=coffee&source=WORLD_BANK
GET /api/prices?region=global
```

Response mau (moi record):
```json
{
  "price_id": "21c34ff9245babdff5526929752bdbd9",
  "commodity": "rice",
  "price_date": "2026-08-01",
  "region": "global",
  "country": "global",
  "price_usd_per_kg": "0.471000",
  "currency": "USD",
  "unit": "kg",
  "source": "WORLD_BANK",
  "is_imputed": "false",
  "ingested_at": "2026-09-23T..."
}
```

### Xem chi tiet ban ghi + trang thai blockchain

```
GET /api/prices/{price_id}
```

Response mau:
```json
{
  "price_id": "21c34ff9245babdff5526929752bdbd9",
  "commodity": "rice",
  "price_date": "2026-08-01",
  "price_usd_per_kg": "0.471000",
  "data_hash": "0xc1eba5590372359566fb8e5e13c7b8b5691ca9d58620e45949ba4944ed116f5d",
  "fingerprint": "AGR-v1-C1EBA559",
  "blockchain_status": "NOT_ANCHORED",
  "proof": null
}
```

`blockchain_status` co the la: `NOT_ANCHORED` | `ANCHORED`

### Ghi hash len blockchain (anchor)

```
POST /api/prices/{price_id}/anchor
```

Response mau:
```json
{
  "id": "21c34ff9245babdff5526929752bdbd9",
  "data_hash": "0xc1eba559...",
  "fingerprint": "AGR-v1-C1EBA559",
  "transaction_hash": "0x57e254e6...",
  "blockchain_status": "ANCHORED",
  "proof": {
    "record_id": "21c34ff9245babdff5526929752bdbd9",
    "data_hash": "0xc1eba559...",
    "source": "WORLD_BANK",
    "created_by": "local-demo-wallet",
    "created_at": 1790000000,
    "tx_hash": "0x57e254...",
    "block_number": 1
  },
  "blockchain_backend": {
    "mode": "local",
    "rpc_url": "http://127.0.0.1:8545",
    "contract_address": null
  }
}
```

### Xac minh du lieu

```
GET /api/prices/{price_id}/verify
```

Response khi hop le (VERIFIED):
```json
{
  "id": "21c34ff9245babdff5526929752bdbd9",
  "current_hash": "0xc1eba559...",
  "stored_hash": "0xc1eba559...",
  "fingerprint": "AGR-v1-C1EBA559",
  "verified": true,
  "blockchain_status": "VERIFIED",
  "proof": { ... }
}
```

Response khi bi sua (TAMPERED):
```json
{
  "verified": false,
  "blockchain_status": "TAMPERED",
  "current_hash": "0xabc...",
  "stored_hash": "0xdef..."
}
```

Response khi chua anchor (NOT_ANCHORED):
```json
{
  "verified": false,
  "blockchain_status": "NOT_ANCHORED",
  "proof": null
}
```

### Lich su giao dich

```
GET /api/transactions
```

Response (array, sap xep theo block_number):
```json
[
  {
    "record_id": "21c34ff9245babdff5526929752bdbd9",
    "action": "ANCHOR_PRICE_RECORD",
    "data_hash": "0xc1eba559...",
    "tx_hash": "0x57e254...",
    "block_number": 1,
    "status": "CONFIRMED",
    "created_at": 1790000000,
    "source": "WORLD_BANK",
    "created_by": "local-demo-wallet"
  }
]
```

### Thong ke tong quan (cho Dashboard)

```
GET /api/stats
```

Response:
```json
{
  "total_records": 140,
  "total_anchored": 5,
  "total_verified": 5,
  "total_unanchored": 135,
  "blockchain_backend": {
    "mode": "local",
    "rpc_url": "http://127.0.0.1:8545",
    "contract_address": null
  }
}
```

### QR Payload

```
GET /api/prices/{price_id}/qr-payload?base_url=http://localhost:8000
```

Response:
```json
{
  "type": "agri-price-proof",
  "version": "v1",
  "record_id": "21c34ff9245babdff5526929752bdbd9",
  "hash": "0xc1eba559...",
  "fingerprint": "AGR-v1-C1EBA559",
  "verify_url": "http://localhost:8000/verify/21c34ff9245babdff5526929752bdbd9"
}
```

### Trang verify sau quet QR (HTML)

```
GET /verify/{price_id}
```

Trang HTML don gian hien thi VERIFIED / TAMPERED / NOT ANCHORED + thong tin ban ghi.

### Lifecycle events

```
GET  /api/prices/{price_id}/lifecycle
POST /api/prices/{price_id}/lifecycle
```

POST body:
```json
{
  "event_type": "VERIFIED",
  "metadata_uri": "ipfs://...",
  "metadata": {}
}
```

---

## 4. Cac man hinh can xay (theo IMPLEMENTATION_PLAN)

### Man hinh 1: Dashboard tong quan
- Lay tu `GET /api/stats`
- Hien thi: Tong so ban ghi, so da anchor, so verified, so chua anchor
- Co the them bieu do tron / bar chart phan bo commodity

### Man hinh 2: Danh sach gia nong san
- Lay tu `GET /api/prices` + filter params
- Bang co cot: commodity, price_date, region, price_usd_per_kg, source, blockchain_status
- Filter: commodity dropdown, source, date range
- Moi row co nut "Anchor" (neu NOT_ANCHORED) va "Verify"

### Man hinh 3: Chi tiet ban ghi
- Lay tu `GET /api/prices/{id}`
- Hien thi toan bo thong tin: commodity, ngay, gia, hash, fingerprint
- Badge mau theo blockchain_status
- Nut "Anchor to blockchain" → goi POST /anchor
- Nut "Verify now" → goi GET /verify
- Hien thi data_hash va transaction_hash dang code block

### Man hinh 4: Xac minh (Verify)
- Lay tu `GET /api/prices/{id}/verify`
- Hien thi ro: current_hash, stored_hash, matched/not matched
- Badge xanh (VERIFIED) / do (TAMPERED) / xam (NOT_ANCHORED)
- "Fingerprint" ngan de de nhin: AGR-v1-XXXXXX

### Man hinh 5: Lich su giao dich
- Lay tu `GET /api/transactions`
- Bang: record_id, action, tx_hash, block_number, created_at
- Highlight mau theo action (ANCHOR vs LIFECYCLE)

### Man hinh 6: Trang QR verify (sau quet QR)
- Lay tu `GET /verify/{id}` hoac xay lai bang React/HTML dep hon
- Backend da co trang HTML don gian, co the override voi trang dep hon

---

## 5. Cach gia lap tampered (demo tampering)

De demo "du lieu bi sua":

1. Anchor mot record: `POST /api/prices/{id}/anchor`
2. Mo file `data/sample/price_records_seed.csv`
3. Sua gia `price_usd_per_kg` cua record do
4. Save file, **khong can restart server** (server load moi request)
   > **Luu y**: Hien tai server load records 1 lan khi khoi dong.
   > De demo tamper, can restart server sau khi sua CSV, roi goi verify.
5. Goi `GET /api/prices/{id}/verify` → se thay `"verified": false`, `"blockchain_status": "TAMPERED"`

---

## 6. Cau truc response chuan ban phai theo

**Cac truong can hien thi:**

| Truong | Lay tu dau | Hien thi cho nguoi dung |
|---|---|---|
| `commodity` | price record | Loai hang hoa |
| `price_date` | price record | Ngay ghi nhan |
| `price_usd_per_kg` | price record | Gia (USD/kg) |
| `source` | price record | Nguon du lieu |
| `data_hash` | GET /api/prices/:id | Hash du lieu |
| `fingerprint` | GET /api/prices/:id | AGR-v1-XXXXXXXX |
| `blockchain_status` | GET /api/prices/:id | Badge trang thai |
| `proof.tx_hash` | proof object | Transaction hash |
| `proof.block_number` | proof object | Block number |
| `proof.created_at` | proof object | Thoi gian anchor (unix ts) |
| `verified` | GET /api/prices/:id/verify | true/false |

**Trang thai blockchain_status:**

| Gia tri | Mau badge de xuat | Y nghia |
|---|---|---|
| `NOT_ANCHORED` | Xam / outline | Chua ghi blockchain |
| `ANCHORED` | Xanh duong | Da ghi blockchain |
| `VERIFIED` | Xanh la | Du lieu hop le |
| `TAMPERED` | Do | Du lieu bi sua |
| `FAILED` | Cam | Ghi blockchain that bai |

---

## 7. Luu y ki thuat quan trong

1. **CORS**: Server hien tai chua co CORS header. Neu dung Vite/React dev server rieng, can them CORS hoac proxy qua Vite config.
2. **Hot reload data**: Server load CSV 1 lan khi khoi dong. Tamper demo can restart.
3. **Blockchain backend mode**: `blockchain_backend.mode` = `"local"` (fallback) hoac `"hardhat"` (RPC that). UI co the hien thi mode nay o footer/status bar.
4. **price_id**: La MD5 hash cua `source|commodity|price_date|region` — chuoi 32 ky tu hex, dung truc tiep lam recordId tren blockchain.
5. **Fingerprint**: Ngan gon, chi de hien thi. Verify phai dung `data_hash` day du.
6. **created_at** trong proof la Unix timestamp (so nguyen). Chuyen sang ngay doc duoc bang `new Date(created_at * 1000)`.
