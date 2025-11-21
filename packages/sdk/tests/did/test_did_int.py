import os
import time
import random
import pytest
from eth_account.signers.base import BaseAccount

from peaq_sdk import Sdk
from peaq_sdk.types.common import ChainType
from peaq_sdk.types.did import Verification, VerificationMethodType, Service, Signature

from tests.helpers.config import EVM_CASES


@pytest.mark.asyncio
@pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
async def test_did_controller_and_address_same(label: str, base_url: str, account: BaseAccount | None):
    if not base_url or not account:
        pytest.skip("EVM env not configured")

    sdk = await Sdk.create_instance({
        "base_url": base_url,
        "chain_type": ChainType.EVM,
        "auth": account
    })

    controller = account.address
    did_address = account.address
    name = f"did:peaq:{account.address}"

    # Best-effort cleanup if previous run left state
    try:
        await (await sdk.did.remove({"name": name, "address": did_address})).receipt
    except Exception:
        pass

    create_res = await sdk.did.create({
        "name": name,
        "controller": controller,
        "did_address": did_address,
        "verification_methods": [Verification(type=VerificationMethodType.ECDSA)],
        "services": [Service(id="#ipfs", type="peaqStorage", data="hello-world")],
        "signature": Signature(type=VerificationMethodType.ECDSA, issuer=controller, hash="hello-world"),
    })
    receipt = await create_res.receipt
    assert (receipt.get("status", 1) if isinstance(receipt, dict) else getattr(receipt, "status", 1)) == 1

    did = await sdk.did.read({"name": name, "address": did_address})
    assert did is not None
    assert did.name == name
    assert did.document is not None
    assert did.document.id == f"did:peaq:{did_address}"
    assert did.document.controller == f"did:peaq:{controller}"

    remove_res = await sdk.did.remove({"name": name, "address": did_address})
    rm_receipt = await remove_res.receipt
    assert (rm_receipt.get("status", 1) if isinstance(rm_receipt, dict) else getattr(rm_receipt, "status", 1)) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
async def test_did_controller_and_address_different(label: str, base_url: str, account: BaseAccount | None):
    if not base_url or not account:
        pytest.skip("EVM env not configured")

    sdk = await Sdk.create_instance({   
        "base_url": base_url,
        "chain_type": ChainType.EVM,
        "auth": account
    })

    controller = account.address
    did_address = "0x48C9774C88736F7c169D2598278876727AFD3599"
    name = f"did:peaq:test:{account.address}"

    # Best-effort cleanup if previous run left state
    try:
        await (await sdk.did.remove({"name": name, "address": did_address})).receipt
    except Exception:
        pass

    create_res = await sdk.did.create({
        "name": name,
        "controller": controller,
        "did_address": did_address,
        "verification_methods": [Verification(type=VerificationMethodType.ECDSA)],
        "services": [Service(id="#ipfs", type="peaqStorage", data="hello-world")],
        "signature": Signature(type=VerificationMethodType.ECDSA, issuer=controller, hash="hello-world"),
    })
    receipt = await create_res.receipt
    assert (receipt.get("status", 1) if isinstance(receipt, dict) else getattr(receipt, "status", 1)) == 1

    did = await sdk.did.read({"name": name, "address": did_address})
    assert did is not None
    assert did.name == name
    assert did.document is not None
    assert did.document.id == f"did:peaq:{did_address}"
    assert did.document.controller == f"did:peaq:{controller}"

    remove_res = await sdk.did.remove({"name": name, "address": did_address})
    rm_receipt = await remove_res.receipt
    assert (rm_receipt.get("status", 1) if isinstance(rm_receipt, dict) else getattr(rm_receipt, "status", 1)) == 1