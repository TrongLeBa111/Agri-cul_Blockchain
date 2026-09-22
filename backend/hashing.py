from __future__ import annotations

import csv
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


HASH_DOMAIN = "AGRI_PRICE_BLOCKCHAIN"
HASH_VERSION = "v1"

HASH_FIELDS = (
    "commodity",
    "price_date",
    "region",
    "country",
    "price_usd_per_kg",
    "currency",
    "unit",
    "source",
    "is_imputed",
)


class PriceRecordError(ValueError):
    """Raised when a price record cannot be normalized for hashing."""


def _normalize_text(value: Any, *, uppercase: bool = False, lowercase: bool = False) -> str:
    normalized = "" if value is None else str(value).strip()
    if uppercase:
        return normalized.upper()
    if lowercase:
        return normalized.lower()
    return normalized


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _normalize_text(value, lowercase=True)
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", ""}:
        return False
    raise PriceRecordError(f"Invalid boolean value for is_imputed: {value!r}")


def _normalize_decimal(value: Any) -> str:
    try:
        decimal_value = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise PriceRecordError(f"Invalid price_usd_per_kg: {value!r}") from exc
    return f"{decimal_value.quantize(Decimal('0.000001'))}"


def canonical_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return the stable record payload that is protected by the data hash."""
    missing = [field for field in HASH_FIELDS if field not in record]
    if missing:
        raise PriceRecordError(f"Missing required field(s): {', '.join(missing)}")

    return {
        "commodity": _normalize_text(record["commodity"], lowercase=True),
        "price_date": _normalize_text(record["price_date"]),
        "region": _normalize_text(record["region"], lowercase=True),
        "country": _normalize_text(record["country"]),
        "price_usd_per_kg": _normalize_decimal(record["price_usd_per_kg"]),
        "currency": _normalize_text(record["currency"], uppercase=True),
        "unit": _normalize_text(record["unit"], lowercase=True),
        "source": _normalize_text(record["source"], uppercase=True),
        "is_imputed": _normalize_bool(record["is_imputed"]),
    }


def canonical_payload(record: dict[str, Any]) -> dict[str, Any]:
    """Wrap a canonical record with project-specific domain and version metadata."""
    return {
        "domain": HASH_DOMAIN,
        "version": HASH_VERSION,
        "record": canonical_record(record),
    }


def canonical_json(record: dict[str, Any]) -> str:
    """Serialize a record in a deterministic form before hashing."""
    payload = canonical_payload(record)
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=False)


def data_hash(record: dict[str, Any]) -> str:
    """Create a SHA-256 proof hash for a price record."""
    digest = hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()
    return f"0x{digest}"


def fingerprint(hash_value: str) -> str:
    clean_hash = hash_value.lower().removeprefix("0x")
    return f"AGR-{HASH_VERSION}-{clean_hash[:8].upper()}"


def qr_payload(record: dict[str, Any], base_url: str = "http://localhost:8000") -> dict[str, Any]:
    record_id = str(record.get("price_id") or record.get("id") or "").strip()
    if not record_id:
        raise PriceRecordError("Missing price_id/id for QR payload")

    hash_value = data_hash(record)
    return {
        "type": "agri-price-proof",
        "version": HASH_VERSION,
        "record_id": record_id,
        "hash": hash_value,
        "fingerprint": fingerprint(hash_value),
        "verify_url": f"{base_url.rstrip('/')}/verify/{record_id}",
    }


def load_price_records(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


if __name__ == "__main__":
    sample_path = Path(__file__).resolve().parents[1] / "data" / "sample" / "price_records_seed.csv"
    for row in load_price_records(sample_path)[:3]:
        hash_value = data_hash(row)
        print(row["price_id"], hash_value, fingerprint(hash_value))

