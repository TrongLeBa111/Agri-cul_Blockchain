# Hashing Strategy Cho Agri Price Blockchain

Tai lieu nay giai thich cach tao hash de xac minh du lieu gia nong san. Goi la "ma hoa" trong trao doi hang ngay cung duoc, nhung ve ky thuat day la **hashing**, khong phai encryption.

## 1. Hash khac encryption nhu the nao?

Encryption:

- Co the giai ma neu co key.
- Dung khi muon giu bi mat noi dung.

Hashing:

- Mot chieu, khong giai nguoc ve du lieu goc.
- Cung mot input luon ra cung mot output.
- Chi can doi mot ky tu thi hash thay doi rat manh.
- Phu hop de chung minh du lieu khong bi sua.

Trong de tai nay, blockchain nen luu hash thay vi luu toan bo gia nong san.

## 2. De xuat an toan cho MVP

Nen dung:

```text
SHA-256(canonical_payload)
```

Hoac neu di theo EVM/Solidity:

```text
Keccak-256(canonical_payload)
```

Khuyen nghi thuc te:

- Backend tao canonical JSON.
- Backend hash bang SHA-256 hoac Keccak-256.
- Smart contract luu `bytes32 dataHash`.
- Khi verify, backend tao lai hash va so voi hash da luu on-chain.

## 3. Phan "doc la" nen nam o dau?

Khong nen tu che loi hash moi. Nen lam doc la o lop payload:

```text
AGRI_PRICE_V1 | project_id | chain_id | record_id | canonical_json
```

Vi du canonical payload:

```json
{
  "domain": "AGRI_PRICE_BLOCKCHAIN",
  "version": "v1",
  "record": {
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
}
```

Sau do:

```text
dataHash = SHA-256(canonical_json)
```

Nhu vay hash van an toan, nhung format payload la cua rieng de tai.

## 4. Cong thuc de xuat

### Ban gon cho MVP

```text
dataHash = SHA-256(
  "AGRI_PRICE_V1|" +
  commodity + "|" +
  price_date + "|" +
  region + "|" +
  country + "|" +
  price_usd_per_kg + "|" +
  currency + "|" +
  unit + "|" +
  source + "|" +
  is_imputed
)
```

Uu diem:

- De giai thich khi thuyet trinh.
- De debug.
- De code nhanh.

Nhuoc diem:

- Can dam bao moi field da duoc chuan hoa truoc.
- Ky tu phan cach `|` co the gay loi neu du lieu text chua duoc lam sach.

### Ban chac hon

```text
dataHash = SHA-256(canonical_json_with_sorted_or_fixed_keys)
```

Uu diem:

- It loi hon khi du lieu text co ky tu dac biet.
- De mo rong them field.
- Phu hop voi backend hien dai.

Khuyen nghi: dung ban JSON canonical.

## 5. Quy tac canonical JSON

Thu tu field co dinh:

```text
domain
version
record.commodity
record.price_date
record.region
record.country
record.price_usd_per_kg
record.currency
record.unit
record.source
record.is_imputed
```

Quy tac chuan hoa:

- Text: trim khoang trang.
- `commodity`: lowercase.
- `source`: uppercase, vi du `WORLD_BANK`, `YAHOO_FINANCE`.
- `currency`: uppercase, vi du `USD`.
- `price_date`: `YYYY-MM-DD`.
- `price_usd_per_kg`: string decimal co 6 chu so sau dau phay.
- `is_imputed`: boolean that, khong dung string `"false"`.

## 6. Fingerprint hien thi cho UI

Hash day du rat dai. UI co the hien thi fingerprint ngan:

```text
AGR-v1-9F3A7C2B
```

Cach tao:

```text
fingerprint = "AGR-v1-" + first_8_chars(dataHash)
```

Luu y:

- Fingerprint chi de hien thi.
- Xac minh van phai dung hash day du.

## 7. Neu muon "bo hash doc la" hon nua

Co the them cac lop sau ma van giu an toan:

### Domain separator

```text
domain = "AGRI_PRICE_BLOCKCHAIN"
```

Giup hash cua he thong nay khong bi lan voi hash cua he thong khac.

### Version

```text
version = "v1"
```

Sau nay doi quy tac hash thi tang len `v2`, khong lam hong du lieu cu.

### Project pepper

```text
pepper = "AGRI_CUL_2026"
```

Pepper la chuoi co dinh cua project dua vao payload. Neu dung de demo thi duoc. Neu dung san pham that, pepper phai quan ly can than.

### Dual hash

```text
contentHash = SHA-256(canonical_record)
proofHash = Keccak-256("AGRI_PRICE_V1|" + contentHash)
```

Cach nay kha dep khi thuyet trinh:

- `contentHash`: dai dien noi dung du lieu.
- `proofHash`: dai dien bang chung dua len blockchain.

## 8. Dieu khong nen lam

- Khong tu viet thuat toan hash rieng tu dau.
- Khong dung MD5 cho bang chung blockchain.
- Khong dua token/API key vao hash.
- Khong dua field thay doi lien tuc nhu `updated_at`, `blockchain_status`, `transaction_hash` vao hash.
- Khong chi hash moi `price_id`, vi nhu vay khong chung minh noi dung gia co bi sua hay khong.

## 9. Lua chon de xuat cho do an

Dung:

```text
proofHash = Keccak-256(
  canonical JSON gom domain, version va record data
)
```

Trong bao cao co the giai thich:

> He thong su dung co che hash mot chieu de tao dau van tay so cho moi ban ghi gia nong san. Dau van tay nay duoc ghi len smart contract. Khi can xac minh, he thong tao lai hash tu du lieu hien tai va so sanh voi hash da luu tren blockchain. Neu hai hash trung nhau, du lieu con nguyen ban; neu khac nhau, du lieu da bi thay doi.

