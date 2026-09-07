#!/usr/bin/env python3
"""Compiles and deploys FaceProofRegistry.sol to any EVM-compatible chain
configured via RPC_URL / PRIVATE_KEY, then writes the ABI so the pipeline
can anchor proofs on-chain. Print the resulting address into CONTRACT_ADDRESS
in your .env file.

Usage:
    python scripts/deploy_contract.py
"""
import json
import os
from pathlib import Path

from solcx import compile_standard, install_solc
from web3 import Web3

CONTRACT_PATH = Path(__file__).parent.parent / "contracts" / "FaceProofRegistry.sol"
ABI_OUTPUT_PATH = Path(__file__).parent.parent / "contracts" / "FaceProofRegistry.abi.json"
SOLC_VERSION = "0.8.20"


def compile_contract():
    install_solc(SOLC_VERSION)
    source = CONTRACT_PATH.read_text()
    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": {"FaceProofRegistry.sol": {"content": source}},
            "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}},
        },
        solc_version=SOLC_VERSION,
    )
    contract_data = compiled["contracts"]["FaceProofRegistry.sol"]["FaceProofRegistry"]
    return contract_data["abi"], contract_data["evm"]["bytecode"]["object"]


def main() -> None:
    rpc_url = os.environ["RPC_URL"]
    private_key = os.environ["PRIVATE_KEY"]

    abi, bytecode = compile_contract()
    ABI_OUTPUT_PATH.write_text(json.dumps(abi, indent=2))

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = w3.eth.account.from_key(private_key)
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    tx = contract.constructor().build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 1_500_000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"Deployed FaceProofRegistry at: {receipt.contractAddress}")
    print("Set this as CONTRACT_ADDRESS in your .env file.")


if __name__ == "__main__":
    main()
