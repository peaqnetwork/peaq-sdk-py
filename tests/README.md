# Testing the Implementation
This project uses `pytest` for all automated tests. The tests cover functionality across EVM and Substrate chains on the `peaq` and `agung` networks, 
including public/private endpoints using both HTTP (RPC) and WebSocket (WSS) providers.

## Testing Framework Structure
```
tests/
├── conftest.py          # Global fixtures (e.g., network config, SDK setup)
├── main/
│   └── test_main.py     # Tests for core Main SDK functionality
├── storage/
│   ├── conftest.py      # Storage-specific fixtures
│   └── test_storage.py  # Tests for storage read/write/remove operations
└── did/
    ├── conftest.py      # DID-specific fixtures and document configurations
    └── test_did.py      # Full DID lifecycle tests (create, read, update, remove)
```

## What the Tests Cover
Each test suite validates the SDK’s ability to:
- Create and manage DIDs across EVM and Substrate chains.
- Read/write to on-chain storage using authenticated transactions.
- Run transactions on public, private, and QuickNode-style endpoints.
- Automatically retry transactions using tip incrementing (Substrate) and gas bumping (EVM) if low-priority errors are returned. (see `peaq_sdk/base.py` for retry logic)
- Assert that SDK behavior is correct under various connection conditions and network types.

## .env File Setup
To run tests, create a `.env` file in the root directory with the following variables:
```
# Agung Network URLs
RPC_AGNG_PUBLIC_BASE_URL=
WSS_AGNG_PUBLIC_BASE_URL=
RPC_AGNG_ONFIN_PRIVATE_BASE_URL=
WSS_AGNG_ONFIN_PRIVATE_BASE_URL=

# Peaq Network URLs
RPC_PEAQ_PUBLIC_BASE_URL=
WSS_PEAQ_PUBLIC_BASE_URL=
RPC_PEAQ_ONFIN_PRIVATE_BASE_URL=
WSS_PEAQ_ONFIN_PUBLIC_BASE_URL=
RPC_PEAQ_QN_PUBLIC_BASE_URL=
WSS_PEAQ_QN_PUBLIC_BASE_URL=

# Keys and Accounts (to execute txs - make sure they are funded)
SUBSTRATE_ADDRESS=     # SS58-format account address (used for Substrate DID & storage ops)
SUBSTRATE_SEED=        # 12- or 24-word mnemonic for signing on Substrate
EVM_ADDRESS=           # Hex-format 0x-prefixed address (used for EVM DID & storage ops)
EVM_PRIVATE=           # 0x-prefixed private key for EVM signer
```
These are loaded into `config()` via `dotenv` and passed into each test dynamically. These urls can be found on the peaq documentation.


## 🚀 How to Run Tests
### 🔍 Preview number of tests that will run:
```
pytest --collect-only -q
```
### 🖨️ See print/logging output:
```
pytest -s
```
### 📝 Verbose logging (basic):
```
pytest -v
```
### 🧠 Very verbose with test result summary (recommended):
```
pytest -vv -r a
```
### 🧾 Log output to file:
```
pytest -vv -r a > pytest.log
```
### 🎯 Run only DID tests:
```
pytest tests/did -vv
```
### ⛔ Stop tests on first failure (recommended):
```
pytest -vv -r a -x -s
```