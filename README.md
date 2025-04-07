# Peaq SDK (Python)

A robust Python SDK for seamless interaction with the peaq blockchain, supporting both EVM and Substrate-based operations. It provides tools to manage Decentralized Identifiers (DIDs), interact with on-chain storage, and perform blockchain transactions with or without local signing capabilities.

## Features
- DID creation and management
- On-chain storage utilization
- RBAC capabilities (coming soon)
- Universal Machine Time (coming soon)

## Installation
Install via pip:
```
pip install peaq-sdk
```

## Quick Start
Initialize the SDK for interaction:
### EVM Connection
```python
from peaq_sdk import Sdk
from peaq_sdk.types import ChainType

# Without signing capabilities (read-only and transaction creation)
sdk = Sdk.create_instance(
    base_url="https://peaq.api.onfinality.io/public",
    chain_type=ChainType.EVM,
)

# With signing capabilities
sdk = Sdk.create_instance(
    base_url="https://peaq.api.onfinality.io/public",
    chain_type=ChainType.EVM,
    seed=my_private_key_or_mnemonic,
)
```
### Substrate Connection
```python
from peaq_sdk import Sdk
from peaq_sdk.types import ChainType

# Without signing capabilities (read-only and transaction creation)
sdk = Sdk.create_instance(
    base_url="wss://peaq.api.onfinality.io/public-ws",
    chain_type=ChainType.Substrate,
)

# With signing capabilities
sdk = Sdk.create_instance(
    base_url="wss://peaq.api.onfinality.io/public-ws",
    chain_type=ChainType.Substrate,
    seed=my_private_key_or_mnemonic,
)
```

## Decentralized Identifiers (DID)
### Create a DID
```python
from peaq_sdk.types import CustomDocumentFields, Verification

custom_fields = CustomDocumentFields(
    verifications=[Verification(type='EcdsaSecp256k1RecoveryMethod2020')]
)

result = sdk.did.create(name="myDid", custom_document_fields=custom_fields)
```
### Read a DID
```python
result = sdk.did.read(name="myDid")
```
### Update a DID
```python
from peaq_sdk.types import CustomDocumentFields, Verification

custom_fields = CustomDocumentFields(
    verifications=[Verification(type='EcdsaSecp256k1RecoveryMethod2020')]
)
result = sdk.did.update(name="myDid", custom_document_fields=custom_fields)
```
### Delete a DID
```python
result = sdk.did.delete(name="myDid")
```

## On-chain Storage
### Add Item
```python
result = sdk.storage.add_item(item_type='key', item='value')
```
### Read Item
```python
result = sdk.storage.get_item(item_type='key')
```
### Update Item
```python
sdk.storage.update_item(item_type='key', item='new_value')
```
### Remove Item
```python
sdk.storage.remove_item(item_type='key')
```

For a more detailed explanation of the functionality please checkout our Python Sdk Reference.

## Security and Private Keys
- Private keys are never **stored**, **sent**, or **logged** by the SDK.
- Signing occurs locally only.
- Private keys are used solely to generate an Account or Keypair, after which they are discarded from memory.
- Ensure your local environment securely manages and protects private keys. **Never share your private keys.**


## Development
### Virtual Environment
```
python3 -m venv working_env
source working_env/bin/activate
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

## Testing
Checkout the `README.md` file in `/tests` directory for more information.