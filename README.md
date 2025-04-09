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

## SDK Operations
All return objects are either:

**Unsent Transaction/Call (seed not in create_instance)**
- Message indicating what tx or call was built.
- Transaction/Call to send:
    - For EVM instance it will return an EVM Transactions the user can send themselves.
    - The Substrate instance returns a Call object that must be sent using the `substrate-interface` [package](https://pypi.org/project/substrate-interface/).
    - You can see how these calls are sent in the sdk under the `_send_evm_tx()` and `_send_substrate_tx()` functions in the `peaq_sdk/base.py` file.

**Sent Transaction (seed in create_instance)**
- Message indicating the operation performed.
- Receipt of the EVM/Substrate transaction.

Read operations are able to perform without a seed/private key being set.
They query the item and return it to the user.

Below are quick examples how to use the sdk assuming the seed is set. For a more detailed
tutorial please checkout our Python SDK Reference.

### Decentralized Identifiers (DID)
#### Create a DID
```python
# example that uses all of the custom fields
from peaq_sdk.types import CustomDocumentFields, Verification, Service, Signature

custom_fields = CustomDocumentFields(
    verifications=[
        Verification(type='EcdsaSecp256k1RecoveryMethod2020')
        ]
    signature=Signature(type='EcdsaSecp256k1RecoveryMethod2020', issuer='0x9Eeab1aCcb1A701aEfAB00F3b8a275a39646641E', hash='0xGENERATED_HASH'),
    services=[
        Service(id='#cid', type='peaqStorage', data='CID_VALUE')
        ]
    )

receipt = sdk.did.create(name="myDid", custom_document_fields=custom_fields)
```
#### Read a DID
```python
# EVM
result = sdk.did.read(name="myDid", wss_base_url="wss://peaq.api.onfinality.io/public-ws")

# Substrate
result = sdk.did.read(name="myDid")
```
#### Update a DID
```python
from peaq_sdk.types import CustomDocumentFields, Verification, Service, Signature

custom_fields = CustomDocumentFields(
    verifications=[
        Verification(type='EcdsaSecp256k1RecoveryMethod2020')
        ]
    signature=Signature(type='EcdsaSecp256k1RecoveryMethod2020', issuer='0x9Eeab1aCcb1A701aEfAB00F3b8a275a39646641C', hash='0xGENERATED_HASH'),
    services=[
        Service(id='#cid', type='peaqStorage', data='CID_VALUE')
        ]
    )

result = sdk.did.update(name="myDid", custom_document_fields=custom_fields)
```
#### Delete a DID
```python
result = sdk.did.delete(name="myDid")
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

## Security and Private Keys
- Private keys are never **stored**, **sent**, or **logged** by the SDK.
    - Used solely to generate an Account or Keypair.
- Signing occurs locally only.
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