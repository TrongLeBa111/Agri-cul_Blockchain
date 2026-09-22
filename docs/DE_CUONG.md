# De Cuong Do An

## 1. Ten de tai

**Agri Price Blockchain - He thong xac thuc va truy xuat du lieu gia nong san bang Blockchain**

## 2. Boi canh va ly do chon de tai

Du lieu gia nong san co gia tri thuc tien trong viec theo doi thi truong, ho tro nguoi nong dan, thuong lai, doanh nghiep va nguoi quan ly ra quyet dinh. Tuy nhien, du lieu gia co the phat sinh tu nhieu nguon, duoc cap nhat lien tuc va co nguy co bi sua doi, thieu minh bach hoac kho kiem chung nguon goc.

Project cu `agri-price-dwh` co the duoc su dung lam nen tang du lieu va quy trinh xu ly gia nong san. De dap ung yeu cau mon hoc ve Blockchain, project moi se bo sung lop xac thuc du lieu bang blockchain. He thong khong nhat thiet dua toan bo du lieu len blockchain, ma luu bang chung du lieu duoi dang `hash` va metadata giao dich. Cach tiep can nay giup giu duoc hieu nang, dong thoi dam bao tinh bat bien va kha nang kiem tra tinh nguyen ban cua du lieu.

## 3. Muc tieu

Xay dung ung dung tich hop blockchain de:

- Quan ly du lieu gia nong san dau vao va dau ra.
- Ghi nhan bang chung du lieu len blockchain.
- Xac minh du lieu co bi thay doi so voi ban ghi goc hay khong.
- Cho phep them moi, tim kiem va truy xuat giao dich.
- Cung cap giao dien de su dung va trinh bay ket qua mot cach truc quan.

## 4. Pham vi thuc hien

### Trong pham vi

- Tai su dung y tuong, cau truc du lieu hoac mot phan xu ly cua repo `agri-price-dwh`.
- Thiet ke database/off-chain storage de luu thong tin gia nong san.
- Thiet ke smart contract luu `hash` va thong tin giao dich lien quan.
- Xay dung backend/API cho cac chuc nang can thiet.
- Xay dung giao dien co cac man hinh chinh:
  - Them du lieu gia nong san.
  - Danh sach/tim kiem du lieu.
  - Chi tiet ban ghi va trang thai xac minh blockchain.
  - Lich su giao dich.
- Viet tai lieu phan tich, thiet ke va huong dan demo.

### Ngoai pham vi ban dau

- Khong can xay dung data warehouse day du nhu san pham thuc te neu thoi gian han che.
- Khong dua toan bo du lieu gia len blockchain.
- Khong yeu cau mainnet that; co the dung local blockchain hoac testnet.
- Khong can tich hop oracle phuc tap trong phien ban dau.

## 5. Doi tuong su dung

- **Admin/Quan ly he thong**: quan ly nguoi dung, cau hinh, kiem tra du lieu.
- **Data Provider/Nguoi cap nhat du lieu**: them moi hoac cap nhat gia nong san.
- **Viewer/Nguoi xem**: tim kiem gia, xem chi tiet, xac minh tinh nguyen ban cua du lieu.

## 6. Du lieu dau vao va dau ra

### Dau vao

- Ten nong san.
- Khu vuc/tinh/thanh/thi truong.
- Ngay ghi nhan.
- Gia.
- Don vi tinh.
- Nguon du lieu.
- Ghi chu neu co.
- Thong tin nguoi tao/cap nhat.

### Dau ra

- Danh sach gia nong san.
- Chi tiet mot ban ghi gia.
- Ma hash cua ban ghi.
- Transaction hash tren blockchain.
- Thoi gian ghi len blockchain.
- Trang thai xac minh: hop le, khong hop le, chua ghi blockchain.
- Lich su giao dich va thay doi.

## 7. Chuc nang chinh

### 7.1. Quan ly du lieu gia nong san

- Them moi ban ghi gia.
- Cap nhat thong tin khi can.
- Liet ke va tim kiem theo ten nong san, khu vuc, ngay, nguon du lieu.
- Xem chi tiet mot ban ghi.

### 7.2. Xac thuc bang blockchain

- Tao hash tu noi dung ban ghi gia.
- Goi smart contract de luu hash va metadata.
- Luu transaction hash ve database.
- So sanh lai hash hien tai voi hash da ghi tren blockchain.

### 7.3. Truy xuat giao dich

- Hien thi lich su cac giao dich da ghi.
- Xem transaction hash.
- Xem trang thai giao dich.
- Loc giao dich theo ngay, nguoi tao hoac ma ban ghi.

### 7.4. Giao dien nguoi dung

- Dashboard tong quan.
- Man hinh them moi du lieu.
- Man hinh tim kiem.
- Man hinh chi tiet va xac minh.
- Man hinh lich su giao dich.

## 8. Kien truc de xuat

```text
Frontend
   |
Backend/API
   |
Database / Data Warehouse layer
   |
Blockchain service
   |
Smart Contract
```

### Thanh phan

- **Frontend**: giao dien thao tac va xem ket qua.
- **Backend/API**: xu ly logic nghiep vu, tao hash, goi blockchain, doc/ghi database.
- **Database/DWH**: luu du lieu gia nong san chi tiet.
- **Smart Contract**: luu hash va metadata toi thieu cua ban ghi.
- **Blockchain network**: local blockchain hoac testnet.

## 9. Thiet ke blockchain

Thong tin nen luu on-chain:

- `recordId`: ma ban ghi trong database.
- `dataHash`: hash cua noi dung ban ghi.
- `source`: nguon du lieu hoac ma nguon.
- `createdBy`: dia chi vi hoac ma nguoi tao.
- `createdAt`: thoi gian ghi.

Thong tin nen luu off-chain:

- Toan bo chi tiet gia nong san.
- Thong tin nguoi dung.
- Lich su hien thi va metadata phuc vu giao dien.

## 10. Cong nghe du kien

Co the chon stack theo muc do quen thuoc cua nhom:

- Smart contract: Solidity.
- Blockchain local/test: Hardhat, Ganache hoac testnet EVM.
- Backend: Node.js/Express hoac framework co san tu project cu.
- Database: PostgreSQL, MySQL hoac SQLite cho demo.
- Frontend: React/Vite hoac giao dien co san neu project cu da co.

Quyet dinh cuoi cung nen dua tren project cu `agri-price-dwh` dang dung cong nghe gi de giam cong viec migrate.

## 11. Ket qua mong doi

- Ung dung demo co the them va tim kiem du lieu gia nong san.
- Moi ban ghi quan trong co hash va transaction blockchain.
- Nguoi dung co the xac minh du lieu co con nguyen ban hay khong.
- Co tai lieu phan tich, thiet ke, implementation plan va huong dan demo.

## 12. Gia tri cua de tai

De tai the hien duoc ung dung blockchain trong linh vuc nong nghiep va du lieu thi truong. He thong giai quyet van de minh bach, chong sua doi du lieu va truy xuat nguon goc ban ghi, phu hop voi yeu cau mon hoc ve xac minh tinh chinh xac, tinh nguyen ban va bao mat cua giao dich so.

