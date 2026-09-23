"""Export blockchain seed data from MotherDuck gold.fact_price_daily.

Examples:
    python scripts/export_blockchain_seed.py
    python scripts/export_blockchain_seed.py --days 180
    python scripts/export_blockchain_seed.py --commodity rice coffee
    python scripts/export_blockchain_seed.py --all
    python scripts/export_blockchain_seed.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT_DIR / "data" / "sample" / "price_records_seed.csv"
DEFAULT_COMMODITIES = ["rice", "coffee", "cocoa", "cotton"]
DEFAULT_DAYS = 90
MAX_RECORDS = 500
PREVIEW_ROWS = 3

BLOCKCHAIN_COLUMNS = [
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


def load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(ROOT_DIR / ".env")


def connect_motherduck():
    try:
        import duckdb
    except ImportError:
        print("[ERROR] duckdb is not installed. Run: pip install duckdb", file=sys.stderr)
        sys.exit(1)

    load_env()
    token = os.getenv("MOTHERDUCK_TOKEN", "").strip()
    if not token:
        print("[ERROR] MOTHERDUCK_TOKEN is required in .env or the environment.", file=sys.stderr)
        sys.exit(1)

    database = os.getenv("MOTHERDUCK_DB", "agri_dwh").strip()
    print(f"[INFO] Connecting to MotherDuck: md:{database}")
    return duckdb.connect(f"md:{database}?motherduck_token={token}")


def build_query(*, days: int, commodities: list[str] | None, fetch_all: bool) -> tuple[str, list[object]]:
    filters = [
        "price_id is not null",
        "commodity is not null",
        "price_date is not null",
        "price_usd_per_kg is not null",
    ]
    params: list[object] = []

    if not fetch_all:
        filters.append("cast(price_date as date) >= current_date - ?::integer")
        params.append(days)

        if commodities:
            placeholders = ", ".join("?" for _ in commodities)
            filters.append(f"lower(trim(cast(commodity as varchar))) in ({placeholders})")
            params.extend(commodity.lower().strip() for commodity in commodities)

    where_clause = " and ".join(filters)
    query = f"""
        select
            cast(price_id as varchar) as price_id,
            lower(trim(cast(commodity as varchar))) as commodity,
            cast(cast(price_date as date) as varchar) as price_date,
            lower(trim(cast(region as varchar))) as region,
            trim(cast(country as varchar)) as country,
            printf('%.6f', round(cast(price_usd_per_kg as double), 6)) as price_usd_per_kg,
            upper(trim(cast(currency as varchar))) as currency,
            lower(trim(cast(unit as varchar))) as unit,
            upper(trim(cast(source as varchar))) as source,
            case when cast(is_imputed as boolean) then 'true' else 'false' end as is_imputed,
            coalesce(
                strftime(cast(ingested_at as timestamp), '%Y-%m-%dT%H:%M:%SZ'),
                strftime(current_timestamp, '%Y-%m-%dT%H:%M:%SZ')
            ) as ingested_at
        from gold.fact_price_daily
        where {where_clause}
        order by price_date desc, source, commodity, region
        limit {MAX_RECORDS}
    """
    return query, params


def fetch_rows(*, days: int, commodities: list[str] | None, fetch_all: bool) -> list[dict[str, str]]:
    query, params = build_query(days=days, commodities=commodities, fetch_all=fetch_all)
    con = connect_motherduck()
    try:
        result = con.execute(query, params)
        columns = [description[0] for description in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()


def print_preview(rows: list[dict[str, str]]) -> None:
    print(f"[INFO] Rows matched: {len(rows)}")
    for row in rows[:PREVIEW_ROWS]:
        print(
            f"  {row['price_id']} | {row['commodity']} | {row['price_date']} | "
            f"{row['region']} | {row['source']} | {row['price_usd_per_kg']}"
        )


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
        writer = csv.DictWriter(file, fieldnames=BLOCKCHAIN_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return backup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export gold.fact_price_daily to the blockchain seed CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help=f"Recent days to export. Default: {DEFAULT_DAYS}.")
    parser.add_argument("--commodity", nargs="+", default=None, help="Filter commodities, e.g. --commodity rice coffee.")
    parser.add_argument("--all", action="store_true", dest="fetch_all", help=f"Ignore filters and export up to {MAX_RECORDS} rows.")
    parser.add_argument("--dry-run", action="store_true", help="Preview rows without writing the CSV.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"Output CSV path. Default: {DEFAULT_OUTPUT}.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    commodities = args.commodity if args.commodity is not None else DEFAULT_COMMODITIES
    rows = fetch_rows(days=args.days, commodities=commodities, fetch_all=args.fetch_all)
    if not rows:
        print("[WARN] No rows matched the export filters.")
        return

    print_preview(rows)
    if args.dry_run:
        print("[DRY-RUN] No file was written.")
        return

    backup = write_csv(args.output, rows)
    if backup:
        print(f"[INFO] Backed up previous seed to {backup}")
    print(f"[OK] Exported {len(rows)} records to {args.output}")


if __name__ == "__main__":
    main()
