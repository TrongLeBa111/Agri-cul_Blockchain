const assert = require("node:assert/strict");
const { ethers } = require("hardhat");

async function deployRegistry() {
  const Registry = await ethers.getContractFactory("AgriPriceRegistry");
  const registry = await Registry.deploy();
  await registry.waitForDeployment();
  return registry;
}

async function expectCustomError(action, contract, errorName, expectedArg) {
  try {
    await action();
  } catch (error) {
    const parsed = contract.interface.parseError(error.data ?? error.error?.data ?? "0x");
    assert.equal(parsed?.name, errorName);
    if (expectedArg !== undefined) {
      assert.equal(parsed.args[0], expectedArg);
    }
    return;
  }

  assert.fail(`Expected custom error ${errorName}`);
}

describe("AgriPriceRegistry", function () {
  const recordId = "demo_wb_rice_2026_06_01_global";
  const dataHash = ethers.id("rice-global-2026-06-01");
  const wrongHash = ethers.id("tampered-rice-global-2026-06-01");
  const source = "WORLD_BANK";

  it("anchors a price record successfully", async function () {
    const [owner] = await ethers.getSigners();
    const registry = await deployRegistry();

    const tx = await registry.anchorPriceRecord(recordId, dataHash, source);
    const receipt = await tx.wait();

    const event = receipt.logs
      .map((log) => registry.interface.parseLog(log))
      .find((log) => log?.name === "PriceRecordAnchored");

    assert.equal(event.args.recordId.hash, ethers.id(recordId));
    assert.equal(event.args.dataHash, dataHash);
    assert.equal(event.args.source, source);
    assert.equal(event.args.createdBy, owner.address);
  });

  it("rejects duplicate anchors with RecordAlreadyAnchored", async function () {
    const registry = await deployRegistry();
    await registry.anchorPriceRecord(recordId, dataHash, source);

    await expectCustomError(
      () => registry.anchorPriceRecord(recordId, dataHash, source),
      registry,
      "RecordAlreadyAnchored",
      recordId
    );
  });

  it("rejects an empty record id with EmptyRecordId", async function () {
    const registry = await deployRegistry();

    await expectCustomError(
      () => registry.anchorPriceRecord("", dataHash, source),
      registry,
      "EmptyRecordId"
    );
  });

  it("rejects an empty hash with EmptyHash", async function () {
    const registry = await deployRegistry();

    await expectCustomError(
      () => registry.anchorPriceRecord(recordId, ethers.ZeroHash, source),
      registry,
      "EmptyHash"
    );
  });

  it("returns the stored price record proof", async function () {
    const [owner] = await ethers.getSigners();
    const registry = await deployRegistry();
    const tx = await registry.anchorPriceRecord(recordId, dataHash, source);
    const receipt = await tx.wait();
    const block = await ethers.provider.getBlock(receipt.blockNumber);

    const proof = await registry.getPriceRecordProof(recordId);

    assert.equal(proof.dataHash, dataHash);
    assert.equal(proof.source, source);
    assert.equal(proof.createdBy, owner.address);
    assert.equal(proof.createdAt, BigInt(block.timestamp));
    assert.equal(proof.exists, true);
  });

  it("verifies true when the hash matches", async function () {
    const registry = await deployRegistry();
    await registry.anchorPriceRecord(recordId, dataHash, source);

    assert.equal(await registry.verifyPriceRecord(recordId, dataHash), true);
  });

  it("verifies false when the hash does not match", async function () {
    const registry = await deployRegistry();
    await registry.anchorPriceRecord(recordId, dataHash, source);

    assert.equal(await registry.verifyPriceRecord(recordId, wrongHash), false);
  });

  it("adds a lifecycle event after the record is anchored", async function () {
    const [owner] = await ethers.getSigners();
    const registry = await deployRegistry();
    const eventHash = ethers.id("ingested-event");

    await registry.anchorPriceRecord(recordId, dataHash, source);
    const tx = await registry.addLifecycleEvent(recordId, "INGESTED", eventHash, "local://seed.csv");
    const receipt = await tx.wait();

    const event = receipt.logs
      .map((log) => registry.interface.parseLog(log))
      .find((log) => log?.name === "ProductLifecycleEventAnchored");

    assert.equal(await registry.getLifecycleEventCount(recordId), 1n);
    assert.equal(event.args.recordId.hash, ethers.id(recordId));
    assert.equal(event.args.eventType, "INGESTED");
    assert.equal(event.args.eventHash, eventHash);
    assert.equal(event.args.metadataUri, "local://seed.csv");
    assert.equal(event.args.createdBy, owner.address);
  });

  it("reverts lifecycle events before anchor with RecordNotAnchored", async function () {
    const registry = await deployRegistry();

    await expectCustomError(
      () => registry.addLifecycleEvent(recordId, "INGESTED", ethers.id("ingested-event"), "local://seed.csv"),
      registry,
      "RecordNotAnchored",
      recordId
    );
  });

  it("returns the stored lifecycle event", async function () {
    const [owner] = await ethers.getSigners();
    const registry = await deployRegistry();
    const eventHash = ethers.id("quality-check-event");

    await registry.anchorPriceRecord(recordId, dataHash, source);
    const tx = await registry.addLifecycleEvent(recordId, "QUALITY_CHECKED", eventHash, "ipfs://quality-report");
    const receipt = await tx.wait();
    const block = await ethers.provider.getBlock(receipt.blockNumber);

    const lifecycleEvent = await registry.getLifecycleEvent(recordId, 0);

    assert.equal(lifecycleEvent.eventType, "QUALITY_CHECKED");
    assert.equal(lifecycleEvent.eventHash, eventHash);
    assert.equal(lifecycleEvent.metadataUri, "ipfs://quality-report");
    assert.equal(lifecycleEvent.createdBy, owner.address);
    assert.equal(lifecycleEvent.createdAt, BigInt(block.timestamp));
  });
});
