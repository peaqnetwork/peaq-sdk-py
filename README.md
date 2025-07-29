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
pip install ./packages/sdk
# or when published:
pip install peaq-sdk
```

### MSF SDK (`packages/msf/`)
Specialized SDK for Machine Station Factory operations with a flattened API:

- **Flattened API**: Direct access to machine station methods
- **Machine Management**: Deploy and manage machine smart accounts
- **Transaction Execution**: Execute transactions through machine stations
- **EIP-712 Signatures**: Generate off-chain signatures

```bash
pip install ./packages/msf
# or when published:
pip install peaq-msf
```

## Quick Start

### Core SDK Usage
```python
from peaq_sdk import Main
from peaq_sdk.types import ChainType, TransactionOptions, ConfirmationMode
from eth_account import Account

# Create account
account = Account.from_key("your_private_key")

# Initialize SDK
sdk = Main.create_instance(
    base_url="https://peaq-rpc-url",
    chain_type=ChainType.EVM,
    auth=account
)

# Use nested API
result = sdk.storage.add_item(
    {"item_type": "test", "item": "data"},
    tx_options=TransactionOptions(mode=ConfirmationMode.FAST)
)

# Machine station operations (nested)
result = sdk.machine_station.deploy_machine_smart_account("0x1234...")
```

### MSF SDK Usage
```python
from peaq_msf import Main
from peaq_msf import ChainType, TransactionOptions, ConfirmationMode
from eth_account import Account

# Create account
account = Account.from_key("your_private_key")

# Initialize MSF SDK
msf = Main.create_instance(
    base_url="https://peaq-rpc-url",
    chain_type=ChainType.EVM,
    auth=account
)

# Use flattened API - direct access to machine station methods
result = msf.deploy_machine_smart_account("0x1234...")  # No nesting!
signature = msf.admin_sign_machine_transaction(...)     # Direct access
```


### Installing for Development

Install core SDK in development mode:
```bash
pip install -e ./packages/sdk
```
#### Read a DID
```python
# Works on both EVM and Substrate
result = sdk.did.read(name="myDid")
```
#### Update a DID
```python
from peaq_sdk.types import CustomDocumentFields, Verification, Service, Signature

Install MSF SDK in development mode (requires core SDK):
```bash
pip install -e ./packages/sdk  # Install core SDK first
pip install -e ./packages/msf  # Then install MSF SDK
```

### On-chain Storage
#### Add Item
```python
result = sdk.storage.add_item(item_type='key', item='value')
```
#### Read Item
```python
result = sdk.storage.get_item(item_type='key')
```
#### Update Item
```python
sdk.storage.update_item(item_type='key', item='new_value')
```
#### Remove Item
```python
sdk.storage.remove_item(item_type='key')
```


# Create a role with custom ID (must be 32 characters)
custom_role_id = "admin_role_123456789012345678901"
result = sdk.rbac.create_role(role_name="Admin", role_id=custom_role_id)
```

## 🔧 Package Architecture

```
peaq-sdk-py/
├── packages/
│   ├── sdk/                 # Core SDK
│   │   ├── src/
│   │   ├── pyproject.toml
│   │   └── README.md
│   └── msf/                 # MSF SDK
│       ├── src/
│       ├── pyproject.toml
│       └── README.md
├── pyproject.toml          # Monorepo config
└── README.md
```

## API Documentation

### Transaction Options
Both SDKs support the same transaction configuration:

```python
from peaq_sdk.types import TransactionOptions, ConfirmationMode

tx_options = TransactionOptions(
    mode=ConfirmationMode.FAST,      # FAST | CUSTOM | FINAL
    gas_limit=100_000,               # Optional gas limit
    max_fee_per_gas=2000,           # Optional EIP-1559 fee
    max_priority_fee_per_gas=1000,  # Optional priority fee
    confirmations=3                  # For CUSTOM mode
)
```

### Status Callbacks
Both SDKs provide real-time transaction status updates:

```python
def status_callback(status_data):
    print(f"Status: {status_data['status']}")          # BROADCAST | IN_BLOCK | FINALIZED
    print(f"Hash: {status_data['hash']}")              # Transaction hash
    print(f"Confirmations: {status_data['total_confirmations']}")

# Use with any transaction
result = sdk.storage.add_item(
    data, 
    status_callback=status_callback,
    tx_options=tx_options
)
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes in the appropriate package (`packages/sdk/` or `packages/msf/`)
4. Test your changes (`pytest packages/*/tests/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.




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