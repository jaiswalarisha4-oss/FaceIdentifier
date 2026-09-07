import hashlib

from merkle import MerkleTree


def leaf(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def test_single_leaf_root_verifies_via_proof():
    leaves = [leaf(b"a")]
    tree = MerkleTree(leaves)
    proof = tree.get_proof(0)
    assert MerkleTree.verify_proof(leaves[0], proof, tree.root)


def test_odd_number_of_leaves_all_verify():
    leaves = [leaf(b"a"), leaf(b"b"), leaf(b"c")]
    tree = MerkleTree(leaves)
    for i, l in enumerate(leaves):
        proof = tree.get_proof(i)
        assert MerkleTree.verify_proof(l, proof, tree.root)


def test_even_number_of_leaves_all_verify():
    leaves = [leaf(b"a"), leaf(b"b"), leaf(b"c"), leaf(b"d")]
    tree = MerkleTree(leaves)
    for i, l in enumerate(leaves):
        proof = tree.get_proof(i)
        assert MerkleTree.verify_proof(l, proof, tree.root)


def test_tampered_leaf_fails_verification():
    leaves = [leaf(b"a"), leaf(b"b"), leaf(b"c"), leaf(b"d")]
    tree = MerkleTree(leaves)
    proof = tree.get_proof(1)
    tampered_leaf = leaf(b"tampered")
    assert not MerkleTree.verify_proof(tampered_leaf, proof, tree.root)


def test_tampered_proof_fails_verification():
    leaves = [leaf(b"a"), leaf(b"b"), leaf(b"c"), leaf(b"d")]
    tree = MerkleTree(leaves)
    proof = tree.get_proof(0)
    tampered_proof = [(leaf(b"garbage"), position) for _, position in proof]
    assert not MerkleTree.verify_proof(leaves[0], tampered_proof, tree.root)
