# Chon Loc Project Cu Cho Blockchain MVP

Tai lieu nay ghi lai cac phan nen giu, nen bo qua va cach tan dung project `agri-price-dwh` de khoi dong de tai blockchain ma khong phu thuoc MotherDuck/dbt token da het han.

## 1. Ket luan ngan

Co the dua tren co so project cu de phat trien tiep blockchain. Tuy nhien, trong MVP khong nen phu thuoc vao MotherDuck, dbt Cloud, Groq, email token hay GitHub Actions cu.

Nen xem project cu la:

- Nguon thiet ke du lieu.
- Nguon lineage va quy trinh ETL tham chieu.
- Nguon giao dien/visualization tham khao.
- Nguon dataset neu tim lai duoc file export tu lan crawl cu.

Khong nen xem project cu la:

- He thong phai chay lai day du.
- Dieu kien bat buoc de demo blockchain.
- Noi luu token moi.

## 2. Phan nen giu de khoi dong blockchain

### 2.1. dbt gold model

Nen giu va dung lam chuan du lieu blockchain:

```text
dbt/models/gold/fact_price_daily.sql
dbt/models/gold/schema.yml
dbt/models/silver/schema.yml
dbt/seeds/commodity_mapping.csv
```

Ly do:

- `fact_price_daily` da co `price_id`, co the dung lam `recordId` off-chain.
- Cac cot `commodity`, `price_date`, `region`, `country`, `price_usd_per_kg`, `currency`, `unit`, `source` phu hop de tao hash.
- `schema.yml` da mo ta rang buoc du lieu va accepted values.
- `commodity_mapping.csv` giup chuan hoa ten nong san.

### 2.2. Data lineage

Nen giu:

```text
Data_lineage.drawio.svg
data_lineage.drawio.xml
```

Ly do:

- Dua vao bao cao de giai thich nguon du lieu cu: Source -> Bronze -> Silver -> Gold -> Dashboard/ML.
- Co the bo sung them lop Blockchain vao lineage moi.

### 2.3. Dashboard

Nen giu o muc tham khao:

```text
dashboard/app.py
imgs/
```

Ly do:

- Ban lam visualization co the tan dung layout, chart va anh demo.
- Khong nen phu thuoc truc tiep vao MotherDuck trong MVP blockchain.
- Neu can, nen tach logic doc du lieu thanh API/backend rieng.

### 2.4. Ingest scripts

Nen giu o muc tham khao:

```text
ingest/worldbank_ingest.py
ingest/daily_yf_alert_ingest.py
ingest/utils.py
scripts/yf_historical_ingest.py
```

Ly do:

- Co cong thuc chuan hoa gia va danh sach commodity.
- Co logic source/region/country.
- Khong can chay lai trong giai doan blockchain ban dau.

### 2.5. Tai lieu kiem tra cu

Nen giu:

```text
ket_qua_kiem_tra_repo.md
implementation_plan.md
```

Ly do:

- Co thong tin ve commodity chinh thuc, pipeline va test da cau hinh.
- Co the trich vao bao cao phan "ke thua project cu".

## 3. Phan nen bo qua trong MVP blockchain

### 3.1. Token/API da het han

Khong dung lai:

```text
MOTHERDUCK_TOKEN
GROQ_API_KEY
EMAIL_PASSWORD
EMAIL_SENDER
EMAIL_RECEIVER
```

Huong xu ly:

- Khong commit `.env`.
- Chua can thiet lap lai MotherDuck.
- Chua can GenBI/Groq.
- Chua can email alert.

### 3.2. dbt runtime artifacts

Khong can cho MVP:

```text
dbt/target/
dbt/dbt_packages/
dbt/logs/
```

Ly do:

- La output sinh ra khi build dbt.
- Khong can de thiet ke blockchain.
- De trong repo co the lam nang va gay nhieu thay doi khong can thiet.

### 3.3. Model ML

Chua can dung:

```text
ml/models/*.pt
ml/models/*.pkl
ml/scripts/
```

Ly do:

- Forecast khong phai yeu cau cot loi cua blockchain.
- Co the giu lam tinh nang phu neu con thoi gian.

### 3.4. File nen

Chua can dung:

```text
dbt.rar
```

Ly do:

- Khong ro noi dung va co the nang.
- Nen giai nen/kiem tra rieng neu that su can.
- Khong nen commit vao repo moi.

## 4. Bang du lieu chon lam moc blockchain

Bang chuan nen dua tren `gold.fact_price_daily`.

Cot nen dung:

```text
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
```

Trong do:

- `price_id`: ma ban ghi off-chain.
- `commodity`: ma nong san.
- `price_date`: ngay gia.
- `region`, `country`: khu vuc thi truong.
- `price_usd_per_kg`: gia da chuan hoa.
- `currency`, `unit`: don vi.
- `source`: nguon du lieu.
- `is_imputed`: danh dau du lieu dien/fill-forward.
- `ingested_at`: thoi diem nap vao he thong.

## 5. Du lieu nao dua vao hash

MVP nen hash cac truong sau:

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

Khong nen hash:

```text
price_id
ingested_at
data_hash
blockchain_tx_hash
blockchain_status
```

Ly do:

- `price_id` la khoa dinh danh, nen dung de tra cuu chua can la noi dung du lieu.
- `ingested_at` co the khac nhau khi import lai.
- Cac truong blockchain sinh ra sau khi anchor.

## 6. Co the dung du lieu crawl cu khong?

Co, neu con mot trong cac dang sau:

```text
gold.fact_price_daily export CSV
gold_ml_features_export.csv
file .duckdb/.parquet/.csv da export
snapshot tu dashboard
```

Neu khong con file export, van co the:

- Dung schema `fact_price_daily` de tao dataset demo nho.
- Ghi ro trong bao cao rang du lieu demo duoc tao theo schema cua project cu.
- Sau nay khi co token moi hoac export cu, chi can thay dataset demo bang du lieu that.

Dataset demo tam thoi da duoc dat tai:

```text
data/sample/price_records_seed.csv
```

File nay chi dung de khoi dong blockchain MVP va test luong hash/anchor/verify. Khi tim duoc export cu tu MotherDuck, nen thay bang du lieu export that.

## 7. Luong khoi dong blockchain ban dau

Khuyen nghi lam theo thu tu:

1. Tao dataset local tu schema `fact_price_daily`.
2. Viet ham chuan hoa ban ghi thanh canonical JSON.
3. Tao hash cho tung ban ghi.
4. Viet smart contract `AgriPriceRegistry`.
5. Anchor 3-5 ban ghi mau len local blockchain.
6. Tao API verify mot ban ghi.
7. Ban giao response cho ban lam visualization.

## 8. Viec nen lam tiep

- Tao thu muc source moi tach khoi project cu, vi du:

```text
contracts/
backend/
frontend/
data/sample/
```

- Khong sua lon `dbt/`, `ingest/`, `ml/` trong giai doan dau.
- Khi code blockchain on dinh moi quyet dinh co import lai dashboard Streamlit hay lam UI moi.
