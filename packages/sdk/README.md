# Peaq SDK

Peaq Network SDK for comprehensive blockchain interactions on EVM and Substrate chains.

## Installation

```bash
pip install peaq-sdk
```

## Usage

```python
from peaq_sdk import Sdk
from peaq_sdk.types import ChainType
from eth_account import Account

# Create an instance
sdk = await Sdk.create_instance({
    "base_url": "https://your-rpc-url.com",
    "chain_type": ChainType.EVM,
    "auth": Account.from_key("your-private-key")
})

# Use SDK modules
result = await sdk.storage.add_item({"item_type": "test", "item": "data"})
did = await sdk.did.create({...})
transfer = sdk.transfer.native("0x...", 1.5)
```

## Features

- **DID Operations**: Create, read, update, and remove decentralized identifiers
- **Storage Management**: On-chain data storage with add, get, update, remove operations
- **RBAC System**: Role-based access control with roles, groups, and permissions
- **Token Transfers**: Native token and ERC-20/721 transfers across chains
- **Multi-chain Support**: EVM and Substrate chain compatibility
- **Transaction Management**: Status callbacks and confirmation modes 