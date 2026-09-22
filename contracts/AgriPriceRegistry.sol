// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract AgriPriceRegistry {
    struct PriceRecordProof {
        string recordId;
        bytes32 dataHash;
        string source;
        address createdBy;
        uint256 createdAt;
        bool exists;
    }

    struct LifecycleEvent {
        string recordId;
        string eventType;
        bytes32 eventHash;
        string metadataUri;
        address createdBy;
        uint256 createdAt;
    }

    mapping(string => PriceRecordProof) private records;
    mapping(string => LifecycleEvent[]) private lifecycleEvents;

    event PriceRecordAnchored(
        string indexed recordId,
        bytes32 indexed dataHash,
        string source,
        address indexed createdBy,
        uint256 createdAt
    );

    event ProductLifecycleEventAnchored(
        string indexed recordId,
        string eventType,
        bytes32 indexed eventHash,
        string metadataUri,
        address indexed createdBy,
        uint256 createdAt
    );

    error EmptyRecordId();
    error EmptyHash();
    error RecordAlreadyAnchored(string recordId);
    error RecordNotAnchored(string recordId);

    function anchorPriceRecord(
        string calldata recordId,
        bytes32 dataHash,
        string calldata source
    ) external {
        if (bytes(recordId).length == 0) revert EmptyRecordId();
        if (dataHash == bytes32(0)) revert EmptyHash();
        if (records[recordId].exists) revert RecordAlreadyAnchored(recordId);

        records[recordId] = PriceRecordProof({
            recordId: recordId,
            dataHash: dataHash,
            source: source,
            createdBy: msg.sender,
            createdAt: block.timestamp,
            exists: true
        });

        emit PriceRecordAnchored(recordId, dataHash, source, msg.sender, block.timestamp);
    }

    function getPriceRecordProof(
        string calldata recordId
    )
        external
        view
        returns (
            bytes32 dataHash,
            string memory source,
            address createdBy,
            uint256 createdAt,
            bool exists
        )
    {
        PriceRecordProof storage proof = records[recordId];
        return (proof.dataHash, proof.source, proof.createdBy, proof.createdAt, proof.exists);
    }

    function verifyPriceRecord(
        string calldata recordId,
        bytes32 dataHash
    ) external view returns (bool) {
        PriceRecordProof storage proof = records[recordId];
        return proof.exists && proof.dataHash == dataHash;
    }

    function addLifecycleEvent(
        string calldata recordId,
        string calldata eventType,
        bytes32 eventHash,
        string calldata metadataUri
    ) external {
        if (!records[recordId].exists) revert RecordNotAnchored(recordId);
        if (eventHash == bytes32(0)) revert EmptyHash();

        lifecycleEvents[recordId].push(
            LifecycleEvent({
                recordId: recordId,
                eventType: eventType,
                eventHash: eventHash,
                metadataUri: metadataUri,
                createdBy: msg.sender,
                createdAt: block.timestamp
            })
        );

        emit ProductLifecycleEventAnchored(
            recordId,
            eventType,
            eventHash,
            metadataUri,
            msg.sender,
            block.timestamp
        );
    }

    function getLifecycleEventCount(string calldata recordId) external view returns (uint256) {
        return lifecycleEvents[recordId].length;
    }

    function getLifecycleEvent(
        string calldata recordId,
        uint256 index
    )
        external
        view
        returns (
            string memory eventType,
            bytes32 eventHash,
            string memory metadataUri,
            address createdBy,
            uint256 createdAt
        )
    {
        LifecycleEvent storage item = lifecycleEvents[recordId][index];
        return (item.eventType, item.eventHash, item.metadataUri, item.createdBy, item.createdAt);
    }
}

