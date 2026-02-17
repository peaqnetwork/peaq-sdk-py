import uuid
import pytest
from eth_account.signers.base import BaseAccount

from peaq_sdk import Sdk
from peaq_sdk.types.common import ChainType
from peaq_sdk.types.rbac import GetRbacError

from tests.helpers.config import EVM_CASES


def _id32() -> str:
    # RBAC API requires exactly 32 chars; use 32 hex chars (UUID without dashes)
    return str(uuid.uuid4()).replace("-", "")


def _receipt_status(receipt) -> int:
    return receipt.get("status", 1) if isinstance(receipt, dict) else getattr(receipt, "status", 1)


async def _assert_relation_gone(fetch_call, predicate):
    """
    Relationship fetches are inconsistent across backends:
    some return an empty list, others raise GetRbacError.
    Accept either, but ensure the target relation is not present.
    """
    try:
        items = await fetch_call()
    except GetRbacError:
        return
    assert not any(predicate(item) for item in items)


@pytest.mark.asyncio
@pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
async def test_rbac_role_group_permission_lifecycle_and_fetches_evm(label: str, base_url: str, account: BaseAccount | None):
    """
    Covers:
    - create_role / update_role / disable_role
    - create_group / update_group / disable_group
    - create_permission / update_permission / disable_permission
    - fetch_role / fetch_group / fetch_permission
    - fetch_roles / fetch_groups / fetch_permissions
    """
    if not base_url or not account:
        pytest.skip("EVM env not configured")

    sdk = await Sdk.create_instance({
        "base_url": base_url,
        "chain_type": ChainType.EVM,
        "auth": account
    })
    owner = account.address

    role_id = _id32()
    group_id = _id32()
    permission_id = _id32()

    # 1) Create role
    res = await sdk.rbac.create_role({"role_name": "role-a", "role_id": role_id})
    # receipt = await res.receipt
    # assert _receipt_status(receipt) == 1

    r = await sdk.rbac.fetch_role({"owner": owner, "role_id": role_id})
    assert r.id == role_id
    assert r.name == "role-a"
    assert r.enabled is True

    # 2) Update role
    upd = await sdk.rbac.update_role({"role_id": role_id, "role_name": "role-a2"})
    upd_receipt = upd.receipt
    assert _receipt_status(upd_receipt) == 1
    r2 = await sdk.rbac.fetch_role({"owner": owner, "role_id": role_id})
    assert r2.name == "role-a2"

    # 3) Disable role
    dis = await sdk.rbac.disable_role({"role_id": role_id})
    dis_receipt = dis.receipt
    assert _receipt_status(dis_receipt) == 1
    r3 = await sdk.rbac.fetch_role({"owner": owner, "role_id": role_id})
    assert r3.enabled is False

    # 4) Create group
    g_res = await sdk.rbac.create_group({"group_name": "group-a", "group_id": group_id})
    g_receipt = g_res.receipt
    assert _receipt_status(g_receipt) == 1
    g = await sdk.rbac.fetch_group({"owner": owner, "group_id": group_id})
    assert g.id == group_id
    assert g.name == "group-a"
    assert g.enabled is True

    # 5) Update group
    g_upd = await sdk.rbac.update_group({"group_id": group_id, "group_name": "group-a2"})
    g_upd_receipt = g_upd.receipt
    assert _receipt_status(g_upd_receipt) == 1
    g2 = await sdk.rbac.fetch_group({"owner": owner, "group_id": group_id})
    assert g2.name == "group-a2"

    # 6) Disable group
    g_dis = await sdk.rbac.disable_group({"group_id": group_id})
    g_dis_receipt = g_dis.receipt
    assert _receipt_status(g_dis_receipt) == 1
    g3 = await sdk.rbac.fetch_group({"owner": owner, "group_id": group_id})
    assert g3.enabled is False

    # 7) Create permission
    p_res = await sdk.rbac.create_permission({"permission_name": "perm-a", "permission_id": permission_id})
    p_receipt = p_res.receipt
    assert _receipt_status(p_receipt) == 1
    p = await sdk.rbac.fetch_permission({"owner": owner, "permission_id": permission_id})
    assert p.id == permission_id
    assert p.name == "perm-a"
    assert p.enabled is True

    # 8) Update permission
    p_upd = await sdk.rbac.update_permission({"permission_id": permission_id, "permission_name": "perm-a2"})
    p_upd_receipt = p_upd.receipt
    assert _receipt_status(p_upd_receipt) == 1
    p2 = await sdk.rbac.fetch_permission({"owner": owner, "permission_id": permission_id})
    assert p2.name == "perm-a2"

    # 9) Disable permission
    p_dis = await sdk.rbac.disable_permission({"permission_id": permission_id})
    p_dis_receipt = p_dis.receipt
    assert _receipt_status(p_dis_receipt) == 1
    p3 = await sdk.rbac.fetch_permission({"owner": owner, "permission_id": permission_id})
    assert p3.enabled is False

    # 10) List fetches should include our entities
    roles = await sdk.rbac.fetch_roles({"owner": owner})
    assert any(x.id == role_id for x in roles)

    groups = await sdk.rbac.fetch_groups({"owner": owner})
    assert any(x.id == group_id for x in groups)

    perms = await sdk.rbac.fetch_permissions({"owner": owner})
    assert any(x.id == permission_id for x in perms)
    
    await sdk.disconnect()

# TODO: Change the reads to be done on substrate query (rather than extrinsic)

@pytest.mark.asyncio
@pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
async def test_rbac_assign_unassign_and_user_permissions_evm(label: str, base_url: str, account: BaseAccount | None):
    """
    Covers:
    - assign_permission_to_role / unassign_permission_to_role + fetch_role_permissions
    - assign_role_to_group / unassign_role_to_group + fetch_group_roles / fetch_group_permissions
    - assign_role_to_user / unassign_role_to_user + fetch_user_roles / fetch_user_permissions
    - assign_user_to_group / unassign_user_to_group + fetch_user_groups
    """
    if not base_url or not account:
        pytest.skip("EVM env not configured")

    sdk = await Sdk.create_instance({
        "base_url": base_url,
        "chain_type": ChainType.EVM,
        "auth": account
    })
    owner = account.address

    # Create entities for relationships
    role_id = _id32()
    group_id = _id32()
    permission_id = _id32()
    user_id = _id32()

    # Create role/group/permission (enabled) — do this sequentially so we always use receipts.
    role_res = await sdk.rbac.create_role({"role_name": "role-rel", "role_id": role_id})
    assert _receipt_status(role_res.receipt) == 1

    group_res = await sdk.rbac.create_group({"group_name": "group-rel", "group_id": group_id})
    assert _receipt_status(group_res.receipt) == 1

    perm_res = await sdk.rbac.create_permission({"permission_name": "perm-rel", "permission_id": permission_id})
    assert _receipt_status(perm_res.receipt) == 1

    # A) role <- permission
    a = await sdk.rbac.assign_permission_to_role({"permission_id": permission_id, "role_id": role_id})
    a_receipt = a.receipt
    assert _receipt_status(a_receipt) == 1

    role_perms = await sdk.rbac.fetch_role_permissions({"owner": owner, "role_id": role_id})
    assert any((x.role == role_id and x.permission == permission_id) for x in role_perms)

    # B) group <- role
    b = await sdk.rbac.assign_role_to_group({"role_id": role_id, "group_id": group_id})
    b_receipt = b.receipt
    assert _receipt_status(b_receipt) == 1

    grp_roles = await sdk.rbac.fetch_group_roles({"owner": owner, "group_id": group_id})
    assert any((x.group == group_id and x.role == role_id) for x in grp_roles)

    grp_perms = await sdk.rbac.fetch_group_permissions({"owner": owner, "group_id": group_id})
    # group permissions should include permission via role assignment
    assert any(p.id == permission_id for p in grp_perms)

    # C) user <- role (direct)
    c = await sdk.rbac.assign_role_to_user({"role_id": role_id, "user_id": user_id})
    c_receipt = c.receipt
    assert _receipt_status(c_receipt) == 1

    user_roles = await sdk.rbac.fetch_user_roles({"owner": owner, "user_id": user_id})
    assert any((x.user == user_id and x.role == role_id) for x in user_roles)

    user_perms = await sdk.rbac.fetch_user_permissions({"owner": owner, "user_id": user_id})
    assert any(p.id == permission_id for p in user_perms)

    # D) user <- group
    d = await sdk.rbac.assign_user_to_group({"user_id": user_id, "group_id": group_id})
    d_receipt = d.receipt
    assert _receipt_status(d_receipt) == 1

    user_groups = await sdk.rbac.fetch_user_groups({"owner": owner, "user_id": user_id})
    assert any((x.user == user_id and x.group == group_id) for x in user_groups)

    # Unassign in reverse order and assert fetches no longer show relationships
    du = await sdk.rbac.unassign_user_to_group({"user_id": user_id, "group_id": group_id})
    assert _receipt_status(du.receipt) == 1
    await _assert_relation_gone(
        lambda: sdk.rbac.fetch_user_groups({"owner": owner, "user_id": user_id}),
        lambda x: x.user == user_id and x.group == group_id,
    )

    cu = await sdk.rbac.unassign_role_to_user({"role_id": role_id, "user_id": user_id})
    assert _receipt_status(cu.receipt) == 1
    await _assert_relation_gone(
        lambda: sdk.rbac.fetch_user_roles({"owner": owner, "user_id": user_id}),
        lambda x: x.user == user_id and x.role == role_id,
    )

    bu = await sdk.rbac.unassign_role_to_group({"role_id": role_id, "group_id": group_id})
    assert _receipt_status(bu.receipt) == 1
    await _assert_relation_gone(
        lambda: sdk.rbac.fetch_group_roles({"owner": owner, "group_id": group_id}),
        lambda x: x.group == group_id and x.role == role_id,
    )

    au = await sdk.rbac.unassign_permission_to_role({"permission_id": permission_id, "role_id": role_id})
    assert _receipt_status(au.receipt) == 1
    await _assert_relation_gone(
        lambda: sdk.rbac.fetch_role_permissions({"owner": owner, "role_id": role_id}),
        lambda x: x.role == role_id and x.permission == permission_id,
    )

    # Cleanup: disable entities to avoid leaving enabled RBAC objects around
    for res in [
        await sdk.rbac.disable_permission({"permission_id": permission_id}),
        await sdk.rbac.disable_group({"group_id": group_id}),
        await sdk.rbac.disable_role({"role_id": role_id}),
    ]:
        assert _receipt_status(res.receipt) == 1

    await sdk.disconnect()