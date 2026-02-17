import json
import time
import random
import pytest
from eth_account.signers.base import BaseAccount

from peaq_sdk import Sdk
from peaq_sdk.types import ConfirmationMode
from peaq_sdk.types.common import ChainType

from tests.helpers.config import EVM_CASES


def _rand_suffix() -> str:
    # keep short for any on-chain constraints
    return f"{int(time.time()) % 100000:05d}{random.randint(0, 9999):04d}"


def _mk_item_type(prefix: str) -> str:
    # item_type is encoded as bytes; keep it short and unique per run
    return f"{prefix}:{_rand_suffix()}"


def _receipt_status(receipt) -> int:
    # web3 receipts are usually dict-like; keep this flexible
    return receipt.get("status", 1) if isinstance(receipt, dict) else getattr(receipt, "status", 1)

def status_callback(status_data):
    print(f"Status: {status_data['status']}")  # BROADCAST | IN_BLOCK | FINALIZED
    print(f"Hash: {status_data['hash']}")
    print(f"Confirmations: {status_data['total_confirmations']}")
    print(f"Mode: {status_data['confirmation_mode']}")
    # print(json.dumps(status_data, indent=2)).  # pretty print all

@pytest.mark.asyncio
@pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
async def test_storage_add_get_update_remove_string(label: str, base_url: str, account: BaseAccount | None):
    if not base_url or not account:
        pytest.skip("EVM env not configured")

    sdk = await Sdk.create_instance({
        "base_url": base_url,
        "chain_type": ChainType.EVM,
        "auth": account
    })

    item_type = _mk_item_type("t")
    addr = account.address

    # Best-effort cleanup
    try:
        (await sdk.storage.remove_item({"item_type": item_type})).receipt
    except Exception:
        pass

    # Add
    add_res = await sdk.storage.add_item({"item_type": item_type, "item": "hello"})
    # add_res = await sdk.storage.add_item({"item_type": item_type, "item": "hello"},
    #     status_callback, # Have function defined 
    # {
    #   "mode": ConfirmationMode.CUSTOM,
    #   "confirmations": 5
    # })
    add_receipt = add_res.receipt
    assert _receipt_status(add_receipt) == 1

    # Get
    got = await sdk.storage.get_item({"item_type": item_type, "address": addr})
    assert got is not None
    assert isinstance(got, dict)
    assert got[item_type] == "hello"

    # Update
    upd_res = await sdk.storage.update_item({"item_type": item_type, "item": "world"})
    upd_receipt = upd_res.receipt
    assert _receipt_status(upd_receipt) == 1

    got2 = await sdk.storage.get_item({"item_type": item_type, "address": addr})
    assert got2 is not None
    assert got2[item_type] == "world"

    # Remove
    rm_res = await sdk.storage.remove_item({"item_type": item_type})
    rm_receipt = rm_res.receipt
    assert _receipt_status(rm_receipt) == 1

    # Now missing
    got3 = await sdk.storage.get_item({"item_type": item_type, "address": addr})
    assert got3 is None
    
    await sdk.disconnect()


@pytest.mark.asyncio
@pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
async def test_storage_add_get_json_roundtrip(label: str, base_url: str, account: BaseAccount | None):
    if not base_url or not account:
        pytest.skip("EVM env not configured")

    sdk = await Sdk.create_instance({
        "base_url": base_url,
        "chain_type": ChainType.EVM,
        "auth": account
    })

    item_type = _mk_item_type("json")
    addr = account.address

    payload = {"k": "v", "n": 1, "nested": {"ok": True}}

    # Best-effort cleanup
    try:
        (await sdk.storage.remove_item({"item_type": item_type})).receipt
    except Exception:
        pass

    add_res = await sdk.storage.add_item({"item_type": item_type, "item": payload})
    add_receipt = add_res.receipt
    assert _receipt_status(add_receipt) == 1

    got = await sdk.storage.get_item({"item_type": item_type, "address": addr})
    assert got is not None
    raw = got[item_type]
    assert isinstance(raw, str)

    decoded = json.loads(raw)
    assert decoded == payload

    # Cleanup
    rm_res = await sdk.storage.remove_item({"item_type": item_type})
    rm_receipt = rm_res.receipt
    assert _receipt_status(rm_receipt) == 1
    
    await sdk.disconnect()


@pytest.mark.asyncio
@pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
async def test_storage_get_missing_returns_none(label: str, base_url: str, account: BaseAccount | None):
    if not base_url or not account:
        pytest.skip("EVM env not configured")

    sdk = await Sdk.create_instance({
        "base_url": base_url,
        "chain_type": ChainType.EVM,
        "auth": account
    })

    item_type = _mk_item_type("missing")
    addr = account.address

    got = await sdk.storage.get_item({"item_type": item_type, "address": addr})
    assert got is None
    
    await sdk.disconnect()


@pytest.mark.asyncio
@pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
async def test_storage_get_requires_address_if_no_signer(label: str, base_url: str, account: BaseAccount | None):
    if not base_url or not account:
        pytest.skip("EVM env not configured")

    # Create instance with no auth/signer to force address requirement on get_item()
    sdk = await Sdk.create_instance({
        "base_url": base_url,
        "chain_type": ChainType.EVM,
    })

    with pytest.raises(TypeError, match=r"Address is required"):
        await sdk.storage.get_item({"item_type": _mk_item_type("needaddr")})
    
    await sdk.disconnect()