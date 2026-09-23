"""Fetch public commodity prices and write the blockchain seed CSV.

This script does not use MotherDuck. It rebuilds the MVP seed from public
sources:

- World Bank Pink Sheet monthly data
- Yahoo Finance commodity futures via yfinance
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT_DIR / "data" / "sample" / "price_records_seed.csv"
DEFAULT_DAYS = 90
MAX_RECORDS = 500
WORLD_BANK_LANDING_URL = "https://www.worldbank.org/en/research/commodity-markets"
WORLD_BANK_FALLBACK_XLSX_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)

CSV_COLUMNS = [
    "price_id",
    "commodity",
    "price_date",
    "region",
    "country",
    "price_usd_per_kg",
    "currency",
    "unit",
    "source",
    "is_imputed",
    "ingested_at",
]

WORLD_BANK_COLUMNS = {
    "rice": {"keyword": "Rice, Thai 5%", "scale": 1 / 1000},
    "coffee": {"keyword": "Coffee, Arabica", "scale": 1},
    "cocoa": {"keyword": "Cocoa", "scale": 1},
    "cotton": {"keyword": "Cotton, A Index", "scale": 1},
}

YAHOO_CONTRACTS = {
    "coffee": {"ticker": "KC=F", "unit": "cents/lb"},
    "rice": {"ticker": "ZR=F", "unit": "cents/cwt"},
    "cocoa": {"ticker": "CC=F", "unit": "usd/metric_ton"},
    "cotton": {"ticker": "CT=F", "unit": "cents/lb"},
}

LB_TO_KG = 0.45359237
CWT_TO_KG = 45.359237


def md5_record_id(source: str, commodity: str, price_date: str, region: str) -> str:
    raw = f"{source}|{commodity}|{price_date}|{region}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def normalize_commodity_filter(items: list[str] | None) -> set[str]:
    allowed = set(WORLD_BANK_COLUMNS)
    if not items:
        return allowed
    selected = {item.lower().strip() for item in items}
    unknown = selected - allowed
    if unknown:
        raise ValueError(f"Unsupported commodities: {', '.join(sorted(unknown))}")
    return selected


def discover_world_bank_xlsx_url() -> str:
    try:
        import requests
    except ImportError:
        return WORLD_BANK_FALLBACK_XLSX_URL

    try:
        response = requests.get(WORLD_BANK_LANDING_URL, timeout=20)
        response.raise_for_status()
    except requests.RequestException:
        return WORLD_BANK_FALLBACK_XLSX_URL

    matches = re.findall(r"https://[^\"']+CMO-Historical-Data-Monthly\.xlsx", response.text)
    return matches[0] if matches else WORLD_BANK_FALLBACK_XLSX_URL


def find_column(columns: list[str], keyword: str) -> str | None:
    normalized_keyword = keyword.lower()
    for column in columns:
        if normalized_keyword in str(column).lower():
            return column
    return None


def to_month_start(value: Any) -> str | None:
    try:
        import pandas as pd
    except ImportError:
        print("[ERROR] pandas is required. Run: pip install pandas openpyxl", file=sys.stderr)
        sys.exit(1)

    text = str(value).strip()
    if re.fullmatch(r"\d{4}M\d{2}", text):
        timestamp = pd.to_datetime(text, format="%YM%m", errors="coerce")
    else:
        timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return None
    return timestamp.strftime("%Y-%m-01")


def parse_world_bank_date_series(series: Any) -> Any:
    import pandas as pd

    text_series = series.astype(str).str.strip()
    if text_series.str.fullmatch(r"\d{4}M\d{2}").any():
        return pd.to_datetime(text_series, format="%YM%m", errors="coerce")
    return pd.to_datetime(series, errors="coerce")


def fetch_world_bank_rows(commodities: set[str], days: int) -> list[dict[str, str]]:
    try:
        import pandas as pd
    except ImportError:
        print("[ERROR] pandas/openpyxl are required. Run: pip install pandas openpyxl", file=sys.stderr)
        sys.exit(1)

    url = discover_world_bank_xlsx_url()
    print(f"[INFO] Fetching World Bank Pink Sheet: {url}")
    try:
        df = pd.read_excel(url, sheet_name="Monthly Prices", skiprows=4)
    except ImportError:
        print("[WARN] openpyxl is not installed. Skipping World Bank rows.")
        print("[WARN] Install it with: pip install openpyxl")
        return []
    df.columns = [str(column).strip() for column in df.columns]
    date_column = df.columns[0]
    cutoff = pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(days=days)
    ingested_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows: list[dict[str, str]] = []

    for commodity in sorted(commodities):
        config = WORLD_BANK_COLUMNS[commodity]
        price_column = find_column(list(df.columns), config["keyword"])
        if price_column is None:
            print(f"[WARN] World Bank column not found for {commodity}: {config['keyword']}")
            continue

        selected = df[[date_column, price_column]].dropna()
        selected[date_column] = parse_world_bank_date_series(selected[date_column])
        selected = selected.dropna(subset=[date_column])
        selected = selected[selected[date_column] >= cutoff]

        for _, row in selected.iterrows():
            price = float(row[price_column]) * float(config["scale"])
            if price <= 0:
                continue
            price_date = to_month_start(row[date_column])
            if price_date is None:
                continue
            source = "WORLD_BANK"
            region = "global"
            rows.append(
                {
                    "price_id": md5_record_id(source, commodity, price_date, region),
                    "commodity": commodity,
                    "price_date": price_date,
                    "region": region,
                    "country": "global",
                    "price_usd_per_kg": f"{price:.6f}",
                    "currency": "USD",
                    "unit": "kg",
                    "source": source,
                    "is_imputed": "false",
                    "ingested_at": ingested_at,
                }
            )

    return rows


def yahoo_price_to_kg(commodity: str, close_price: float) -> float:
    if commodity in {"coffee", "cotton"}:
        return (close_price / 100.0) / LB_TO_KG
    if commodity == "cocoa":
        return close_price / 1000.0
    if commodity == "rice":
        return (close_price / 100.0) / CWT_TO_KG
    raise ValueError(f"Unsupported commodity: {commodity}")


def fetch_yahoo_rows(commodities: set[str], days: int) -> list[dict[str, str]]:
    try:
        import pandas as pd
        import yfinance as yf
    except ImportError:
        print("[WARN] yfinance is not installed. Skipping Yahoo Finance rows.")
        print("[WARN] Install it with: pip install yfinance pandas")
        return []

    ingested_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows: list[dict[str, str]] = []

    for commodity in sorted(commodities):
        contract = YAHOO_CONTRACTS[commodity]
        ticker = contract["ticker"]
        print(f"[INFO] Fetching Yahoo Finance {commodity}: {ticker}")
        df = yf.download(ticker, period=f"{max(days, 7)}d", interval="1d", progress=False)
        if df.empty:
            print(f"[WARN] Yahoo Finance returned no rows for {ticker}")
            continue

        if isinstance(df.columns, pd.MultiIndex):
            close = df["Close"][ticker] if ("Close", ticker) in df.columns else df["Close"].iloc[:, 0]
        else:
            close = df["Close"]

        for date_value, close_price in close.dropna().items():
            price = yahoo_price_to_kg(commodity, float(close_price))
            if price <= 0:
                continue
            price_date = pd.to_datetime(date_value).strftime("%Y-%m-%d")
            source = "YAHOO_FINANCE"
            region = "us_futures"
            rows.append(
                {
                    "price_id": md5_record_id(source, commodity, price_date, region),
                    "commodity": commodity,
                    "price_date": price_date,
                    "region": region,
                    "country": "United States",
                    "price_usd_per_kg": f"{price:.6f}",
                    "currency": "USD",
                    "unit": "kg",
                    "source": source,
                    "is_imputed": "false",
                    "ingested_at": ingested_at,
                }
            )

    return rows


def dedupe_and_sort(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id = {row["price_id"]: row for row in rows}
    return sorted(
        by_id.values(),
        key=lambda row: (row["price_date"], row["source"], row["commodity"], row["region"]),
        reverse=True,
    )[:MAX_RECORDS]


def backup_existing(output: Path) -> Path | None:
    if not output.exists():
        return None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = output.with_name(f"{output.stem}.backup_{timestamp}{output.suffix}")
    shutil.move(str(output), str(backup))
    return backup


def write_csv(output: Path, rows: list[dict[str, str]]) -> Path | None:
    output.parent.mkdir(parents=True, exist_ok=True)
    backup = backup_existing(output)
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return backup


def print_preview(rows: list[dict[str, str]], limit: int = 10) -> None:
    print(f"[INFO] Rows: {len(rows)}")
    for row in rows[:limit]:
        print(
            f"  {row['price_id']} | {row['commodity']} | {row['price_date']} | "
            f"{row['region']} | {row['source']} | {row['price_usd_per_kg']}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch public data and rebuild blockchain seed CSV.")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help=f"Recent days to fetch. Default: {DEFAULT_DAYS}.")
    parser.add_argument("--commodity", nargs="+", help="Filter commodities, e.g. --commodity rice coffee.")
    parser.add_argument("--source", choices=["worldbank", "yahoo", "both"], default="both")
    parser.add_argument("--dry-run", action="store_true", help="Preview rows without writing the CSV.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    commodities = normalize_commodity_filter(args.commodity)
    rows: list[dict[str, str]] = []

    if args.source in {"worldbank", "both"}:
        rows.extend(fetch_world_bank_rows(commodities, args.days))
    if args.source in {"yahoo", "both"}:
        rows.extend(fetch_yahoo_rows(commodities, args.days))

    rows = dedupe_and_sort(rows)
    if not rows:
        print("[WARN] No rows fetched.")
        return

    print_preview(rows)
    if args.dry_run:
        print("[DRY-RUN] No file was written.")
        return

    backup = write_csv(args.output, rows)
    if backup:
        print(f"[INFO] Backed up previous seed to {backup}")
    print(f"[OK] Wrote {len(rows)} records to {args.output}")


if __name__ == "__main__":
    main()
