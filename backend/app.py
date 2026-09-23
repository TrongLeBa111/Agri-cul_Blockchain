from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from backend.blockchain_service import BlockchainService, proof_to_dict
from backend.hashing import data_hash, fingerprint, load_price_records, qr_payload
from backend.local_chain import LocalProofLedger


ROOT_DIR = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT_DIR / "data" / "sample" / "price_records_seed.csv"
LEDGER_PATH = ROOT_DIR / "data" / "local" / "proof_ledger.json"
DEFAULT_CREATOR = "local-demo-wallet"


def load_records() -> dict[str, dict[str, str]]:
    rows = load_price_records(SEED_PATH)
    return {row["price_id"]: row for row in rows}


class AgriPriceHandler(BaseHTTPRequestHandler):
    server_version = "AgriPriceBlockchain/0.1"

    @property
    def records(self) -> dict[str, dict[str, str]]:
        return self.server.records

    @property
    def blockchain(self) -> BlockchainService:
        return self.server.blockchain

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path_parts = [part for part in parsed.path.split("/") if part]

        if parsed.path == "/api/prices":
            return self._json(self._filter_records(parse_qs(parsed.query)))

        if parsed.path == "/api/transactions":
            return self._json(self.blockchain.get_transactions())

        if parsed.path == "/api/stats":
            return self._stats()

        if len(path_parts) == 3 and path_parts[:2] == ["api", "prices"]:
            return self._price_detail(path_parts[2])

        if len(path_parts) == 4 and path_parts[:2] == ["api", "prices"] and path_parts[3] == "verify":
            return self._verify(path_parts[2])

        if len(path_parts) == 4 and path_parts[:2] == ["api", "prices"] and path_parts[3] == "qr-payload":
            base_url = parse_qs(parsed.query).get("base_url", ["http://localhost:8000"])[0]
            return self._qr_payload(path_parts[2], base_url)

        if len(path_parts) == 4 and path_parts[:2] == ["api", "prices"] and path_parts[3] == "lifecycle":
            return self._lifecycle(path_parts[2])

        if len(path_parts) == 2 and path_parts[0] == "verify":
            return self._verify_page(path_parts[1])

        return self._json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path_parts = [part for part in parsed.path.split("/") if part]

        if len(path_parts) == 4 and path_parts[:2] == ["api", "prices"] and path_parts[3] == "anchor":
            return self._anchor(path_parts[2])

        if len(path_parts) == 4 and path_parts[:2] == ["api", "prices"] and path_parts[3] == "lifecycle":
            return self._add_lifecycle(path_parts[2])

        return self._json({"error": "Not found"}, status=404)

    def _price_detail(self, record_id: str) -> None:
        record = self.records.get(record_id)
        if not record:
            return self._json({"error": "Price record not found"}, status=404)

        proof = self.blockchain.get_price_record_proof(record_id)
        hash_value = data_hash(record)
        body = {
            **record,
            "data_hash": hash_value,
            "fingerprint": fingerprint(hash_value),
            "blockchain_status": "ANCHORED" if proof else "NOT_ANCHORED",
            "proof": proof_to_dict(proof),
        }
        return self._json(body)

    def _anchor(self, record_id: str) -> None:
        record = self.records.get(record_id)
        if not record:
            return self._json({"error": "Price record not found"}, status=404)

        hash_value = data_hash(record)
        proof = self.blockchain.anchor_price_record(
            record_id=record_id,
            data_hash=hash_value,
            source=record["source"],
            created_by=DEFAULT_CREATOR,
        )
        return self._json(
            {
                "id": record_id,
                "data_hash": hash_value,
                "fingerprint": fingerprint(hash_value),
                "transaction_hash": proof.tx_hash,
                "blockchain_status": "ANCHORED",
                "proof": proof_to_dict(proof),
                "blockchain_backend": self.blockchain.status(),
            }
        )

    def _verify(self, record_id: str) -> None:
        record = self.records.get(record_id)
        if not record:
            return self._json({"error": "Price record not found"}, status=404)

        proof = self.blockchain.get_price_record_proof(record_id)
        current_hash = data_hash(record)
        stored_hash = proof.data_hash if proof else None
        verified = self.blockchain.verify_price_record(record_id, current_hash) if proof else False
        return self._json(
            {
                "id": record_id,
                "current_hash": current_hash,
                "stored_hash": stored_hash,
                "fingerprint": fingerprint(current_hash),
                "verified": verified,
                "blockchain_status": "VERIFIED" if verified else "NOT_ANCHORED" if proof is None else "TAMPERED",
                "proof": proof_to_dict(proof),
                "blockchain_backend": self.blockchain.status(),
            }
        )

    def _qr_payload(self, record_id: str, base_url: str) -> None:
        record = self.records.get(record_id)
        if not record:
            return self._json({"error": "Price record not found"}, status=404)
        return self._json(qr_payload(record, base_url=base_url))

    def _lifecycle(self, record_id: str) -> None:
        if record_id not in self.records:
            return self._json({"error": "Price record not found"}, status=404)
        return self._json([event.__dict__ for event in self.blockchain.get_lifecycle_events(record_id)])

    def _add_lifecycle(self, record_id: str) -> None:
        if record_id not in self.records:
            return self._json({"error": "Price record not found"}, status=404)

        body = self._read_json_body()
        event_type = str(body.get("event_type", "OBSERVED")).strip().upper()
        metadata_uri = str(body.get("metadata_uri", "")).strip()
        event_body = {
            "record_id": record_id,
            "event_type": event_type,
            "metadata_uri": metadata_uri,
            "metadata": body.get("metadata", {}),
        }
        import hashlib

        event_hash = "0x" + hashlib.sha256(
            json.dumps(event_body, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ).hexdigest()
        try:
            event = self.blockchain.add_lifecycle_event(
                record_id=record_id,
                event_type=event_type,
                event_hash=event_hash,
                metadata_uri=metadata_uri,
                created_by=DEFAULT_CREATOR,
            )
        except ValueError as exc:
            return self._json({"error": str(exc)}, status=409)
        return self._json({"event": event.__dict__, "blockchain_backend": self.blockchain.status()})

    def _verify_page(self, record_id: str) -> None:
        record = self.records.get(record_id)
        if not record:
            return self._html("<h1>Price record not found</h1>", status=404)

        proof = self.blockchain.get_price_record_proof(record_id)
        current_hash = data_hash(record)
        verified = self.blockchain.verify_price_record(record_id, current_hash) if proof else False
        status = "VERIFIED" if verified else "NOT ANCHORED" if proof is None else "TAMPERED"
        tx_hash = proof.tx_hash if proof else "N/A"
        lifecycle_count = len(self.blockchain.get_lifecycle_events(record_id))
        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Agri Price Proof</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; background: #f7faf8; color: #142018; }}
    main {{ max-width: 760px; margin: auto; background: white; border: 1px solid #dbe7dd; padding: 24px; }}
    code {{ overflow-wrap: anywhere; }}
    .ok {{ color: #0b7a33; font-weight: 700; }}
    .bad {{ color: #b42318; font-weight: 700; }}
  </style>
</head>
<body>
  <main>
    <h1>Agri Price Proof</h1>
    <p>Status: <span class="{'ok' if verified else 'bad'}">{status}</span></p>
    <p>Record: <code>{record_id}</code></p>
    <p>Commodity: {record['commodity']} | Date: {record['price_date']} | Source: {record['source']}</p>
    <p>Hash: <code>{current_hash}</code></p>
    <p>Transaction: <code>{tx_hash}</code></p>
    <p>Lifecycle events: {lifecycle_count}</p>
  </main>
</body>
</html>"""
        return self._html(html)

    def _filter_records(self, query: dict[str, list[str]]) -> list[dict[str, str]]:
        filters = {
            key: values[0].strip().lower()
            for key, values in query.items()
            if key in {"commodity", "source", "region"} and values and values[0].strip()
        }
        records = list(self.records.values())
        for key, value in filters.items():
            records = [record for record in records if value in record.get(key, "").lower()]
        return records

    def _stats(self) -> None:
        proofs = {
            record_id: self.blockchain.get_price_record_proof(record_id)
            for record_id in self.records
        }
        total_records = len(self.records)
        total_anchored = sum(1 for proof in proofs.values() if proof)
        total_verified = sum(
            1
            for record_id, proof in proofs.items()
            if proof and self.blockchain.verify_price_record(record_id, data_hash(self.records[record_id]))
        )
        return self._json(
            {
                "total_records": total_records,
                "total_anchored": total_anchored,
                "total_verified": total_verified,
                "total_unanchored": total_records - total_anchored,
                "blockchain_backend": self.blockchain.status(),
            }
        )

    def _read_json_body(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def _json(self, body: object, status: int = 200) -> None:
        encoded = json.dumps(body, ensure_ascii=True, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


class AgriPriceServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int]) -> None:
        super().__init__(server_address, AgriPriceHandler)
        self.records = load_records()
        self.ledger = LocalProofLedger(LEDGER_PATH)
        self.blockchain = BlockchainService(self.ledger)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = AgriPriceServer((host, port))
    print(f"Agri Price Blockchain API running at http://{host}:{port}")
    print(f"Loaded {len(server.records)} price records from {SEED_PATH}")
    print(f"Blockchain backend: {server.blockchain.status()['mode']}")
    server.serve_forever()


if __name__ == "__main__":
    run()
