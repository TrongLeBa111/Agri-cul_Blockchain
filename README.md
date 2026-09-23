# Agri Price Blockchain

He thong xac thuc va truy xuat du lieu gia nong san bang Blockchain.

> Du lieu gia nong san co the bi sua doi, thieu minh bach hoac kho kiem chung nguon goc.
> Project nay ghi bang chung hash cua moi ban ghi len smart contract, cho phep bat ky ai xac minh du lieu co con nguyen ban hay khong.

---

## Kien truc tong the

```
World Bank API / MotherDuck
        |
        v
  data/sample/price_records_seed.csv   (du lieu off-chain)
        |
        v
  backend/hashing.py                   (canonical JSON + SHA-256)
        |
        v
  backend/blockchain_service.py        (bridge Python -> Hardhat RPC)
        |
        v
  contracts/AgriPriceRegistry.sol      (luu hash on-chain)
        |
        v
  backend/app.py                       (HTTP API)
        |
        v
  Frontend / Visualization             (dashboard, verify, QR)
```

**On-chain** (blockchain): `recordId`, `dataHash`, `source`, `createdBy`, `createdAt`, lifecycle events  
**Off-chain** (CSV/DB): Toan bo thong tin gia chi tiet

---

## Cay thu muc

```
Agri-cul_Blockchain/
├── contracts/
│   └── AgriPriceRegistry.sol          # Smart contract chinh
├── test/
│   └── AgriPriceRegistry.test.cjs     # Hardhat test (10/10 pass)
├── scripts/
│   ├── deploy.js                      # Deploy contract len local node
│   ├── export_blockchain_seed.py      # Export tu MotherDuck gold.fact_price_daily
│   └── fetch_public_blockchain_seed.py # Fetch truc tiep tu World Bank API
├── backend/
│   ├── hashing.py                     # Canonical JSON + SHA-256 + fingerprint
│   ├── local_chain.py                 # LocalProofLedger (fallback JSON)
│   ├── blockchain_service.py          # Bridge Python -> Hardhat RPC
│   ├── app.py                         # HTTP API server (port 8000)
│   └── demo_flow.py                   # Script demo nhanh
├── data/
│   ├── sample/
│   │   └── price_records_seed.csv     # 140 ban ghi World Bank 2023-2026
│   └── local/
│       └── proof_ledger.json          # Local ledger (tu sinh, khong commit)
├── deployments/
│   └── localhost.json                 # Dia chi contract sau khi deploy
├── ml/                                # LSTM models du bao gia (tham khao)
├── docs/
│   ├── DE_CUONG.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── PHASE_1_DATA_FLOW_SMART_CONTRACT.md
│   ├── HASHING_STRATEGY.md
│   ├── QR_AND_PRODUCT_LIFECYCLE.md
│   ├── HARDHAT_SETUP.md
│   └── VISUALIZATION_HANDOFF.md       # Handoff cho thanh vien Visualization
├── hardhat.config.cjs
├── package.json
└── .env                               # MOTHERDUCK_TOKEN (khong commit)
```

---

## Cai dat

### 1. Cai Hardhat (Node.js)

```bash
npm install
```

### 2. Cai Python dependencies

```bash
pip install python-dotenv
# (duckdb neu muon dung export_blockchain_seed.py)
pip install duckdb
```

### 3. Tao file `.env`

```bash
cp .env.example .env
# Them MOTHERDUCK_TOKEN neu can export tu MotherDuck
```

---

## Chay nhanh (local fallback mode)

Khong can Hardhat, khong can Docker, chi can Python:

```bash
python -m backend.app
# → Agri Price Blockchain API running at http://127.0.0.1:8000
# → Loaded 140 price records
# → Blockchain backend: local (JSON fallback)
```

---

## Chay voi Hardhat (smart contract that)

```bash
# Terminal 1: Chay local blockchain
npm run chain:hardhat

# Terminal 2: Deploy contract
npm run deploy:local

# Terminal 3: Chay API (tu dong detect Hardhat node)
python -m backend.app
# → Blockchain backend: hardhat (RPC that)
```

---

## API Endpoints

| Method | Endpoint | Mo ta |
|---|---|---|
| GET | `/api/prices` | Danh sach gia (filter: `?commodity=rice&source=WORLD_BANK`) |
| GET | `/api/prices/:id` | Chi tiet ban ghi + trang thai blockchain |
| POST | `/api/prices/:id/anchor` | Ghi hash len blockchain |
| GET | `/api/prices/:id/verify` | Xac minh du lieu |
| GET | `/api/prices/:id/qr-payload` | QR payload |
| GET | `/api/prices/:id/lifecycle` | Lich su vong doi |
| POST | `/api/prices/:id/lifecycle` | Them lifecycle event |
| GET | `/api/transactions` | Tat ca giao dich blockchain |
| GET | `/api/stats` | Thong ke tong quan |
| GET | `/verify/:id` | Trang HTML xac minh (sau quet QR) |

---

## Smart Contract Test

```bash
npx hardhat test
# 10 passing
```

---

## Cap nhat du lieu seed

### Tu World Bank API (khong can token)

```bash
python scripts/fetch_public_blockchain_seed.py --source worldbank --days 1095
```

### Tu MotherDuck gold.fact_price_daily

```bash
# Can MOTHERDUCK_TOKEN trong .env
python scripts/export_blockchain_seed.py --days 90
python scripts/export_blockchain_seed.py --all
python scripts/export_blockchain_seed.py --dry-run  # preview
```

---

## Trang thai blockchain_status

| Gia tri | Y nghia |
|---|---|
| `NOT_ANCHORED` | Chua ghi blockchain |
| `ANCHORED` | Da ghi blockchain |
| `VERIFIED` | Du lieu hop le (hash khop) |
| `TAMPERED` | Du lieu bi sua (hash khong khop) |
| `FAILED` | Ghi that bai |

---

## Thanh vien

- **Thanh vien 1** (Ban): Smart contract, data flow, blockchain service, API → `docs/PHASE_1_DATA_FLOW_SMART_CONTRACT.md`
- **Thanh vien 2**: Visualization, dashboard, frontend → `docs/VISUALIZATION_HANDOFF.md`
- **Thanh vien 3**: Bao cao, test case, kiem thu

---

## Tai lieu tham khao

- [De cuong](docs/DE_CUONG.md)
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
- [Phase 1 - Data Flow & Smart Contract](docs/PHASE_1_DATA_FLOW_SMART_CONTRACT.md)
- [Hashing Strategy](docs/HASHING_STRATEGY.md)
- [Visualization Handoff](docs/VISUALIZATION_HANDOFF.md)
- [Hardhat Setup](docs/HARDHAT_SETUP.md)
