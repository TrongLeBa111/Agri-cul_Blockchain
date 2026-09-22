# Implementation Plan

## 1. Dinh huong trien khai

Project moi se dung repo `Agri-cul_Blockchain` lam repo chinh. Repo `agri-price-dwh` duoc xem la project nen/tham chieu cho du lieu gia nong san.

Huong trien khai khuyen nghi:

1. Lay y tuong va mo hinh du lieu tu `agri-price-dwh`.
2. Xay backend/API toi thieu cho cac nghiep vu can demo.
3. Bo sung smart contract de luu bang chung du lieu.
4. Xay giao dien cho them moi, tim kiem va xac minh.
5. Viet tai lieu va kich ban demo.

Khong nen co gang port toan bo project cu ngay tu dau. Chi nen lay cac phan can cho demo de dam bao kip tien do va dung yeu cau blockchain.

## 2. Cach noi 2 GitHub

### Cach 1: Lien ket tai lieu

Them link repo cu vao README va bao cao nhu mot nguon tham chieu. Cach nay don gian, it rui ro.

Repo cu:

```text
https://github.com/LeGiaVan/agri-price-dwh
```

Repo moi:

```text
https://github.com/TrongLeBa111/Agri-cul_Blockchain
```

### Cach 2: Git submodule

Neu muon giu repo cu nam trong repo moi ma van tach lich su commit:

```bash
git submodule add https://github.com/LeGiaVan/agri-price-dwh.git external/agri-price-dwh
git submodule update --init --recursive
```

Nen dung cach nay neu can xem/chay project cu ben trong project moi.

### Cach 3: Copy phan can thiet

Chi copy model du lieu, script ETL hoac file mau can dung vao repo moi. Cach nay phu hop nhat neu do an can gon, de bao cao va de demo.

Khuyen nghi hien tai: **bat dau bang cach 1 va cach 3**. Chua can dung submodule neu nhom chua chac se chay truc tiep project cu.

## 3. Module can xay

### 3.1. Data module

Nhiem vu:

- Xac dinh bang du lieu gia nong san.
- Tao du lieu mau neu chua co data that.
- Chuan hoa cac truong can hash.

Du lieu toi thieu:

```text
id
product_name
market_location
price
unit
recorded_date
source
created_by
created_at
updated_at
blockchain_tx_hash
data_hash
verification_status
```

### 3.2. Hashing module

Nhiem vu:

- Chuyen ban ghi thanh JSON co thu tu truong on dinh.
- Tao hash cho ban ghi.
- Dam bao cung mot noi dung luon tao ra cung mot hash.

Nguyen tac:

- Khong dua cac truong thay doi ky thuat vao hash, vi du `updated_at`, `tx_hash`, `verification_status`.
- Chi hash cac truong dai dien cho noi dung du lieu gia.

### 3.3. Smart contract module

Nhiem vu:

- Luu hash cua ban ghi.
- Tra ve thong tin hash theo `recordId`.
- Phat event khi co ban ghi moi.
- Ho tro verify hash.

Ham du kien:

```solidity
addPriceRecordHash(recordId, dataHash, source)
getPriceRecordHash(recordId)
verifyPriceRecord(recordId, dataHash)
```

### 3.4. Backend/API module

API du kien:

```text
POST /api/prices
GET  /api/prices
GET  /api/prices/:id
POST /api/prices/:id/anchor
GET  /api/prices/:id/verify
GET  /api/transactions
```

Giai thich:

- `POST /api/prices`: them ban ghi gia vao database.
- `GET /api/prices`: tim kiem va loc du lieu.
- `GET /api/prices/:id`: xem chi tiet.
- `POST /api/prices/:id/anchor`: tao hash va ghi len blockchain.
- `GET /api/prices/:id/verify`: kiem tra ban ghi co khop voi blockchain khong.
- `GET /api/transactions`: xem lich su giao dich.

### 3.5. Frontend module

Man hinh toi thieu:

- Dashboard tong quan.
- Danh sach gia nong san.
- Form them moi.
- Chi tiet ban ghi.
- Xac minh blockchain.
- Lich su giao dich.

Trang thai hien thi:

- `Not anchored`: ban ghi chua ghi blockchain.
- `Verified`: du lieu khop blockchain.
- `Tampered`: du lieu khong khop blockchain.
- `Pending`: giao dich dang xu ly.

## 4. Phan cong cong viec cho 3 nguoi

## Thanh vien 1: Ban - Quan ly, data flow va smart contract

Vai tro:

- Quan ly tong the project.
- Lap trinh chinh phan luong du lieu va blockchain.
- Thiet ke cach du lieu duoc tao hash, ghi hop dong thong minh va xac minh.
- Chot kien truc tich hop giua database, backend va smart contract.
- Review code cua cac thanh vien khac.
- Chuan bi demo cuoi.

Cong viec chinh:

- Tao repo, cau truc thu muc va README.
- Quyet dinh cach su dung repo `agri-price-dwh`.
- Thiet ke data flow: tao moi, chuan hoa du lieu, tao hash, ghi blockchain, verify.
- Thiet ke va code smart contract luu bang chung du lieu.
- Thiet ke service ket noi backend voi smart contract.
- Dinh nghia API contract cho cac endpoint lien quan den blockchain.
- Xu ly luong them du lieu, tao hash, ghi blockchain va xac minh.
- Sua loi tich hop.
- Tong hop bao cao va slide demo.

Deliverable:

- Data flow va smart contract design.
- Smart contract va blockchain service.
- API contract cho phan blockchain.
- Flow demo hoan chinh.
- Tai lieu tong hop.

## Thanh vien 2: Visualization va backend ho tro hien thi

Vai tro:

- Lap trinh chinh phan giao dien hien thi va visualization.
- Xay backend/API can thiet de phuc vu giao dien.
- Phoi hop voi ban de lay dung du lieu tu data flow va blockchain service.

Cong viec chinh:

- Thiet ke layout cac man hinh chinh.
- Xay dashboard tong quan.
- Xay bang danh sach gia nong san, tim kiem va loc.
- Xay man hinh chi tiet ban ghi, hien thi `dataHash`, `transactionHash`, trang thai verify.
- Xay trang lich su giao dich/visualization.
- Viet cac API phuc vu UI neu backend chinh chua co san.
- Lam viec voi ban de thong nhat response format.

Deliverable:

- Giao dien demo.
- Visualization/dashboard.
- Backend endpoint ho tro hien thi.
- Tai lieu mo ta UI flow.

## Thanh vien 3: Bao cao va kiem thu

Vai tro:

- Phu trach bao cao, test case va minh chung kiem thu.
- Theo doi yeu cau mon hoc de dam bao san pham bam de.
- Ho tro chuan bi slide va kich ban demo.

Cong viec chinh:

- Viet de cuong, use case, activity/sequence diagram va mo ta input-output.
- Lap test plan cho cac luong chinh.
- Viet test case: them du lieu, ghi blockchain, verify hop le, verify sai, tim kiem.
- Ghi ket qua kiem thu va anh minh chung.
- Tong hop phan rui ro, danh gia va ket luan.
- Ho tro chuan bi slide thuyet trinh.

Deliverable:

- Bao cao do an.
- Test plan va test case.
- Bang ket qua kiem thu.
- Slide/kich ban demo.

## 5. Lo trinh theo giai doan

### Giai doan 1: Chuan bi va phan tich

Muc tieu:

- Chot de tai.
- Chot pham vi MVP.
- Xem project cu co phan nao tai su dung duoc.
- Viet de cuong va thiet ke so bo.

Ket qua:

- README.
- De cuong.
- Implementation plan.
- Data model ban dau.
- Tai lieu giai doan 1 cho data flow va smart contract.

### Giai doan 2: Nen tang ky thuat

Muc tieu:

- Tao cau truc source.
- Cai dat backend, database, frontend va blockchain environment.
- Tao smart contract ban dau.

Ket qua:

- App khoi dong duoc.
- Database co bang du lieu.
- Contract deploy duoc local.

### Giai doan 3: Chuc nang cot loi

Muc tieu:

- Them du lieu gia.
- Tao hash.
- Ghi hash len blockchain.
- Tim kiem va xem chi tiet.
- Verify du lieu.

Ket qua:

- Flow demo chinh hoat dong end-to-end.

### Giai doan 4: Hoan thien UI va bao cao

Muc tieu:

- Hoan thien giao dien.
- Them trang lich su giao dich.
- Viet huong dan chay.
- Chuan bi slide va kich ban demo.

Ket qua:

- Ban demo on dinh.
- Tai lieu nop bai.
- Slide thuyet trinh.

## 6. Kich ban demo de xuat

1. Mo dashboard, xem tong quan so ban ghi va so giao dich blockchain.
2. Them mot ban ghi gia nong san moi.
3. Bam ghi blockchain/anchor de luu hash cua ban ghi.
4. Mo chi tiet ban ghi, xem `dataHash` va `transactionHash`.
5. Bam verify de chung minh du lieu hop le.
6. Sua gia trong database/UI theo tinh huong demo.
7. Verify lai va hien thi du lieu khong con khop blockchain.
8. Mo lich su giao dich de xem cac lan ghi nhan.

## 7. Tieu chi hoan thanh MVP

- Co it nhat mot flow them du lieu va ghi blockchain thanh cong.
- Co the tim kiem va xem chi tiet ban ghi.
- Co the verify ban ghi hop le/khong hop le.
- Co giao dien de demo khong can thao tac truc tiep database.
- Co tai lieu giai thich ro du lieu nao on-chain va du lieu nao off-chain.
- Co phan phan cong cong viec va minh chung dong gop cua tung thanh vien.

## 8. Rui ro va cach xu ly

### Rui ro 1: Project cu qua lon hoac kho chay

Cach xu ly:

- Chi lay data model va dataset mau.
- Khong phu thuoc project cu trong demo chinh.

### Rui ro 2: Blockchain tich hop mat thoi gian

Cach xu ly:

- Bat dau bang local blockchain.
- Chi luu hash va metadata toi thieu.
- Tach ro logic blockchain service trong backend.

### Rui ro 3: UI khong kip hoan thien

Cach xu ly:

- Uu tien cac man hinh phuc vu demo.
- Dashboard va lich su co the lam don gian.

### Rui ro 4: Thanh vien lam lech nhau

Cach xu ly:

- Ban giu vai tro quan ly API contract va merge.
- Moi thanh vien lam theo module rieng.
- Thong nhat format du lieu truoc khi code.

## 9. Viec can lam tiep ngay

1. Clone hoac mo repo `agri-price-dwh` de xem stack va schema.
2. Chot cong nghe backend/frontend/smart contract.
3. Tao data model cuoi cung.
4. Tao skeleton source cho backend, frontend va contract.
5. Viet contract toi thieu va API verify dau tien.

## 10. Tai lieu theo vai tro

- Phan cua ban: [Giai doan 1 - Data flow va smart contract](PHASE_1_DATA_FLOW_SMART_CONTRACT.md)
- Phan chon loc project cu: [Chon loc project cu cho blockchain MVP](LEGACY_REUSE_SELECTION.md)
