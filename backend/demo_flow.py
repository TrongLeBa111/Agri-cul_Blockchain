from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from backend.hashing import data_hash, fingerprint, load_price_records, qr_payload
from backend.local_chain import LocalProofLedger


ROOT_DIR = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT_DIR / "data" / "sample" / "price_records_seed.csv"
LEDGER_PATH = ROOT_DIR / "data" / "local" / "demo_proof_ledger.json"


def main() -> None:
    records = load_price_records(SEED_PATH)
    ledger = LocalProofLedger(LEDGER_PATH)
    record = records[0]
    record_id = record["price_id"]
    hash_value = data_hash(record)
    proof = ledger.anchor_price_record(
        record_id=record_id,
        data_hash=hash_value,
        source=record["source"],
        created_by="demo-flow",
    )
    verified = ledger.verify_price_record(record_id, hash_value)

    print("record_id:", record_id)
    print("data_hash:", hash_value)
    print("fingerprint:", fingerprint(hash_value))
    print("tx_hash:", proof.tx_hash)
    print("verified:", verified)
    print("qr_payload:", qr_payload(record))

    lifecycle = ledger.add_lifecycle_event(
        record_id=record_id,
        event_type="INGESTED",
        event_hash=hash_value,
        metadata_uri="local://data/sample/price_records_seed.csv",
        created_by="demo-flow",
    )
    print("lifecycle_event:", asdict(lifecycle))


if __name__ == "__main__":
    main()

