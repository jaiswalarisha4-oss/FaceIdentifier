"""Anchors Merkle roots on any real EVM-compatible chain (public testnet,
mainnet, or a local node like Anvil/Ganache) via the FaceProofRegistry
contract. Used automatically by pipeline.py when RPC_URL, PRIVATE_KEY and
CONTRACT_ADDRESS are all present in the environment; otherwise the
pipeline falls back to simulated_chain.py.
"""
import json
import os
from pathlib import Path
from typing import Optional, Tuple

from web3 import Web3

ABI_PATH = Path(__file__).parent.parent / "contracts" / "FaceProofRegistry.abi.json"


class TestnetAnchor:
    def __init__(
        self,
        rpc_url: Optional[str] = None,
        private_key: Optional[str] = None,
        contract_address: Optional[str] = None,
    ):
        self.rpc_url = rpc_url or os.environ["RPC_URL"]
        self.private_key = private_key or os.environ["PRIVATE_KEY"]
        self.contract_address = Web3.to_checksum_address(
            contract_address or os.environ["CONTRACT_ADDRESS"]
        )
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.account = self.w3.eth.account.from_key(self.private_key)
        abi = json.loads(ABI_PATH.read_text())
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)

    @staticmethod
    def is_configured() -> bool:
        return all(os.environ.get(k) for k in ("RPC_URL", "PRIVATE_KEY", "CONTRACT_ADDRESS"))

    def anchor(self, merkle_root: bytes, metadata_uri: str) -> str:
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        tx = self.contract.functions.anchorProof(merkle_root, metadata_uri).build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "gas": 200_000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.transactionHash.hex()

    def verify(self, merkle_root: bytes) -> Tuple[str, int, str]:
        submitter, timestamp, metadata_uri = self.contract.functions.getProof(merkle_root).call()
        return submitter, timestamp, metadata_uri
