// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title FaceProofRegistry
/// @notice Anchors Merkle roots that summarize batches of off-chain
/// "face scan -> matching social media post" evidence. Only a 32-byte
/// root and a pointer to off-chain metadata are stored on-chain -- never
/// raw images or biometric data -- so a single cheap transaction can
/// attest to many independently-verifiable discoveries at once.
contract FaceProofRegistry {
    struct Proof {
        address submitter;
        uint256 timestamp;
        string metadataURI;
    }

    mapping(bytes32 => Proof) public proofs;

    event ProofAnchored(
        bytes32 indexed merkleRoot,
        address indexed submitter,
        uint256 timestamp,
        string metadataURI
    );

    function anchorProof(bytes32 merkleRoot, string calldata metadataURI) external {
        require(proofs[merkleRoot].timestamp == 0, "Proof already anchored");
        proofs[merkleRoot] = Proof(msg.sender, block.timestamp, metadataURI);
        emit ProofAnchored(merkleRoot, msg.sender, block.timestamp, metadataURI);
    }

    function getProof(bytes32 merkleRoot)
        external
        view
        returns (address submitter, uint256 timestamp, string memory metadataURI)
    {
        Proof memory p = proofs[merkleRoot];
        require(p.timestamp != 0, "Proof not found");
        return (p.submitter, p.timestamp, p.metadataURI);
    }
}
