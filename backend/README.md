# Backend MVP

Backend nay dung Python standard library de chay luong blockchain MVP ma khong can token MotherDuck/Groq/dbt.

## Chay local

Tu thu muc repo:

```bash
python -m backend.app
```

Mac dinh server chay tai:

```text
http://127.0.0.1:8000
```

## API

```text
GET  /api/prices
GET  /api/prices/:id
POST /api/prices/:id/anchor
GET  /api/prices/:id/verify
GET  /api/prices/:id/qr-payload
GET  /verify/:id
GET  /api/prices/:id/lifecycle
POST /api/prices/:id/lifecycle
```

## Demo nhanh

Lay danh sach ban ghi:

```bash
curl http://127.0.0.1:8000/api/prices
```

Anchor mot ban ghi:

```bash
curl -X POST http://127.0.0.1:8000/api/prices/demo_wb_rice_2026_06_01_global/anchor
```

Verify:

```bash
curl http://127.0.0.1:8000/api/prices/demo_wb_rice_2026_06_01_global/verify
```

Lay payload de render QR:

```bash
curl http://127.0.0.1:8000/api/prices/demo_wb_rice_2026_06_01_global/qr-payload
```

Mo trang verify sau khi quet QR:

```text
http://127.0.0.1:8000/verify/demo_wb_rice_2026_06_01_global
```

Them lifecycle event:

```bash
curl -X POST http://127.0.0.1:8000/api/prices/demo_wb_rice_2026_06_01_global/lifecycle ^
  -H "Content-Type: application/json" ^
  -d "{\"event_type\":\"INGESTED\",\"metadata_uri\":\"local://seed\",\"metadata\":{\"source\":\"seed\"}}"
```

## Luu y

File ledger local duoc sinh tai:

```text
data/local/proof_ledger.json
```

Day chi la mock blockchain de test flow. Khi deploy smart contract that, thay `LocalProofLedger` bang service goi contract.

