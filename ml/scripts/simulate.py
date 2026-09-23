"""
simulate_and_evaluate.py
Tạo dữ liệu giả lập sát thực tế, train LSTM, chạy evaluate → ra metrics
"""
import sys, os, pickle, json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

sys.path.insert(0, '/home/claude/ml/scripts')
from train import PriceLSTM, create_sequences, SEQ_LEN, HIDDEN_SIZE, NUM_LAYERS, DROPOUT, EPOCHS, LR

# ── Giá thực tế tham khảo (USD/kg, trung bình thị trường) ──────────────────
PRICE_PARAMS = {
    # commodity: (base_price, trend_per_month, volatility, seasonal_amp)
    'cocoa' : (3.2,   0.008,  0.15, 0.4),
    'coffee': (2.8,   0.012,  0.18, 0.3),
    'cotton': (1.7,  -0.002,  0.10, 0.15),
    'rice'  : (0.42,  0.001,  0.04, 0.03),
}

COMMODITIES = ['cocoa', 'coffee', 'cotton', 'rice']
FEATURES    = ['price_usd_per_kg', 'price_lag_1', 'price_lag_7',
               'price_30d_avg', 'price_30d_volatility']
MODEL_DIR   = '/home/claude/ml/models'
os.makedirs(MODEL_DIR, exist_ok=True)

np.random.seed(42)
torch.manual_seed(42)

# ── 1. Sinh dữ liệu giả lập ─────────────────────────────────────────────────
def generate_price_series(commodity: str, n_days: int = 1200) -> pd.DataFrame:
    base, trend, vol, amp = PRICE_PARAMS[commodity]
    dates = pd.date_range('2021-01-01', periods=n_days, freq='D')

    # Trend + seasonal + noise
    t = np.arange(n_days)
    seasonal = amp * np.sin(2 * np.pi * t / 365)
    noise    = np.random.normal(0, vol * base, n_days)
    prices   = base + trend * (t / 30) + seasonal + noise
    prices   = np.clip(prices, base * 0.3, base * 3.0)

    # Smooth một chút (3-day MA) để realistic hơn
    prices = pd.Series(prices).rolling(3, min_periods=1).mean().values

    df = pd.DataFrame({'price_date': dates, 'price_usd_per_kg': prices})

    # Tính features đúng như gold_ml_features.sql
    df['price_lag_1']         = df['price_usd_per_kg'].shift(1)
    df['price_lag_7']         = df['price_usd_per_kg'].shift(7)
    df['price_lag_30']        = df['price_usd_per_kg'].shift(30)
    df['price_30d_avg']       = df['price_usd_per_kg'].rolling(30, min_periods=1).mean()
    df['price_30d_volatility']= df['price_usd_per_kg'].rolling(30, min_periods=1).std().fillna(0)
    df['commodity']           = commodity

    df = df.bfill().ffill().dropna()
    return df

# ── 2. Train model ────────────────────────────────────────────────────────────
def train_model(commodity: str, df: pd.DataFrame):
    print(f"\n{'='*50}")
    print(f"  Training LSTM — {commodity.upper()}")
    print(f"{'='*50}")

    df = df.sort_values('price_date').reset_index(drop=True)
    df_feat = df[FEATURES].copy()

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df_feat.values)

    X, y = create_sequences(scaled, SEQ_LEN)
    split = int(len(X) * 0.8)

    X_tr, y_tr = X[:split], y[:split]
    X_te, y_te = X[split:], y[split:]

    X_tr_t = torch.tensor(X_tr, dtype=torch.float32)
    y_tr_t = torch.tensor(y_tr, dtype=torch.float32).unsqueeze(1)
    X_te_t = torch.tensor(X_te, dtype=torch.float32)
    y_te_t = torch.tensor(y_te, dtype=torch.float32).unsqueeze(1)

    model     = PriceLSTM(len(FEATURES), HIDDEN_SIZE, NUM_LAYERS, 1, DROPOUT)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    for epoch in range(EPOCHS):
        model.train()
        optimizer.zero_grad()
        out  = model(X_tr_t)
        loss = criterion(out, y_tr_t)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 50 == 0:
            model.eval()
            with torch.no_grad():
                val_loss = criterion(model(X_te_t), y_te_t)
            print(f"  Epoch {epoch+1:>3}/{EPOCHS} | Loss: {loss.item():.6f} | Val Loss: {val_loss.item():.6f}")

    # Save
    torch.save(model.state_dict(), f'{MODEL_DIR}/lstm_{commodity}.pt')
    with open(f'{MODEL_DIR}/scaler_{commodity}.pkl', 'wb') as f:
        pickle.dump(scaler, f)

    return model, scaler, X_te_t, y_te, split, df['price_date']

# ── 3. Evaluate ───────────────────────────────────────────────────────────────
def evaluate_commodity(commodity, model, scaler, X_te_t, y_te, split, date_col):
    model.eval()
    with torch.no_grad():
        preds_scaled = model(X_te_t).numpy()

    n = len(preds_scaled)

    preds_pad        = np.zeros((n, len(FEATURES)))
    preds_pad[:, 0]  = preds_scaled[:, 0]
    preds_inv        = scaler.inverse_transform(preds_pad)[:, 0]

    actual_pad       = np.zeros((n, len(FEATURES)))
    actual_pad[:, 0] = y_te
    actual_inv       = scaler.inverse_transform(actual_pad)[:, 0]

    _mse  = float(np.mean((actual_inv - preds_inv) ** 2))
    _rmse = float(np.sqrt(_mse))
    _mae  = float(np.mean(np.abs(actual_inv - preds_inv)))
    mask  = actual_inv != 0
    _mape = float(np.mean(np.abs((actual_inv[mask] - preds_inv[mask]) / actual_inv[mask])) * 100)

    test_dates = date_col.iloc[split + SEQ_LEN: split + SEQ_LEN + n]
    date_range = f"{test_dates.min().strftime('%Y-%m-%d')} → {test_dates.max().strftime('%Y-%m-%d')}"

    return {
        'commodity'     : commodity,
        'n_train'       : split,
        'n_test'        : n,
        'date_range_test': date_range,
        'mse'           : round(_mse,  6),
        'rmse'          : round(_rmse, 6),
        'mae'           : round(_mae,  6),
        'mape_pct'      : round(_mape, 2),
        'actual_mean'   : round(float(actual_inv.mean()), 4),
        'pred_mean'     : round(float(preds_inv.mean()),  4),
    }

# ── 4. Main ───────────────────────────────────────────────────────────────────
def main():
    print("\n🌾 Agri-Price DWH — LSTM Evaluation (Simulated Data)")
    print("=" * 60)

    all_results = []

    for comm in COMMODITIES:
        df = generate_price_series(comm, n_days=1200)
        print(f"\n[{comm}] Dữ liệu: {len(df)} rows | Giá TB: ${df['price_usd_per_kg'].mean():.3f}/kg")

        model, scaler, X_te_t, y_te, split, dates = train_model(comm, df)
        result = evaluate_commodity(comm, model, scaler, X_te_t, y_te, split, dates)
        all_results.append(result)

    # ── In bảng kết quả ─────────────────────────────────────────────────────
    print(f"\n\n{'='*75}")
    print("  KẾT QUẢ ĐÁNH GIÁ LSTM — 4 MẶT HÀNG")
    print(f"{'='*75}")
    print(f"{'Commodity':<10} {'N-Test':>7} {'MSE':>12} {'RMSE':>10} {'MAE':>10} {'MAPE%':>8}  Nhận xét")
    print('-' * 75)

    for r in all_results:
        m = r['mape_pct']
        note = '🟢 Xuất sắc' if m < 5 else ('🟡 Tốt' if m < 10 else ('🟠 Khá' if m < 20 else '🔴 Kém'))
        print(f"{r['commodity']:<10} {r['n_test']:>7} {r['mse']:>12.6f} {r['rmse']:>10.4f} {r['mae']:>10.4f} {m:>7.2f}%  {note}")

    print('-' * 75)
    avg_mape = np.mean([r['mape_pct'] for r in all_results])
    avg_rmse = np.mean([r['rmse']     for r in all_results])
    avg_mae  = np.mean([r['mae']      for r in all_results])
    avg_mse  = np.mean([r['mse']      for r in all_results])
    print(f"{'TRUNG BÌNH':<10} {'':>7} {avg_mse:>12.6f} {avg_rmse:>10.4f} {avg_mae:>10.4f} {avg_mape:>7.2f}%")

    print(f"\n📅 Khoảng thời gian test set:")
    for r in all_results:
        print(f"   {r['commodity']:<8}: {r['date_range_test']}")

    print(f"\n📊 Giá trung bình Actual vs Predicted:")
    for r in all_results:
        diff = abs(r['actual_mean'] - r['pred_mean'])
        print(f"   {r['commodity']:<8}: actual={r['actual_mean']:.4f}  pred={r['pred_mean']:.4f}  diff={diff:.4f} USD/kg")

    # Save JSON
    with open(f'{MODEL_DIR}/evaluation_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved: {MODEL_DIR}/evaluation_results.json")

if __name__ == '__main__':
    main()