# Peaq Network SDK Monorepo

This repository contains the Python SDKs for interacting with the peaq Network blockchain.

## Packages

### Core SDK (`packages/sdk/`)
The main SDK providing comprehensive blockchain interaction capabilities:

- **DID Operations**: Create, update, and manage decentralized identifiers
- **Storage**: On-chain storage management
- **RBAC**: Role-based access control operations
- **Transfer**: Native and token transfers

```bash
pip install peaq-sdk
```

### MSF SDK (`packages/msf/`)
Specialized SDK for Machine Station Factory operations with a flattened API:

- **Flattened API**: Direct access to machine station methods
- **Transaction Execution**: Execute transactions through machine stations
- **EIP-712 Signatures**: Generate off-chain signatures

```bash
pip install peaq-msf
```

## Quick Start

### Core SDK Usage
```python
from peaq_sdk import Sdk
from peaq_sdk.types import ChainType
from eth_account import Account


# Create account
account = Account.from_key("your_private_key")

# Initialize SDK
sdk = await Sdk.create_instance({
    'base_url': HTTPS_PEAQ_URL,
    'chain_type': ChainType.EVM,
    'auth': account
})

result = await sdk.storage.add_item(
    {
        "item_type": "test",
        "item": "data"
    }
)

print(result.tx_hash)
print(await result.receipt)
```

### MSF SDK Usage
```python
from peaq_msf import MSF
from eth_account import Account

# Create accounts
admin = Account.from_key(ADMIN_KEY)
manager = Account.from_key(MANAGER_KEY)

# Initialize MSF SDK
msf_sdk = await MSF.create_instance({
    "base_url": HTTPS_PEAQ_URL,
    "machine_station_address": MACHINE_STATION_ADDRESS,
    "station_admin": admin,
    "station_manager": manager,
})

# Use flattened API - direct access to machine station methods
result = msf_sdk.deploy_machine_smart_account("0x1234...")
signature = msf_sdk.admin_sign_machine_transaction(...)
```


## Transaction Configurations

### Transaction Options
Both SDKs support the same transaction configuration:

```python
from peaq_sdk.types import ConfirmationMode

result = await sdk.storage.add_item(
    {
        ...,
    }
    None,
    { 
        'mode': ConfirmationMode.FAST,      # FAST | CUSTOM | FINAL
        # 'confirmations': 5,                 # Required for CUSTOM mode
        'gas_limit': 100_000,               # Optional gas limit
        'max_fee_per_gas': 2000,            # Optional EIP-1559 fee
        'max_priority_fee_per_gas': 1000    # Optional priority fee
    }
)
# Gas Fees optimized for AGUNG
```

**Confirmation Modes:**
- **FAST**: Resolves after first block inclusion
- **CUSTOM**: Waits for user-defined confirmations (requires `confirmations` parameter)
- **FINAL**: Waits for Polkadot-style GRANDPA finality

### Status Callbacks
Both SDKs provide real-time transaction status updates:

```python
def status_callback(status_data):
    print(f"Status: {status_data['status']}")          # BROADCAST | IN_BLOCK | FINALIZED
    print(f"Hash: {status_data['hash']}")              # Transaction hash with 0x prefix
    print(f"Confirmations: {status_data['total_confirmations']}")
    print(f"Mode: {status_data['confirmation_mode']}") # FAST | CUSTOM | FINAL

    print(json.dumps(status_data, indent=2)) # pretty print all data

# Use with any transaction
result = await sdk.storage.add_item(
    {
        ...,
    }
    status_callback
)
```




## Development
### Virtual Environment
```
python3 -m venv working_env_msf
source working_env_msf/bin/activate
```
```
python3 -m venv working_env_sdk
source working_env_sdk/bin/activate
```
### Build Package
```
pip install -r requirements.txt
python -m build
```
### Exit Virtual Environment
```
deactivate
```
### Remove virtual env
```
rm -rf working_env
```