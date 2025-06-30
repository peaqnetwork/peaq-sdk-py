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
Each test suite validates the SDK's ability to:
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

## Test Suite Documentation

This test suite supports comprehensive testing across multiple blockchain networks and RPC providers.

## Environment Variables

### Test Modes
Set these environment variables to control test execution:

- `QUICK_TEST`: Set to `"true"` to run tests against only one provider (much faster)
- `TEST_PROVIDER`: Which provider to use in quick test mode (default: `"public"`)
- `TEST_CHAIN`: Which chain to test in quick test mode (default: `"agung"`)

### Available Test Modes
- **Full Mode** (default): Test all available providers across both chains
- **Quick Mode** (`QUICK_TEST=true`): Test single provider/chain combination

### Available Providers
- `public` - Public RPC endpoints
- `private` - OnFinality private endpoints
- `quicknode` - QuickNode public endpoints (Peaq only)
- `quicknode_private` - QuickNode private endpoints (Peaq only)
- `onfinality` - OnFinality public endpoints

### Available Chains
- `agung` - Agung testnet
- `peaq` - Peaq mainnet

## Required Environment Variables

### Agung URLs
```bash
# Public endpoints
RPC_AGNG_PUBLIC_BASE_URL=
WSS_AGNG_PUBLIC_BASE_URL=

# OnFinality endpoints
RPC_AGNG_ONFIN_PRIVATE_BASE_URL=
WSS_AGNG_ONFIN_PRIVATE_BASE_URL=
RPC_AGNG_ONFIN_PUBLIC_BASE_URL=
WSS_AGNG_ONFIN_PUBLIC_BASE_URL=
```

### Peaq URLs
```bash
# Public endpoints
RPC_PEAQ_PUBLIC_BASE_URL=
WSS_PEAQ_PUBLIC_BASE_URL=

# OnFinality endpoints
RPC_PEAQ_ONFIN_PRIVATE_BASE_URL=
WSS_PEAQ_ONFIN_PRIVATE_BASE_URL=
RPC_PEAQ_ONFIN_PUBLIC_BASE_URL=
WSS_PEAQ_ONFIN_PUBLIC_BASE_URL=

# QuickNode endpoints
RPC_PEAQ_QN_PUBLIC_BASE_URL=
WSS_PEAQ_QN_PUBLIC_BASE_URL=
RPC_PEAQ_QN_PRIVATE_BASE_URL=
WSS_PEAQ_QN_PRIVATE_BASE_URL=
```

### Authentication
```bash
# Substrate credentials
SUBSTRATE_ADDRESS=
SUBSTRATE_SEED=

# EVM credentials
EVM_ADDRESS=
EVM_PRIVATE=
```

## Usage Examples

### Full Test Suite (All Providers)
```bash
# Run all tests across all configured providers
pytest tests/

# Run specific module across all providers
pytest tests/rbac/
```

### Quick Test Mode
```bash
# Quick test with default settings (agung + public)
QUICK_TEST=true pytest tests/

# Quick test with specific provider
QUICK_TEST=true TEST_PROVIDER=quicknode TEST_CHAIN=peaq pytest tests/

# Quick test with OnFinality private
QUICK_TEST=true TEST_PROVIDER=private pytest tests/
```



### Advanced Examples
```bash
# Test only RBAC functionality with QuickNode
QUICK_TEST=true TEST_PROVIDER=quicknode TEST_CHAIN=peaq pytest tests/rbac/

# Test with OnFinality public endpoints on Peaq
QUICK_TEST=true TEST_PROVIDER=onfinality TEST_CHAIN=peaq pytest tests/

# Test with QuickNode private endpoints on Peaq
QUICK_TEST=true TEST_PROVIDER=quicknode_private TEST_CHAIN=peaq pytest tests/

# Test DID functionality with OnFinality on Agung
QUICK_TEST=true TEST_PROVIDER=onfinality TEST_CHAIN=agung pytest tests/did/

# Verbose output for debugging
QUICK_TEST=true pytest tests/ -v -s
```

## Test Structure

The test suite is organized into modules:

- `tests/rbac/` - Role-Based Access Control tests
- `tests/did/` - Decentralized Identity tests  
- `tests/machine_station/` - Machine Station tests
- `tests/storage/` - Storage tests
- `tests/main/` - Main SDK tests

## Provider Availability

| Provider | Agung | Peaq |
|----------|-------|------|
| public | ✅ | ✅ |
| private | ✅ | ✅ |
| quicknode | ❌ | ✅ |
| quicknode_private | ❌ | ✅ |
| onfinality | ✅ | ✅ |
| onfinality_private | ✅ | ✅ |

## Test Mode Summary

| Test Mode | Description | Speed | Coverage |
|-----------|-------------|-------|----------|
| **Full** | All providers, both chains | Slowest | Complete |
| **Quick** | Single provider/chain | Fastest | Targeted |

## Tips

1. **Quick Testing**: Use `QUICK_TEST=true` during development for faster iteration
2. **OnFinality Testing**: Use `TEST_PROVIDER=onfinality` to specifically test OnFinality reliability on Peaq
3. **Provider Testing**: Test specific providers with `TEST_PROVIDER` 
4. **Missing URLs**: Tests will be automatically skipped if URLs are not configured
5. **Error Handling**: The test suite includes automatic retry logic for network issues
6. **Parallel Testing**: Consider using `pytest-xdist` for parallel execution: `pip install pytest-xdist && pytest -n auto`

## Test Naming Convention

Tests now use descriptive names that clearly show the chain and provider:

- `agung-public-rpc` - Agung with public RPC endpoints
- `agung-onfinality-private` - Agung with OnFinality private endpoints  
- `agung-onfinality-public` - Agung with OnFinality public endpoints
- `peaq-public-rpc` - Peaq with public RPC endpoints
- `peaq-onfinality-private` - Peaq with OnFinality private endpoints
- `peaq-onfinality-public` - Peaq with OnFinality public endpoints
- `peaq-quicknode-public` - Peaq with QuickNode public endpoints
- `peaq-quicknode-private` - Peaq with QuickNode private endpoints

## Debugging

For debugging test failures:

```bash
# Run with verbose output to see descriptive test names
QUICK_TEST=true pytest tests/rbac/ -v -s

# Debug OnFinality-specific issues
QUICK_TEST=true TEST_PROVIDER=onfinality TEST_CHAIN=peaq pytest tests/rbac/ -v -s

# Run single test with output (you'll see the provider name clearly)
QUICK_TEST=true pytest tests/rbac/test_rbac.py::TestRBACCreateOperations::test_substrate_create_role -v -s

# Stop on first failure
QUICK_TEST=true pytest tests/ -x

# Debug specific QuickNode endpoint
QUICK_TEST=true TEST_PROVIDER=quicknode TEST_CHAIN=peaq pytest tests/rbac/ -v -s -x

# See all test names before running
pytest tests/rbac/ --collect-only -q
```

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