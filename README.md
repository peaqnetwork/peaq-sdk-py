# Peaq SDK (Python)

A robust Python SDK for seamless interaction with the peaq blockchain, supporting both EVM and Substrate-based operations. It provides tools to manage Decentralized Identifiers (DIDs), interact with on-chain storage, and perform blockchain transactions with or without local signing capabilities.

## Features
- DID creation and management
- On-chain storage utilization
- RBAC (Role-Based Access Control) capabilities
- Token transfer functionality
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
    chain_type=ChainType.SUBSTRATE,
)

# With signing capabilities
sdk = Sdk.create_instance(
    base_url="wss://peaq.api.onfinality.io/public-ws",
    chain_type=ChainType.SUBSTRATE,
    seed=my_private_key_or_mnemonic,
)
```

## SDK Operations
All return objects are either:

**Unsent Transaction/Call (seed not in create_instance)**
- Message indicating what tx or call was built.
- Transaction/Call to send:
    - For EVM instance it will return an EVM Transaction the user can send themselves.
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
        ],
    signature=Signature(type='EcdsaSecp256k1RecoveryMethod2020', issuer='0x9Eeab1aCcb1A701aEfAB00F3b8a275a39646641E', hash='0xGENERATED_HASH'),
    services=[
        Service(id='#cid', type='peaqStorage', data='CID_VALUE')
        ]
    )

receipt = sdk.did.create(name="myDid", custom_document_fields=custom_fields)
```
#### Read a DID
```python
# Works on both EVM and Substrate
result = sdk.did.read(name="myDid")
```
#### Update a DID
```python
from peaq_sdk.types import CustomDocumentFields, Verification, Service, Signature

custom_fields = CustomDocumentFields(
    verifications=[
        Verification(type='EcdsaSecp256k1RecoveryMethod2020')
        ],
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

### Role-Based Access Control (RBAC)
#### Create a Role
```python
# Create a role with auto-generated ID
result = sdk.rbac.create_role(role_name="Admin")

# Create a role with custom ID (must be 32 characters)
custom_role_id = "admin_role_123456789012345678901"
result = sdk.rbac.create_role(role_name="Admin", role_id=custom_role_id)
```

#### Fetch a Role
```python
# Read a role by owner address and role ID
owner_address = "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"  # Substrate address
role_id = "admin_role_123456789012345678901"
result = sdk.rbac.fetch_role(owner=owner_address, role_id=role_id)
```

#### Assign Role to User
```python
role_id = "admin_role_123456789012345678901"
user_id = "user_id_12345678901234567890123"  # 32-character user ID
result = sdk.rbac.assign_role_to_user(role_id=role_id, user_id=user_id)
```

### Token Transfer
#### Native Token Transfer
```python
# Transfer native tokens to another address
recipient = "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"  # Can be Substrate or EVM address
amount = 1.5  # Human-readable amount (e.g., 1.5 PEAQ)
result = sdk.transfer.native(to=recipient, amount=amount)
```

#### ERC-20 Token Transfer
```python
# Transfer ERC-20 tokens (EVM only)
erc20_contract = "0x1234567890123456789012345678901234567890"
recipient = "0x9876543210987654321098765432109876543210"
amount = 100.0  # Amount in human-readable format
token_decimals = 18  # Token decimals (default: 18)

result = sdk.transfer.erc20(
    erc_20_address=erc20_contract,
    recipient_address=recipient,
    amount=amount,
    token_decimals=token_decimals
)
```

#### ERC-721 (NFT) Transfer
```python
# Transfer NFT tokens (EVM only)
nft_contract = "0x1234567890123456789012345678901234567890"
recipient = "0x9876543210987654321098765432109876543210"
token_id = 42  # NFT token ID

result = sdk.transfer.erc721(
    erc_721_address=nft_contract,
    recipient_address=recipient,
    token_id=token_id
)
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
### Remove virtual env
```
rm -rf working_env
```

## Testing
Checkout the `README.md` file in `/tests` directory for more information.