# QR Va Vong Doi San Pham

## 1. QR thuoc phan nao?

QR la phan giao nhau giua hai vai tro:

- Phan cua ban: dinh nghia `recordId`, hash, transaction/proof, API verify va cac event vong doi dua len smart contract.
- Phan visualization: render QR code, tao trang hien thi lich su va xu ly trai nghiem quet QR.

Neu khong co backend/blockchain proof tu phan cua ban, QR chi la mot duong link dep. Vi vay phan nen tang QR nen duoc tinh trong phan cua ban.

## 2. QR nen chua gi?

Khong nen dua toan bo du lieu gia vao QR. QR nen chua URL xac minh:

```text
http://localhost:8000/verify/{recordId}
```

Hoac payload JSON:

```json
{
  "type": "agri-price-proof",
  "version": "v1",
  "record_id": "demo_wb_rice_2026_06_01_global",
  "hash": "0x...",
  "fingerprint": "AGR-v1-...",
  "verify_url": "http://localhost:8000/verify/demo_wb_rice_2026_06_01_global"
}
```

## 3. Luong quet QR

```text
Nguoi dung quet QR
        |
        v
Mo verify_url
        |
        v
Backend lay ban ghi off-chain
        |
        v
Backend tao lai hash
        |
        v
Backend doc proof tu blockchain/smart contract
        |
        v
Hien thi Verified / Tampered / Not Anchored
        |
        v
Hien thi lich su lifecycle event neu co
```

## 4. Vong doi san pham nen gom gi?

Trong MVP, event vong doi co the la:

```text
OBSERVED
INGESTED
CLEANED
ANCHORED
VERIFIED
UPDATED
```

Neu sau nay mo rong thanh truy xuat nong san that, co the them:

```text
HARVESTED
PACKAGED
SHIPPED
RECEIVED
SOLD
```

## 5. API lien quan QR hien co

Backend local da co:

```text
GET  /api/prices/:id/qr-payload
GET  /verify/:id
GET  /api/prices/:id/lifecycle
POST /api/prices/:id/lifecycle
```

`qr-payload` tra ve JSON de ban visualization render QR.

`verify/:id` la trang HTML don gian de mo sau khi quet QR.

