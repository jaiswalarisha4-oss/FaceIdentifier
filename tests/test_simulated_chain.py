from simulated_chain import SimulatedChain


def test_chain_is_valid_after_adding_blocks(tmp_path):
    chain_path = tmp_path / "chain.json"
    chain = SimulatedChain(storage_path=str(chain_path), difficulty=1)
    chain.add_block({"merkle_root": "aa" * 32})
    chain.add_block({"merkle_root": "bb" * 32})
    assert chain.is_valid()


def test_tampering_with_history_is_detected(tmp_path):
    chain_path = tmp_path / "chain.json"
    chain = SimulatedChain(storage_path=str(chain_path), difficulty=1)
    chain.add_block({"merkle_root": "aa" * 32})
    chain.add_block({"merkle_root": "bb" * 32})

    chain.chain[1]["data"]["merkle_root"] = "ff" * 32
    assert not chain.is_valid()


def test_find_block_by_root(tmp_path):
    chain_path = tmp_path / "chain.json"
    chain = SimulatedChain(storage_path=str(chain_path), difficulty=1)
    block = chain.add_block({"merkle_root": "cc" * 32, "metadata_uri": "local://x"})

    found = chain.find_block_by_root("cc" * 32)
    assert found is not None
    assert found["hash"] == block["hash"]
    assert chain.find_block_by_root("dd" * 32) is None


def test_chain_persists_across_instances(tmp_path):
    chain_path = tmp_path / "chain.json"
    chain = SimulatedChain(storage_path=str(chain_path), difficulty=1)
    chain.add_block({"merkle_root": "ee" * 32})

    reloaded = SimulatedChain(storage_path=str(chain_path), difficulty=1)
    assert reloaded.find_block_by_root("ee" * 32) is not None
    assert reloaded.is_valid()
