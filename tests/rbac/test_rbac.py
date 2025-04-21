import pytest

def test_rbac(substrate_sdk, role_name, role_id, connection_type):
    
    create_result = substrate_sdk.rbac.create_role(role_name=role_name)
    print(create_result)
    
    # create_result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)
    