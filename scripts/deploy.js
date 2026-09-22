const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const AgriPriceRegistry = await hre.ethers.getContractFactory("AgriPriceRegistry");
  const registry = await AgriPriceRegistry.deploy();
  await registry.waitForDeployment();

  const address = await registry.getAddress();
  const deployment = {
    contract: "AgriPriceRegistry",
    address,
    network: hre.network.name,
    chainId: hre.network.config.chainId,
    deployedAt: new Date().toISOString()
  };

  const outputDir = path.join(__dirname, "..", "deployments");
  fs.mkdirSync(outputDir, { recursive: true });
  fs.writeFileSync(
    path.join(outputDir, `${hre.network.name}.json`),
    JSON.stringify(deployment, null, 2)
  );

  console.log(`AgriPriceRegistry deployed to ${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

