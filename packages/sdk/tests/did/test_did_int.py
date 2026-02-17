import os
import time
import random
import pytest
from eth_account.signers.base import BaseAccount

from peaq_sdk import Sdk
from peaq_sdk.types.common import ChainType
from peaq_sdk.types.did import Verification, VerificationMethodType, Service, Signature

from tests.helpers.config import EVM_CASES


def _norm_service(s: dict) -> dict:
    """
    The chain/protobuf layer tends to normalize unset strings to "" rather than None.
    Normalize to a stable shape for assertions.
    """
    return {
        "id": s.get("id"),
        "type": s.get("type"),
        "serviceEndpoint": (s.get("serviceEndpoint") or None),
        "data": (s.get("data") or None),
    }


def _norm_services(services: list[dict]) -> list[dict]:
    return sorted([_norm_service(s) for s in services], key=lambda x: (x["id"] or "", x["type"] or ""))


def _assert_did_document_roundtrip(
    did,
    *,
    did_address: str,
    controller: str,
    expected_services: list[dict],
    expected_signature: dict | None,
):
    assert did is not None
    assert did.document is not None

    # Core identity fields
    assert did.document.id == f"did:peaq:{did_address}"
    assert did.document.controller == f"did:peaq:{controller}"

    # Verification methods: SDK normalizes these on create
    vms = did.document.verificationMethod
    assert isinstance(vms, list)
    assert len(vms) == 1

    vm0 = vms[0]
    assert vm0["type"] == VerificationMethodType.ECDSA.value
    assert vm0["controller"] == f"did:peaq:{controller}"
    # Auto-generated method id if not provided by user
    assert vm0["id"].startswith(f"did:peaq:{did_address}#keys-")
    # For EVM, SDK uses EIP-155 identifier format
    pkmb = vm0.get("publicKeyMultibase")
    assert isinstance(pkmb, str)
    assert pkmb.startswith("eip155:")
    assert pkmb.endswith(f":{controller}")

    # Authentication should reference the verification method id(s)
    auth = did.document.authentication
    assert isinstance(auth, list)
    assert vm0["id"] in auth

    # Services
    services = did.document.service
    assert isinstance(services, list)
    assert _norm_services(services) == _norm_services(expected_services)

    # Signature
    assert did.document.signature == expected_signature


def _rand_suffix() -> str:
    # Keep tags short to satisfy on-chain name length constraints.
    return f"{int(time.time()) % 100000:05d}{random.randint(0, 9999):04d}"


def _mk_name(prefix: str, addr: str) -> str:
    # Existing tests show names like `did:peaq:test:<address>` work; keep any additions short.
    # Example: did:peaq:sv:0xabc... (prefix <= 3 chars)
    return f"did:peaq:{prefix}:{addr}"


@pytest.mark.asyncio
@pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
async def test_did_create_rejects_service_without_endpoint_or_data(label: str, base_url: str, account: BaseAccount | None):
    if not base_url or not account:
        pytest.skip("EVM env not configured")

    sdk = await Sdk.create_instance({
        "base_url": base_url,
        "chain_type": ChainType.EVM,
        "auth": account
    })

    controller = account.address
    did_address = account.address
    # Keep name short (chain can revert with "Name too long")
    name = _mk_name("bad", account.address)

    with pytest.raises(ValueError, match=r"must have either serviceEndpoint or data"):
        await sdk.did.create({
            "name": name,
            "controller": controller,
            "did_address": did_address,
            "verification_methods": [],
            "services": [Service(id="#bad", type="peaqStorage")],
        })

    await sdk.disconnect()


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
        (await sdk.did.remove({"name": name, "address": did_address})).receipt
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
    receipt = create_res.receipt
    assert (receipt.get("status", 1) if isinstance(receipt, dict) else getattr(receipt, "status", 1)) == 1

    did = await sdk.did.read({"name": name, "address": did_address})
    assert did is not None
    assert did.name == name
    _assert_did_document_roundtrip(
        did,
        did_address=did_address,
        controller=controller,
        expected_services=[
            {"id": "#ipfs", "type": "peaqStorage", "serviceEndpoint": None, "data": "hello-world"}
        ],
        expected_signature={
            "type": VerificationMethodType.ECDSA.value,
            "issuer": controller,
            "hash": "hello-world",
        },
    )

    remove_res = await sdk.did.remove({"name": name, "address": did_address})
    rm_receipt = remove_res.receipt
    assert (rm_receipt.get("status", 1) if isinstance(rm_receipt, dict) else getattr(rm_receipt, "status", 1)) == 1
    
    await sdk.disconnect()


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
        (await sdk.did.remove({"name": name, "address": did_address})).receipt
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
    receipt = create_res.receipt
    assert (receipt.get("status", 1) if isinstance(receipt, dict) else getattr(receipt, "status", 1)) == 1

    did = await sdk.did.read({"name": name, "address": did_address})
    assert did is not None
    assert did.name == name
    _assert_did_document_roundtrip(
        did,
        did_address=did_address,
        controller=controller,
        expected_services=[
            {"id": "#ipfs", "type": "peaqStorage", "serviceEndpoint": None, "data": "hello-world"}
        ],
        expected_signature={
            "type": VerificationMethodType.ECDSA.value,
            "issuer": controller,
            "hash": "hello-world",
        },
    )

    remove_res = await sdk.did.remove({"name": name, "address": did_address})
    rm_receipt = remove_res.receipt
    assert (rm_receipt.get("status", 1) if isinstance(rm_receipt, dict) else getattr(rm_receipt, "status", 1)) == 1
    
    await sdk.disconnect()


@pytest.mark.asyncio
@pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
async def test_did_services_service_endpoint_and_optional_signature(label: str, base_url: str, account: BaseAccount | None):
    if not base_url or not account:
        pytest.skip("EVM env not configured")

    sdk = await Sdk.create_instance({
        "base_url": base_url,
        "chain_type": ChainType.EVM,
        "auth": account
    })

    controller = account.address
    did_address = account.address
    name = _mk_name("sv", account.address)

    # Best-effort cleanup
    try:
        (await sdk.did.remove({"name": name, "address": did_address})).receipt
    except Exception:
        pass

    create_res = await sdk.did.create({
        "name": name,
        "controller": controller,
        "did_address": did_address,
        "verification_methods": [Verification(type=VerificationMethodType.ECDSA)],
        "services": [Service(id="#http", type="peaqEndpoint", service_endpoint="https://example.com")],
        # Intentionally omit signature (should round-trip as None)
    })
    receipt = create_res.receipt
    assert (receipt.get("status", 1) if isinstance(receipt, dict) else getattr(receipt, "status", 1)) == 1

    did = await sdk.did.read({"name": name, "address": did_address})
    assert did is not None
    assert did.name == name
    _assert_did_document_roundtrip(
        did,
        did_address=did_address,
        controller=controller,
        expected_services=[
            {"id": "#http", "type": "peaqEndpoint", "serviceEndpoint": "https://example.com", "data": None}
        ],
        expected_signature=None,
    )

    remove_res = await sdk.did.remove({"name": name, "address": did_address})
    rm_receipt = remove_res.receipt
    assert (rm_receipt.get("status", 1) if isinstance(rm_receipt, dict) else getattr(rm_receipt, "status", 1)) == 1
    
    await sdk.disconnect()
    


@pytest.mark.asyncio
@pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
async def test_did_multiple_verification_methods_and_pk_override(label: str, base_url: str, account: BaseAccount | None):
    if not base_url or not account:
        pytest.skip("EVM env not configured")

    sdk = await Sdk.create_instance({
        "base_url": base_url,
        "chain_type": ChainType.EVM,
        "auth": account
    })

    controller = account.address
    did_address = account.address
    name = _mk_name("vm", account.address)

    # Best-effort cleanup
    try:
        (await sdk.did.remove({"name": name, "address": did_address})).receipt
    except Exception:
        pass

    override_pk = "eip155:9990:0x0000000000000000000000000000000000000000"
    create_res = await sdk.did.create({
        "name": name,
        "controller": controller,
        "did_address": did_address,
        "verification_methods": [
            Verification(type=VerificationMethodType.ECDSA),
            Verification(
                type=VerificationMethodType.ECDSA,
                id=f"did:peaq:{did_address}#custom-key",
                controller=f"did:peaq:{controller}",
                public_key_multibase=override_pk,
            ),
        ],
        "services": [Service(id="#ipfs", type="peaqStorage", data="hello-world")],
        "signature": Signature(type=VerificationMethodType.ECDSA, issuer=controller, hash="hello-world"),
    })
    receipt = create_res.receipt
    assert (receipt.get("status", 1) if isinstance(receipt, dict) else getattr(receipt, "status", 1)) == 1

    did = await sdk.did.read({"name": name, "address": did_address})
    assert did is not None
    assert did.document is not None

    vms = did.document.verificationMethod
    assert isinstance(vms, list)
    assert len(vms) == 2

    # First vm is auto-generated
    assert vms[0]["type"] == VerificationMethodType.ECDSA.value
    assert vms[0]["id"].startswith(f"did:peaq:{did_address}#keys-")

    # Second vm should preserve explicit id/controller/pk override
    assert vms[1]["type"] == VerificationMethodType.ECDSA.value
    assert vms[1]["id"] == f"did:peaq:{did_address}#custom-key"
    assert vms[1]["controller"] == f"did:peaq:{controller}"
    assert vms[1]["publicKeyMultibase"] == override_pk

    # Auth should include both method ids
    auth = did.document.authentication
    assert isinstance(auth, list)
    assert vms[0]["id"] in auth
    assert vms[1]["id"] in auth

    remove_res = await sdk.did.remove({"name": name, "address": did_address})
    rm_receipt = remove_res.receipt
    assert (rm_receipt.get("status", 1) if isinstance(rm_receipt, dict) else getattr(rm_receipt, "status", 1)) == 1
    
    await sdk.disconnect()
    


@pytest.mark.asyncio
@pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
async def test_did_update_roundtrip(label: str, base_url: str, account: BaseAccount | None):
    if not base_url or not account:
        pytest.skip("EVM env not configured")

    sdk = await Sdk.create_instance({
        "base_url": base_url,
        "chain_type": ChainType.EVM,
        "auth": account
    })

    controller = account.address
    did_address = account.address
    name = _mk_name("up", account.address)

    # Best-effort cleanup
    try:
        (await sdk.did.remove({"name": name, "address": did_address})).receipt
    except Exception:
        pass

    # Create initial DID
    create_res = await sdk.did.create({
        "name": name,
        "controller": controller,
        "did_address": did_address,
        "verification_methods": [Verification(type=VerificationMethodType.ECDSA)],
        "services": [Service(id="#ipfs", type="peaqStorage", data="v1")],
        "signature": Signature(type=VerificationMethodType.ECDSA, issuer=controller, hash="v1"),
    })
    _ = create_res.receipt

    # Update DID (overwrite services + signature)
    update_res = await sdk.did.update({
        "name": name,
        "controller": controller,
        "did_address": did_address,
        "verification_methods": [Verification(type=VerificationMethodType.ECDSA)],
        "services": [Service(id="#ipfs", type="peaqStorage", data="v2")],
        "signature": Signature(type=VerificationMethodType.ECDSA, issuer=controller, hash="v2"),
    })
    upd_receipt = update_res.receipt
    assert (upd_receipt.get("status", 1) if isinstance(upd_receipt, dict) else getattr(upd_receipt, "status", 1)) == 1

    did = await sdk.did.read({"name": name, "address": did_address})
    assert did is not None
    assert did.name == name
    _assert_did_document_roundtrip(
        did,
        did_address=did_address,
        controller=controller,
        expected_services=[
            {"id": "#ipfs", "type": "peaqStorage", "serviceEndpoint": None, "data": "v2"}
        ],
        expected_signature={
            "type": VerificationMethodType.ECDSA.value,
            "issuer": controller,
            "hash": "v2",
        },
    )

    remove_res = await sdk.did.remove({"name": name, "address": did_address})
    rm_receipt = remove_res.receipt
    assert (rm_receipt.get("status", 1) if isinstance(rm_receipt, dict) else getattr(rm_receipt, "status", 1)) == 1
    
    await sdk.disconnect()