# Hardhat Va Ganache Setup

Tai lieu nay ghi lai cach compile va chay smart contract local cho MVP blockchain.

## 1. Cai dependency

```bash
npm install
```

## 2. Compile contract

```bash
npm run compile
```

Contract chinh:

```text
contracts/AgriPriceRegistry.sol
```

## 3. Chay local blockchain

Dung Hardhat:

```bash
npm run chain:hardhat
```

Hoac dung Ganache:

```bash
npm run chain:ganache
```

## 4. Deploy len local node

Mo terminal 1:

```bash
npm run chain:hardhat
```

Mo terminal 2:

```bash
npm run deploy:local
```

Ket qua deploy duoc ghi vao:

```text
deployments/localhost.json
```

## 5. Ghi chu

- Hardhat local chain thuong reset khi tat node.
- Du lieu off-chain sau nay nen luu SQLite/local database.
- Blockchain chi luu `recordId`, `dataHash`, `source`, dia chi nguoi ghi va lifecycle event hash.

## 6. Trang thai hien tai

Da compile va deploy local thanh cong:

```text
RPC URL:          http://127.0.0.1:8545
Chain ID:         31337
Contract:         AgriPriceRegistry
Contract address: 0x5FbDB2315678afecb367f032d93F642f64180aa3
Deployment file:  deployments/localhost.json
```

Kiem tra nhanh:

```bash
npm run compile
```

Neu node Hardhat bi tat, can chay lai:

```bash
npm run chain:hardhat
npm run deploy:local
```

Buoc tiep theo la thay `LocalProofLedger` trong backend bang service goi smart contract that qua RPC `http://127.0.0.1:8545`.
