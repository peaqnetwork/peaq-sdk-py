# Peaq MSF SDK

Peaq Network SDK for Machine Station Factory operations on EVM-compatible blockchains.

## Installation

```bash
pip install peaq-msf
```

## Usage

```python
from peaq_msf import MSF
from eth_account import Account

# Create an instance
mst = MSF.create_instance({
    "base_url": "https://your-rpc-url.com",
    "machine_station_address": "0x...",
    "station_admin": Account.from_key("your-private-key"),
    "station_manager": Account.from_key("your-manager-private-key")
})
```

## Features

- Machine Station Factory contract interactions
- Smart account deployment
- Transaction execution
- EIP-712 signature generation
- Configuration management 