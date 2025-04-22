import pytest

@pytest.mark.skip(reason="Testing EVM")
def test_substrate_rbac(substrate_sdk, role_name, role_id, connection_type):
    test = substrate_sdk.rbac.fetch_role(owner='5Df42mkztLtkksgQuLy4YV6hmhzdjYvDknoxHv1QBkaY12Pg', role_id='33191458-aa93-4c7e-9102-6caa087b')
    print(test)
    # create_result = substrate_sdk.rbac.create_role(role_name=role_name)
    # print(create_result)
    
    
    
    # create_result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)

def test_evm_rbac(evm_sdk, role_name, role_id, connection_type):
    sdk, base_wss = evm_sdk
    
    
    test = sdk.rbac.fetch_role(owner='0x9Eeab1aCcb1A701aEfAB00F3b8a275a39646641C', role_id='dd206072-7118-48be-ba87-1dacc332', wss_base_url=base_wss)

    print(test)