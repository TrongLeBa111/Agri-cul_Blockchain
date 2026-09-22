from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Proof:
    record_id: str
    data_hash: str
    source: str
    created_by: str
    created_at: int
    tx_hash: str
    block_number: int


@dataclass(frozen=True)
class LifecycleEvent:
    record_id: str
    event_type: str
    event_hash: str
    metadata_uri: str
    created_by: str
    created_at: int
    tx_hash: str
    block_number: int


class LocalProofLedger:
    """Small file-backed stand-in for a blockchain while contract deployment is not set up."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"proofs": {}, "lifecycle_events": []})

    def anchor_price_record(self, record_id: str, data_hash: str, source: str, created_by: str) -> Proof:
        data = self._read()
        proofs = data["proofs"]
        if record_id in proofs:
            existing = proofs[record_id]
            return Proof(**existing)

        proof = Proof(
            record_id=record_id,
            data_hash=data_hash,
            source=source,
            created_by=created_by,
            created_at=int(time.time()),
            tx_hash=self._make_tx_hash(record_id, data_hash),
            block_number=len(proofs) + len(data["lifecycle_events"]) + 1,
        )
        proofs[record_id] = asdict(proof)
        self._write(data)
        return proof

    def get_price_record_proof(self, record_id: str) -> Proof | None:
        proof = self._read()["proofs"].get(record_id)
        return Proof(**proof) if proof else None

    def verify_price_record(self, record_id: str, data_hash: str) -> bool:
        proof = self.get_price_record_proof(record_id)
        return bool(proof and proof.data_hash.lower() == data_hash.lower())

    def add_lifecycle_event(
        self,
        record_id: str,
        event_type: str,
        event_hash: str,
        metadata_uri: str,
        created_by: str,
    ) -> LifecycleEvent:
        data = self._read()
        event = LifecycleEvent(
            record_id=record_id,
            event_type=event_type,
            event_hash=event_hash,
            metadata_uri=metadata_uri,
            created_by=created_by,
            created_at=int(time.time()),
            tx_hash=self._make_tx_hash(record_id, event_hash),
            block_number=len(data["proofs"]) + len(data["lifecycle_events"]) + 1,
        )
        data["lifecycle_events"].append(asdict(event))
        self._write(data)
        return event

    def get_lifecycle_events(self, record_id: str) -> list[LifecycleEvent]:
        events = [
            LifecycleEvent(**event)
            for event in self._read()["lifecycle_events"]
            if event["record_id"] == record_id
        ]
        return events

    def _make_tx_hash(self, record_id: str, hash_value: str) -> str:
        raw = f"{record_id}|{hash_value}|{time.time_ns()}|{uuid.uuid4()}"
        import hashlib

        return "0x" + hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _read(self) -> dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write(self, data: dict[str, Any]) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=True, indent=2)
        tmp_path.replace(self.path)

