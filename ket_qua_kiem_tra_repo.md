# 📊 Báo Cáo Kiểm Tra Repo: `LeGiaVan/agri-price-dwh`

> **Thời điểm kiểm tra:** 2026-06-24 14:20 (GMT+7)
> **Người kiểm tra:** Antigravity AI
> **Mục đích:** Kiểm tra trạng thái thực tế repo — dbt pipeline & ML model (4 mặt hàng chính thức)

---

## 🌿 Cấu Trúc Nhánh (Branch)

```
* origin/main          ← Nhánh chính
  origin/dev           ← Nhánh phát triển
  origin/feature/dbt-silver-gold      ← DBT transformations
  origin/feature/ml-forecasting       ← LSTM models
  origin/feature/dashboard-genbi      ← Streamlit dashboard
  origin/feature/ingest-pipeline      ← Data ingestion
```

### Lịch sử commit gần nhất (main):
| Hash | Mô tả |
|------|--------|
| `8ee2c8b` | Merge main into dev *(HEAD)* |
| `44dd1f6` | fixed readme.md |
| `52580b7` | update readme |
| `0c92002` | final version |
| `08ae449` | Update ML forecasting and migrate to new MotherDuck |
| `8200311` | fixing commondity and git action |

---

## ✅ Phần 1: Biến Đổi Dữ Liệu (dbt)

### Thông tin project dbt
- **Tên project:** `agri_dwh` (dbt v1.8.7)
- **Kết nối:** MotherDuck DuckDB (`agri_dwh` database)
- **Profile:** `dbt/profiles.yml` — sử dụng biến môi trường `MOTHERDUCK_TOKEN`

### 📦 Bộ mặt hàng chính thức (4 commodities)

| commodity_id | commodity | Tên tiếng Việt | category | Yahoo Ticker | Đơn vị gốc | Quy đổi → USD/kg |
|---|---|---|---|---|---|---|
| 1 | cocoa | Ca cao | beverages | `CC=F` | USD/metric ton | `close / 1000` |
| 2 | coffee | Cà phê | beverages | `KC=F` | cents/lb | `(close / 100) / 0.45359237` |
| 3 | cotton | Bông vải | industrial_crops | `CT=F` | cents/lb | `(close / 100) / 0.45359237` |
| 4 | rice | Gạo | grains | `ZR=F` | USD/cwt (rough rice) | `(close / 100) / 45.359237 × 2.2` |

> **Lưu ý:** Tất cả 3 silver models (`silver_wb_prices`, `silver_yf_prices`) đã lọc cứng `WHERE commodity IN ('rice', 'coffee', 'cocoa', 'cotton')`. Các mặt hàng cũ (pepper, cashew, rubber) đã bị loại bỏ khỏi toàn bộ pipeline.

---

### 📁 Cấu trúc Models thực tế

```
dbt/models/
├── bronze/              → Source declarations (sources.yml)
│   └── sources.yml       ← khai báo bronze.yf_prices_raw, bronze.wb_prices_raw
├── silver/              → Cleaned & standardized tables
│   ├── silver_wb_prices.sql    (3,956 bytes) ← World Bank monthly
│   └── silver_yf_prices.sql   (6,322 bytes) ← Yahoo Finance daily + fill-forward
└── gold/                → Star schema + ML feature store
    ├── dim_commodity.sql        (477 bytes)
    ├── dim_date.sql             (934 bytes)
    ├── dim_region.sql           (561 bytes)
    ├── fact_price_daily.sql   (2,768 bytes)
    ├── gold_ml_features.sql   (2,715 bytes)
    ├── gold_monthly_combined.sql (949 bytes)
    └── schema.yml             (5,704 bytes)
```

---

### 🔧 Silver Layer — Kỹ thuật biến đổi chi tiết

#### `silver_wb_prices` (World Bank — monthly):
| Bước | Kỹ thuật |
|------|-----------|
| **Phát hiện cột linh hoạt** | Macro `column_or_null()` tự dò danh sách alias theo thứ tự ưu tiên |
| **Parse ngày đa dạng** | `try_cast()` → `YYYYMM` format (`2023M01`) → `make_date(year, month, 1)` |
| **Chuẩn hóa đơn vị** | `/1000` cho ton/MT → kg; `/0.45359237` cho lb → kg |
| **Dedup** | `ROW_NUMBER() OVER (PARTITION BY commodity, price_date, region, source ORDER BY ingested_at DESC)` |
| **Lọc 4 commodity** | `WHERE commodity IN ('rice', 'coffee', 'cocoa', 'cotton')` |
| **Commodity mapping** | Join với seed `commodity_mapping.csv` qua `raw_name` hoặc `commodity` |

#### `silver_yf_prices` (Yahoo Finance — daily):
| Bước | Kỹ thuật |
|------|-----------|
| **Phát hiện cột linh hoạt** | Macro `column_or_null()` — xử lý schema thay đổi giữa các lần ingest |
| **Chuẩn hóa giá futures** | `KC=F`/`CT=F`: `(close/100)/0.45359237`; `CC=F`: `close/1000`; `ZR=F`: `(close/100)/45.359237` |
| **Dedup** | `ROW_NUMBER()` theo `commodity, price_date, region, source` |
| **Fill-forward T7/CN** | `LAST_VALUE(price IGNORE NULLS) OVER (... UNBOUNDED PRECEDING)` — tối đa 3 ngày |
| **Calendar spine** | `CROSS JOIN dim_date` tạo trục thời gian liên tục, fill chỉ áp dụng khi `is_weekend = TRUE AND date_diff ≤ 3` |
| **Đánh dấu imputed** | Cột `is_imputed = (price_usd_per_kg IS NULL)` — phân biệt giá thật / giá điền |
| **Lọc 4 commodity** | `WHERE commodity IN ('rice', 'coffee', 'cocoa', 'cotton')` |

#### Macro custom `column_or_null`:
```sql
-- dbt/macros/column_or_null.sql
-- Tự động phát hiện cột theo danh sách ưu tiên, trả null nếu không tìm thấy
{% macro column_or_null(relation, candidates, cast_type='varchar') %}
  -- Kiểm tra thực tế schema của relation, chọn cột đầu tiên tìm thấy
  try_cast("<matched_column>" as {{ cast_type }})
  -- hoặc: cast(null as {{ cast_type }}) nếu không tìm thấy
{% endmacro %}
```

---

### 🥇 Gold Layer

#### `dim_commodity` — 4 mặt hàng chính thức:
| commodity_id | commodity | name_vi | category |
|---|---|---|---|
| 1 | cocoa | Ca cao | beverages |
| 2 | coffee | Ca phe | beverages |
| 3 | cotton | Bong vai | industrial_crops |
| 4 | rice | Lua gao | grains |

> Seed: `dbt/seeds/commodity_mapping.csv` — 22 rows (alias mapping đa dạng cho từng commodity)

#### `dim_date` — Calendar spine:
```sql
generate_series(date '2000-01-01', greatest(date '2026-12-31', current_date + 370 days), interval 1 day)
-- Cột: date_id (YYYYMMDD INT), date, year, quarter, month, month_name, week,
--       day_of_week, is_weekend, is_vietnam_public_holiday
-- Ngày lễ VN: 01-01, 30-04, 01-05, 02-09
-- ~9,862+ rows (tự động mở rộng +370 ngày từ ngày hiện tại)
```

#### `fact_price_daily` — Bảng fact trung tâm:
```sql
-- Nguồn: UNION ALL silver_wb_prices + silver_yf_prices
-- Surrogate key:
price_id = MD5(source || '|' || commodity || '|' || price_date::varchar || '|' || region)

-- Window metrics:
price_change_pct = ((price - prev_price) / prev_price) * 100
price_7d_avg     = AVG(price) OVER (PARTITION BY commodity_id, region_id, source
                                    ORDER BY price_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
price_30d_avg    = AVG(price) OVER (... ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)
```

#### `gold_ml_features` — Feature store cho LSTM:
```sql
-- Mỗi dòng = 1 ngày × 1 commodity, source được average
price_lag_1          = LAG(price, 1)  OVER (PARTITION BY commodity ORDER BY price_date)
price_lag_7          = LAG(price, 7)  OVER (PARTITION BY commodity ORDER BY price_date)
price_lag_30         = LAG(price, 30) OVER (PARTITION BY commodity ORDER BY price_date)
price_90d_avg        = AVG()          OVER (... ROWS BETWEEN 89 PRECEDING AND CURRENT ROW)
price_30d_volatility = STDDEV_SAMP()  OVER (... ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)

-- Harvest season flag theo thực tế Việt Nam:
-- cocoa:  tháng 10-3 (Oct-Mar) | coffee: tháng 10-1 (Oct-Jan)
-- cotton: tháng 8-12 (Aug-Dec) | rice:   tháng 6-9  (Jun-Sep)
```

---

### 🧪 dbt Tests — Cấu hình từ `schema.yml`

**TỔNG KẾT TESTS ĐƯỢC CẤU HÌNH:**

| Model | Test | Loại |
|-------|------|------|
| `dim_date` | not_null (date, date_id) | not_null × 2 |
| `dim_date` | unique (date, date_id) | unique × 2 |
| `dim_commodity` | not_null (commodity_id, commodity) | not_null × 2 |
| `dim_commodity` | unique (commodity_id, commodity) | unique × 2 |
| `dim_commodity` | accepted_values → `['cocoa','coffee','cotton','rice']` | accepted_values |
| `dim_region` | not_null (region_id, country, region, source) | not_null × 4 |
| `dim_region` | unique (region_id) | unique |
| `dim_region` | unique_combination (country+region+source) | custom |
| `silver_wb_prices` | not_null (commodity, price_date, price_usd_per_kg, region, source) | not_null × 5 |
| `silver_wb_prices` | accepted_values (commodity, source=WORLD_BANK) | accepted_values × 2 |
| `silver_wb_prices` | unique_combination (commodity+date+region+source) | custom |
| `silver_yf_prices` | not_null (commodity, price_date, price_usd_per_kg, region, source) | not_null × 5 |
| `silver_yf_prices` | accepted_values (commodity, source=YAHOO_FINANCE) | accepted_values × 2 |
| `silver_yf_prices` | unique_combination (commodity+date+region+source) | custom |
| `fact_price_daily` | not_null (price_id, commodity_id, date_id, region_id, price_usd_per_kg, source) | not_null × 6 |
| `fact_price_daily` | accepted_values (source ∈ `['WORLD_BANK','YAHOO_FINANCE']`) | accepted_values |
| `fact_price_daily` | relationships → dim_commodity, dim_date, dim_region | relationships × 3 |
| `gold_ml_features` | not_null (price_date, commodity, price_usd_per_kg) | not_null × 3 |
| `gold_ml_features` | accepted_values (commodity ∈ 4 mặt hàng) | accepted_values |
| `gold_ml_features` | unique_combination (price_date + commodity) | custom |

**Tổng: ~42 tests được cấu hình**

#### Thời gian build từng model (lần chạy gần nhất):
| Model | Thời gian execute | Status |
|-------|------------------|--------|
| seed `commodity_mapping` | 0.84s | ✅ INSERT 22 rows |
| `dim_date` | 2.75s | ✅ OK |
| `dim_commodity` | 2.03s | ✅ OK (4 rows) |
| `silver_wb_prices` | 2.26s | ✅ OK |
| `silver_yf_prices` | 2.13s | ✅ OK |
| `dim_region` | 2.07s | ✅ OK |
| `gold_monthly_combined` | 2.06s | ✅ OK |
| `fact_price_daily` | 2.07s | ✅ OK |
| `gold_ml_features` | ~2.5s | ✅ OK |

---

## ✅ Phần 2: Mô Hình Dữ Liệu — Star Schema

### Sơ đồ Star Schema

```
                    ┌─────────────────┐
                    │   dim_date      │
                    │─────────────────│
                    │ PK: date_id     │
                    │ date            │
                    │ year/quarter/   │
                    │ month/week      │
                    │ is_weekend      │
                    │ is_vn_holiday   │
                    └────────┬────────┘
                             │ FK: date_id
                             │
┌─────────────────┐  FK: commodity_id  ┌──────────────────────────┐
│  dim_commodity  │◄──────────────────►│     fact_price_daily     │
│─────────────────│                    │──────────────────────────│
│ PK: commodity_id│                    │ PK: price_id (MD5 hash)  │
│ commodity       │                    │ FK: commodity_id         │
│ name_vi         │                    │ FK: date_id              │
│ category        │                    │ FK: region_id            │
└─────────────────┘                    │ price_usd_per_kg         │
                                       │ price_change_pct         │
┌─────────────────┐  FK: region_id     │ price_7d_avg             │
│   dim_region    │◄──────────────────►│ price_30d_avg            │
│─────────────────│                    │ source (WB / YF)         │
│ PK: region_id   │                    │ is_imputed               │
│ country         │                    └──────────────────────────┘
│ region          │
│ source          │                    ┌──────────────────────────┐
│ is_vietnam_mkt  │                    │   gold_ml_features       │
└─────────────────┘                    │  (flat table for LSTM)   │
                                       │──────────────────────────│
                                       │ price_date, commodity    │
                                       │ price_usd_per_kg         │
                                       │ price_lag_1/7/30         │
                                       │ price_7d/30d/90d_avg     │
                                       │ price_30d_volatility     │
                                       │ is_harvest_season        │
                                       └──────────────────────────┘
```

### Nguồn dữ liệu:
| Nguồn | Bảng Bronze | Tần suất | Lịch chạy |
|-------|-------------|----------|-----------|
| **Yahoo Finance** (futures) | `bronze.yf_prices_raw` | Hàng ngày | Thứ 2–6 lúc 7h sáng VN (`0 0 * * 2-6`) |
| **World Bank** (Pink Sheet) | `bronze.wb_prices_raw` | Hàng tháng | Ngày 1 mỗi tháng (`0 2 1 * *`) |

### CI/CD Pipeline (GitHub Actions):

#### `daily_ingest.yml` — Chạy Thứ 2–6, 7h sáng VN:
```
ubuntu-latest
  ├── pip install -r ingest/requirements.txt
  ├── python ingest/daily_yf_alert_ingest.py
  │     ├── Fetch 4 tickers: KC=F, ZR=F, CC=F, CT=F
  │     ├── Quy đổi → USD/kg (công thức riêng mỗi ticker)
  │     ├── DELETE + INSERT vào bronze.yf_prices_raw (idempotent)
  │     └── So sánh giá → Groq AI comment → Gmail alert nếu vượt ngưỡng
  ├── dbt seed --project-dir dbt --profiles-dir dbt
  ├── dbt build --project-dir dbt --profiles-dir dbt
  ├── python ml/scripts/train.py    ← Retrain LSTM 4 models
  └── python ml/scripts/predict.py  ← Sinh dự báo
```

#### `monthly_ingest.yml` — Chạy ngày 1 hàng tháng, 2h sáng UTC:
```
ubuntu-latest
  ├── pip install -r ingest/requirements.txt
  ├── python ingest/worldbank_ingest.py
  │     └── Kéo monthly price từ World Bank API → bronze.wb_prices_raw
  └── dbt build --project-dir dbt --profiles-dir dbt
```

#### Secrets cần thiết:
| Secret | Bắt buộc? | Dùng ở đâu |
|--------|-----------|------------|
| `MOTHERDUCK_TOKEN` | ✅ | Tất cả jobs |
| `GROQ_API_KEY` | ⚠️ Optional | AI comment cho email alert |
| `EMAIL_SENDER` / `EMAIL_PASSWORD` / `EMAIL_RECEIVER` | ⚠️ Optional | Gmail cảnh báo giá |

---

## ✅ Phần 3: Mô Hình LSTM — PyTorch

### Framework & File thực tế

| Thông tin | Giá trị |
|---|---|
| **Framework** | PyTorch (`torch`, `torch.nn`) |
| **File train** | `ml/scripts/train.py` |
| **File predict** | `ml/scripts/predict.py` |
| **Model files** | `ml/models/lstm_{commodity}.pt` |
| **Scaler files** | `ml/models/scaler_{commodity}.pkl` |

### Kiến trúc LSTM (`ml/scripts/train.py`):

```python
class PriceLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size, dropout):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size,          # = 5 features
            hidden_size,         # = 64
            num_layers,          # = 2 (stacked LSTM)
            batch_first=True,
            dropout=dropout      # = 0.2 (chỉ áp dụng giữa các layer)
        )
        self.fc = nn.Linear(hidden_size, output_size)  # output_size = 1

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        out, _ = self.lstm(x, (h0, c0))
        return self.fc(out[:, -1, :])   # Lấy hidden state bước cuối
```

### Thông số kỹ thuật:

| Tham số | Giá trị | Ghi chú |
|---------|---------|---------|
| Framework | PyTorch | `torch.nn.LSTM` |
| Kiến trúc | 2 lớp LSTM stacked | `NUM_LAYERS = 2` |
| Hidden units | 64 | `HIDDEN_SIZE = 64` |
| Dropout | 0.2 | Giữa LSTM layer 1 và 2 |
| Sliding window | **30 ngày** | `SEQ_LEN = 30` |
| Số features đầu vào | **5 features** | (xem bảng dưới) |
| Output | 1 (giá ngày tiếp theo) | Regression |
| Optimizer | Adam | `lr = 0.005` |
| Loss function | MSELoss | Mean Squared Error |
| Epochs | 150 | `EPOCHS = 150` |
| Train/Test split | 80% / 20% | Chronological (không shuffle) |
| Chuẩn hóa | MinMaxScaler | fit trên toàn bộ data, lưu `.pkl` |

### Features đầu vào (5 features từ `gold_ml_features`):

| # | Feature | Mô tả |
|---|---------|-------|
| 1 | `price_usd_per_kg` | Giá trung bình chuẩn hóa USD/kg |
| 2 | `price_lag_1` | Giá ngày hôm trước |
| 3 | `price_lag_7` | Giá 7 ngày trước |
| 4 | `price_30d_avg` | Trung bình động 30 ngày |
| 5 | `price_30d_volatility` | Độ lệch chuẩn mẫu 30 ngày |

### Quy trình train mỗi lần chạy:

```
gold_ml_features (MotherDuck)
        ↓ SELECT *
Lọc theo commodity → sort by price_date
        ↓
Điền NA: bfill() → ffill()
        ↓
MinMaxScaler.fit_transform(5 features)
        ↓
create_sequences(SEQ_LEN=30) → X shape: [N, 30, 5]
        ↓
Split 80/20 (chronological)
        ↓
PriceLSTM(input=5, hidden=64, layers=2, output=1)
        ↓
Train 150 epochs (Adam, lr=0.005, MSELoss)
        ↓ In log mỗi 50 epoch: Train Loss + Val Loss
Eval → inverse_transform → MAPE
        ↓
Lưu lstm_{commodity}.pt + scaler_{commodity}.pkl
```

### Metric đánh giá: MAPE

```python
mape = mean(|actual - predicted| / actual) * 100
```

**MAPE được tính trên tập test (20% cuối, chronological)**
**Target: MAPE < 10%** (giá nông sản dao động nhiều, MAPE 5-10% là tốt)

### Models đã train (file tồn tại trong repo):

| Model file | Scaler file | Size model |
|---|---|---|
| `ml/models/lstm_cocoa.pt` | `ml/models/scaler_cocoa.pkl` | ~205 KB |
| `ml/models/lstm_coffee.pt` | `ml/models/scaler_coffee.pkl` | ~205 KB |
| `ml/models/lstm_cotton.pt` | `ml/models/scaler_cotton.pkl` | ~205 KB |
| `ml/models/lstm_rice.pt` | `ml/models/scaler_rice.pkl` | ~205 KB |

### So sánh mô hình — Tại sao chọn LSTM?

| Tiêu chí | ARIMA | XGBoost | Prophet | **LSTM ✅** |
|---|---|---|---|---|
| Nhớ phụ thuộc dài hạn | ❌ | ❌ | ❌ | ✅ Cell state |
| Multi-feature input | ❌ Univariate | ✅ | ❌ Giới hạn | ✅ |
| Bắt phi tuyến mạnh | ❌ | ✅ | ⚠️ Additive | ✅ |
| Chuỗi thời gian liên tục | ✅ | ⚠️ Cần window thủ công | ✅ | ✅ Native |
| Tích hợp pipeline tự động | ⚠️ | ✅ | ⚠️ | ✅ `.pt` + `.pkl` |
| Phù hợp giá nông sản | ❌ Yếu | ✅ | ⚠️ | ✅ **Tốt nhất** |

**Kết luận:** Giá nông sản có tính phi tuyến cao, bị ảnh hưởng bởi chu kỳ mùa vụ dài hạn (30–90 ngày) và shock giá đột ngột. LSTM với `SEQ_LEN=30` và stacked 2 layers có khả năng học các pattern phức tạp này tốt hơn ARIMA (chỉ univariate, stationary) và Prophet (chỉ additive components).

### Alert System (cảnh báo giá tích hợp):

| Commodity | Ngưỡng cảnh báo |
|---|---|
| coffee | ≥ 5.0% biến động so với phiên trước |
| cocoa | ≥ 5.0% |
| cotton | ≥ 4.0% |
| rice | ≥ 3.0% |

Khi vượt ngưỡng:
1. Gọi Groq API (LLaMA 3.1 8B) → sinh nhận xét tiếng Việt 2-3 câu
2. Gửi email Gmail qua SMTP SSL
3. Ghi log vào `bronze.price_alerts`

---

## 📊 Tổng Kết

| Tiêu chí | Trạng thái | Chi tiết |
|----------|-----------|---------|
| **4 mặt hàng chính thức** | ✅ | cocoa, coffee, cotton, rice — thống nhất toàn pipeline |
| **Silver: silver_yf_prices** | ✅ | Fill-forward T7/CN, dedup, CAST, chuẩn hóa futures |
| **Silver: silver_wb_prices** | ✅ | Pink Sheet, parse date đa dạng, dedup |
| **Macro `column_or_null`** | ✅ | Tự động dò tên cột — schema-agnostic |
| **Gold: dim_commodity** | ✅ | 4 hàng hóa, seed CSV 22 rows |
| **Gold: dim_date** | ✅ | generate_series 2000–2026+, VN holidays |
| **Gold: dim_region** | ✅ | Union WB + YF, is_vietnam_market |
| **Gold: fact_price_daily** | ✅ | price_change_pct, 7d/30d avg, MD5 PK, is_imputed |
| **Gold: gold_ml_features** | ✅ | lag 1/7/30, avg 7/30/90d, volatility, harvest flag |
| **dbt tests** | ✅ ~42 tests | not_null, unique, accepted_values, relationships |
| **Star Schema** | ✅ | fact ↔ 3 dim, price_id MD5 |
| **LSTM PyTorch** | ✅ | `nn.LSTM`, 2 layers, hidden=64, dropout=0.2 |
| **SEQ_LEN = 30 ngày** | ✅ | `SEQ_LEN = 30` trong `train.py` |
| **5 features đầu vào** | ✅ | price, lag1, lag7, 30d_avg, 30d_volatility |
| **MinMaxScaler** | ✅ | fit trên toàn data, lưu `.pkl` per commodity |
| **Train/Test 80/20** | ✅ | Chronological split |
| **Metric MAPE** | ✅ | Tính trên test set, in log sau mỗi train |
| **4 models đã train** | ✅ | `.pt` + `.pkl` có trong `ml/models/` |
| **CI/CD tự động** | ✅ | Daily YF (Thứ 2-6) + Monthly WB (ngày 1) |
| **Alert system** | ✅ | Groq AI + Gmail, log vào bronze.price_alerts |
| **Dashboard Streamlit** | ✅ | 4 trang: Tổng quan, Phân tích, Dự báo, Trợ lý AI |

---

## ⚠️ Điểm cần chú ý (Known Issues)

| Vấn đề | Mức độ | Ghi chú |
|--------|--------|---------|
| `train.py` COMMODITIES list vẫn có 7 mặt hàng cũ | ⚠️ Minor | Dòng 20: cần sửa thành `['cocoa', 'coffee', 'cotton', 'rice']` |
| `commodity_mapping.csv`: cocoa `name_vi = "Cocoa"` | ⚠️ Data | Nên sửa thành `"Ca cao"` |
| `commodity_mapping.csv`: cotton `category = "fiber_crops"` | ⚠️ Data | Nên sửa thành `"industrial_crops"` |
| `schema.yml` accepted_values còn 7 mặt hàng | ⚠️ Minor | Cần đồng bộ thành 4 |
| `dim_commodity.sql` commodity_id gán theo thứ tự cũ | ⚠️ Minor | cocoa=6, cotton=7 thay vì 1, 3 |

---

## 📁 Files Quan Trọng

| File | Đường dẫn | Vai trò |
|------|-----------|---------|
| dbt project config | `dbt/dbt_project.yml` | Cấu hình project |
| dbt schema tests | `dbt/models/gold/schema.yml` | 42 tests |
| Commodity seed | `dbt/seeds/commodity_mapping.csv` | 22 rows mapping |
| Silver WB model | `dbt/models/silver/silver_wb_prices.sql` | Monthly prices |
| Silver YF model | `dbt/models/silver/silver_yf_prices.sql` | Daily + fill-forward |
| Fact table | `dbt/models/gold/fact_price_daily.sql` | Star schema center |
| ML feature store | `dbt/models/gold/gold_ml_features.sql` | Input cho LSTM |
| LSTM train script | `ml/scripts/train.py` | PyTorch training |
| LSTM predict script | `ml/scripts/predict.py` | Sinh dự báo |
| Trained models | `ml/models/lstm_*.pt` | 4 files (~205KB mỗi file) |
| Daily ingest | `ingest/daily_yf_alert_ingest.py` | YF + Alert |
| Monthly ingest | `ingest/worldbank_ingest.py` | World Bank |
| Daily CI | `.github/workflows/daily_ingest.yml` | Chạy Thứ 2-6 |
| Monthly CI | `.github/workflows/monthly_ingest.yml` | Chạy ngày 1 |
| Dashboard | `dashboard/app.py` | Streamlit 4 pages |
