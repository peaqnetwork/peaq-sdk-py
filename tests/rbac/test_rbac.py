import pytest

@pytest.mark.skip(reason="Testing EVM")
def test_substrate_rbac(substrate_sdk, role_name, role_id, connection_type):
    
    create_result = substrate_sdk.rbac.create_role(role_name=role_name)
    print(create_result)
    
    # create_result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)

def test_evm_rbac(evm_sdk, role_name, role_id, connection_type):
    sdk, base_wss = evm_sdk
    
    
    create_result = sdk.rbac.create_role(role_name=role_name)
    print(create_result)