from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from backend.local_chain import LifecycleEvent, LocalProofLedger, Proof


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RPC_URL = "http://127.0.0.1:8545"
DEFAULT_ARTIFACT_PATH = ROOT_DIR / "artifacts" / "contracts" / "AgriPriceRegistry.sol" / "AgriPriceRegistry.json"
DEFAULT_DEPLOYMENT_PATH = ROOT_DIR / "deployments" / "localhost.json"


class BlockchainService:
    """Bridge to the deployed Hardhat contract with a local ledger fallback."""

    def __init__(
        self,
        fallback_ledger: LocalProofLedger,
        rpc_url: str = DEFAULT_RPC_URL,
        artifact_path: str | Path = DEFAULT_ARTIFACT_PATH,
        deployment_path: str | Path = DEFAULT_DEPLOYMENT_PATH,
    ) -> None:
        self.fallback_ledger = fallback_ledger
        self.rpc_url = rpc_url
        self.artifact_path = Path(artifact_path)
        self.deployment_path = Path(deployment_path)
        self.mode = "local"
        self.contract_address: str | None = None
        self._web3: Any | None = None
        self._contract: Any | None = None
        self._account: str | None = None
        self._connect()

    def anchor_price_record(self, record_id: str, data_hash: str, source: str, created_by: str) -> Proof:
        if not self.is_rpc_enabled:
            return self.fallback_ledger.anchor_price_record(record_id, data_hash, source, created_by)

        existing = self.get_price_record_proof(record_id)
        if existing:
            return existing

        receipt = self._send_transaction(
            self._contract.functions.anchorPriceRecord(record_id, self._bytes32(data_hash), source)
        )
        proof_data = self._contract.functions.getPriceRecordProof(record_id).call()
        block_number = int(receipt["blockNumber"])
        tx_hash = receipt["transactionHash"].hex()
        created_at = int(proof_data[3])
        created_by_address = str(proof_data[2])
        return self.fallback_ledger.record_anchor(
            record_id=record_id,
            data_hash=data_hash,
            source=source,
            created_by=created_by_address,
            tx_hash=tx_hash,
            block_number=block_number,
            created_at=created_at,
        )

    def get_price_record_proof(self, record_id: str) -> Proof | None:
        if not self.is_rpc_enabled:
            return self.fallback_ledger.get_price_record_proof(record_id)

        data_hash, source, created_by, created_at, exists = self._contract.functions.getPriceRecordProof(record_id).call()
        if not exists:
            return None

        cached = self.fallback_ledger.get_price_record_proof(record_id)
        return Proof(
            record_id=record_id,
            data_hash=self._hex(data_hash),
            source=source,
            created_by=created_by,
            created_at=int(created_at),
            tx_hash=cached.tx_hash if cached else "",
            block_number=cached.block_number if cached else 0,
        )

    def verify_price_record(self, record_id: str, data_hash: str) -> bool:
        if not self.is_rpc_enabled:
            return self.fallback_ledger.verify_price_record(record_id, data_hash)
        return bool(self._contract.functions.verifyPriceRecord(record_id, self._bytes32(data_hash)).call())

    def add_lifecycle_event(
        self,
        record_id: str,
        event_type: str,
        event_hash: str,
        metadata_uri: str,
        created_by: str,
    ) -> LifecycleEvent:
        if not self.is_rpc_enabled:
            return self.fallback_ledger.add_lifecycle_event(
                record_id=record_id,
                event_type=event_type,
                event_hash=event_hash,
                metadata_uri=metadata_uri,
                created_by=created_by,
            )

        receipt = self._send_transaction(
            self._contract.functions.addLifecycleEvent(
                record_id,
                event_type,
                self._bytes32(event_hash),
                metadata_uri,
            )
        )
        block_number = int(receipt["blockNumber"])
        block = self._web3.eth.get_block(block_number)
        event = self.fallback_ledger.record_lifecycle_event(
            record_id=record_id,
            event_type=event_type,
            event_hash=event_hash,
            metadata_uri=metadata_uri,
            created_by=self._account or created_by,
            tx_hash=receipt["transactionHash"].hex(),
            block_number=block_number,
            created_at=int(block["timestamp"]),
        )
        return event

    def get_lifecycle_events(self, record_id: str) -> list[LifecycleEvent]:
        return self.fallback_ledger.get_lifecycle_events(record_id)

    def get_transactions(self) -> list[dict[str, Any]]:
        return self.fallback_ledger.get_transactions()

    @property
    def is_rpc_enabled(self) -> bool:
        return self._contract is not None

    def status(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "rpc_url": self.rpc_url,
            "contract_address": self.contract_address,
        }

    def _connect(self) -> None:
        try:
            from web3 import Web3
        except ImportError:
            return

        if not self.artifact_path.exists() or not self.deployment_path.exists():
            return

        web3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 1}))
        if not web3.is_connected():
            return

        artifact = json.loads(self.artifact_path.read_text(encoding="utf-8"))
        deployment = json.loads(self.deployment_path.read_text(encoding="utf-8"))
        address = web3.to_checksum_address(deployment["address"])
        code = web3.eth.get_code(address)
        if code in (b"", "0x"):
            return

        accounts = web3.eth.accounts
        if not accounts:
            return

        self._web3 = web3
        self._account = accounts[0]
        self.contract_address = address
        self._contract = web3.eth.contract(address=address, abi=artifact["abi"])
        self.mode = "hardhat"

    def _send_transaction(self, transaction: Any) -> Any:
        tx_hash = transaction.transact({"from": self._account})
        return self._web3.eth.wait_for_transaction_receipt(tx_hash)

    def _bytes32(self, hash_value: str) -> bytes:
        clean = hash_value.removeprefix("0x")
        if len(clean) != 64:
            raise ValueError(f"Expected bytes32 hex hash, got {hash_value!r}")
        return bytes.fromhex(clean)

    def _hex(self, value: Any) -> str:
        if isinstance(value, str):
            return value if value.startswith("0x") else f"0x{value}"
        return "0x" + bytes(value).hex()


def proof_to_dict(proof: Proof | None) -> dict[str, Any] | None:
    return asdict(proof) if proof else None
