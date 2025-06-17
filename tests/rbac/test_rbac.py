import pytest
from peaq_sdk.types.rbac import GetRbacError, FetchResponseData
from peaq_sdk.types.common import WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult

class TestRBACCreateOperations:
    """Test creation of roles, groups, and permissions."""
    
    def test_substrate_create_role(self, substrate_sdk, role_name, role_id):
        """Test creating a role on Substrate."""
        result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(result, WrittenTransactionResult)
        assert result.message.startswith("Successfully added the RBAC role")
        assert role_name in result.message
        assert role_id in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_substrate_create_role_auto_id(self, substrate_sdk, role_name):
        """Test creating a role with auto-generated ID on Substrate."""
        result = substrate_sdk.rbac.create_role(role_name=role_name)
        assert isinstance(result, WrittenTransactionResult)
        assert result.message.startswith("Successfully added the RBAC role")
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_substrate_create_group(self, substrate_sdk, group_name, group_id):
        """Test creating a group on Substrate."""
        result = substrate_sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(result, WrittenTransactionResult)
        assert result.message.startswith("Successfully added the RBAC group")
        assert group_name in result.message
        assert group_id in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_substrate_create_permission(self, substrate_sdk, permission_name, permission_id):
        """Test creating a permission on Substrate."""
        result = substrate_sdk.rbac.create_permission(permission_name=permission_name, permission_id=permission_id)
        assert isinstance(result, WrittenTransactionResult)
        assert result.message.startswith("Successfully added the RBAC permission")
        assert permission_name in result.message
        assert permission_id in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_evm_create_role(self, evm_sdk, role_name, role_id):
        """Test creating a role on EVM."""
        sdk, base_wss = evm_sdk
        result = sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(result, WrittenTransactionResult)
        assert result.message.startswith("Successfully added the RBAC role")
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1
    
    def test_evm_create_group(self, evm_sdk, group_name, group_id):
        """Test creating a group on EVM."""
        sdk, base_wss = evm_sdk
        result = sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(result, WrittenTransactionResult)
        assert result.message.startswith("Successfully added the RBAC group")
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1
    
    def test_evm_create_permission(self, evm_sdk, permission_name, permission_id):
        """Test creating a permission on EVM."""
        sdk, base_wss = evm_sdk
        result = sdk.rbac.create_permission(permission_name=permission_name, permission_id=permission_id)
        assert isinstance(result, WrittenTransactionResult)
        assert result.message.startswith("Successfully added the RBAC permission")
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1

class TestRBACCreateThenFetchOperations:
    """Test creating entities and then fetching them to ensure they exist."""
    
    def test_substrate_create_then_fetch_role(self, substrate_sdk, config, role_name, role_id):
        """Test creating a role and then fetching it on Substrate."""
        # First create the role
        create_result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then fetch it
        fetch_result = substrate_sdk.rbac.fetch_role(
            owner=config['SUBSTRATE_ADDRESS'], 
            role_id=role_id
        )
        assert isinstance(fetch_result, FetchResponseData)
        assert fetch_result.id == role_id
        assert fetch_result.name == role_name
        assert isinstance(fetch_result.enabled, bool)
    
    def test_substrate_create_then_fetch_group(self, substrate_sdk, config, group_name, group_id):
        """Test creating a group and then fetching it on Substrate."""
        # First create the group
        create_result = substrate_sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then fetch it
        fetch_result = substrate_sdk.rbac.fetch_group(
            owner=config['SUBSTRATE_ADDRESS'], 
            group_id=group_id
        )
        assert isinstance(fetch_result, FetchResponseData)
        assert fetch_result.id == group_id
        assert fetch_result.name == group_name
        assert isinstance(fetch_result.enabled, bool)
    
    def test_substrate_create_then_fetch_permission(self, substrate_sdk, config, permission_name, permission_id):
        """Test creating a permission and then fetching it on Substrate."""
        # First create the permission
        create_result = substrate_sdk.rbac.create_permission(permission_name=permission_name, permission_id=permission_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then fetch it
        fetch_result = substrate_sdk.rbac.fetch_permission(
            owner=config['SUBSTRATE_ADDRESS'], 
            permission_id=permission_id
        )
        assert isinstance(fetch_result, FetchResponseData)
        assert fetch_result.id == permission_id
        assert fetch_result.name == permission_name
        assert isinstance(fetch_result.enabled, bool)
    
    def test_evm_create_then_fetch_role(self, evm_sdk, config, role_name, role_id):
        """Test creating a role and then fetching it on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the role
        create_result = sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt.status == 1
        
        # Then fetch it
        fetch_result = sdk.rbac.fetch_role(
            owner=config['EVM_ADDRESS'], 
            role_id=role_id,
            wss_base_url=base_wss
        )
        assert isinstance(fetch_result, FetchResponseData)
        assert fetch_result.id == role_id
        assert fetch_result.name == role_name
        assert isinstance(fetch_result.enabled, bool)
    
    def test_evm_create_then_fetch_group(self, evm_sdk, config, group_name, group_id):
        """Test creating a group and then fetching it on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the group
        create_result = sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt.status == 1
        
        # Then fetch it
        fetch_result = sdk.rbac.fetch_group(
            owner=config['EVM_ADDRESS'], 
            group_id=group_id,
            wss_base_url=base_wss
        )
        assert isinstance(fetch_result, FetchResponseData)
        assert fetch_result.id == group_id
        assert fetch_result.name == group_name
        assert isinstance(fetch_result.enabled, bool)
    
    def test_evm_create_then_fetch_permission(self, evm_sdk, config, permission_name, permission_id):
        """Test creating a permission and then fetching it on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the permission
        create_result = sdk.rbac.create_permission(permission_name=permission_name, permission_id=permission_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt.status == 1
        
        # Then fetch it
        fetch_result = sdk.rbac.fetch_permission(
            owner=config['EVM_ADDRESS'], 
            permission_id=permission_id,
            wss_base_url=base_wss
        )
        assert isinstance(fetch_result, FetchResponseData)
        assert fetch_result.id == permission_id
        assert fetch_result.name == permission_name
        assert isinstance(fetch_result.enabled, bool)

class TestRBACAssignmentOperations:
    """Test assignment operations (permission to role, role to group, etc.)."""
    
    def test_substrate_assign_permission_to_role(self, substrate_sdk, permission_name, permission_id, role_name, role_id):
        """Test creating a permission and role, then assigning the permission to the role on Substrate."""
        # First create the permission and role
        permission_result = substrate_sdk.rbac.create_permission(permission_name=permission_name, permission_id=permission_id)
        assert isinstance(permission_result, WrittenTransactionResult)
        assert permission_result.receipt['_ExtrinsicReceipt__is_success']
        
        role_result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(role_result, WrittenTransactionResult)
        assert role_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then assign permission to role
        result = substrate_sdk.rbac.assign_permission_to_role(
            permission_id=permission_id, 
            role_id=role_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully assigned permission {permission_id} to role {role_id}" in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_substrate_assign_role_to_group(self, substrate_sdk, role_name, role_id, group_name, group_id):
        """Test creating a role and group, then assigning the role to the group on Substrate."""
        # First create the role and group
        role_result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(role_result, WrittenTransactionResult)
        assert role_result.receipt['_ExtrinsicReceipt__is_success']
        
        group_result = substrate_sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(group_result, WrittenTransactionResult)
        assert group_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then assign role to group
        result = substrate_sdk.rbac.assign_role_to_group(
            role_id=role_id, 
            group_id=group_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully assigned role {role_id} to group {group_id}" in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_substrate_assign_role_to_user(self, substrate_sdk, role_name, role_id, user_id):
        """Test creating a role, then assigning it to a user on Substrate."""
        # First create the role
        role_result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(role_result, WrittenTransactionResult)
        assert role_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then assign role to user
        result = substrate_sdk.rbac.assign_role_to_user(
            role_id=role_id, 
            user_id=user_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully assigned role {role_id} to user {user_id}" in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_substrate_assign_user_to_group(self, substrate_sdk, user_id, group_name, group_id):
        """Test creating a group, then assigning a user to it on Substrate."""
        # First create the group
        group_result = substrate_sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(group_result, WrittenTransactionResult)
        assert group_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then assign user to group
        result = substrate_sdk.rbac.assign_user_to_group(
            user_id=user_id, 
            group_id=group_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully assigned user {user_id} to group {group_id}" in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_evm_assign_permission_to_role(self, evm_sdk, permission_name, permission_id, role_name, role_id):
        """Test creating a permission and role, then assigning the permission to the role on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the permission and role
        permission_result = sdk.rbac.create_permission(permission_name=permission_name, permission_id=permission_id)
        assert isinstance(permission_result, WrittenTransactionResult)
        assert permission_result.receipt.status == 1
        
        role_result = sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(role_result, WrittenTransactionResult)
        assert role_result.receipt.status == 1
        
        # Then assign permission to role
        result = sdk.rbac.assign_permission_to_role(
            permission_id=permission_id, 
            role_id=role_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully assigned permission {permission_id} to role {role_id}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1
    
    def test_evm_assign_role_to_group(self, evm_sdk, role_name, role_id, group_name, group_id):
        """Test creating a role and group, then assigning the role to the group on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the role and group
        role_result = sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(role_result, WrittenTransactionResult)
        assert role_result.receipt.status == 1
        
        group_result = sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(group_result, WrittenTransactionResult)
        assert group_result.receipt.status == 1
        
        # Then assign role to group
        result = sdk.rbac.assign_role_to_group(
            role_id=role_id, 
            group_id=group_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully assigned role {role_id} to group {group_id}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1
    
    def test_evm_assign_role_to_user(self, evm_sdk, role_name, role_id, user_id):
        """Test creating a role, then assigning it to a user on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the role
        role_result = sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(role_result, WrittenTransactionResult)
        assert role_result.receipt.status == 1
        
        # Then assign role to user
        result = sdk.rbac.assign_role_to_user(
            role_id=role_id, 
            user_id=user_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully assigned role {role_id} to user {user_id}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1
    
    def test_evm_assign_user_to_group(self, evm_sdk, user_id, group_name, group_id):
        """Test creating a group, then assigning a user to it on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the group
        group_result = sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(group_result, WrittenTransactionResult)
        assert group_result.receipt.status == 1
        
        # Then assign user to group
        result = sdk.rbac.assign_user_to_group(
            user_id=user_id, 
            group_id=group_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully assigned user {user_id} to group {group_id}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1

class TestRBACUpdateOperations:
    """Test update operations for roles, groups, and permissions."""
    
    def test_substrate_update_role(self, substrate_sdk, role_id, role_name):
        """Test creating then updating a role name on Substrate."""
        # First create the role
        create_result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then update it
        new_name = f"updated-{role_name}"
        result = substrate_sdk.rbac.update_role(
            role_id=role_id, 
            role_name=new_name
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully updated role {role_id} with name {new_name}" in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    # def test_substrate_update_group(self, substrate_sdk, group_id, group_name):
    #     """Test creating then updating a group name on Substrate."""
    #     # First create the group
    #     create_result = substrate_sdk.rbac.create_group(group_name=group_name, group_id=group_id)
    #     assert isinstance(create_result, WrittenTransactionResult)
    #     assert create_result.receipt['_ExtrinsicReceipt__is_success']
        
    #     # Then update it
    #     new_name = f"updated-{group_name}"
    #     result = substrate_sdk.rbac.update_group(
    #         group_id=group_id, 
    #         group_name=new_name
    #     )
    #     assert isinstance(result, WrittenTransactionResult)
    #     assert f"Successfully updated group {group_id} with name {new_name}" in result.message
    #     assert 'extrinsic_hash' in result.receipt
    #     assert result.receipt['_ExtrinsicReceipt__is_success']
    
    # def test_substrate_update_permission(self, substrate_sdk, permission_id, permission_name):
    #     """Test creating then updating a permission name on Substrate."""
    #     # First create the permission
    #     create_result = substrate_sdk.rbac.create_permission(permission_name=permission_name, permission_id=permission_id)
    #     assert isinstance(create_result, WrittenTransactionResult)
    #     assert create_result.receipt['_ExtrinsicReceipt__is_success']
        
    #     # Then update it
    #     new_name = f"updated-{permission_name}"
    #     result = substrate_sdk.rbac.update_permission(
    #         permission_id=permission_id, 
    #         permission_name=new_name
    #     )
    #     assert isinstance(result, WrittenTransactionResult)
    #     assert f"Successfully updated permission {permission_id} with name {new_name}" in result.message
    #     assert 'extrinsic_hash' in result.receipt
    #     assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_evm_update_role(self, evm_sdk, role_id, role_name):
        """Test creating then updating a role name on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the role
        create_result = sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt.status == 1
        
        # Then update it
        new_name = f"updated-{role_name}"
        result = sdk.rbac.update_role(
            role_id=role_id, 
            role_name=new_name
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully updated role {role_id} with name {new_name}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1
    
    def test_evm_update_group(self, evm_sdk, group_id, group_name):
        """Test creating then updating a group name on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the group
        create_result = sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt.status == 1
        
        # Then update it
        new_name = f"updated-{group_name}"
        result = sdk.rbac.update_group(
            group_id=group_id, 
            group_name=new_name
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully updated group {group_id} with name {new_name}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1
    
    def test_evm_update_permission(self, evm_sdk, permission_id, permission_name):
        """Test creating then updating a permission name on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the permission
        create_result = sdk.rbac.create_permission(permission_name=permission_name, permission_id=permission_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt.status == 1
        
        # Then update it
        new_name = f"updated-{permission_name}"
        result = sdk.rbac.update_permission(
            permission_id=permission_id, 
            permission_name=new_name
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully updated permission {permission_id} with name {new_name}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1

class TestRBACDisableOperations:
    """Test disable operations for roles, groups, and permissions."""
    
    def test_substrate_disable_role(self, substrate_sdk, role_id, role_name):
        """Test creating then disabling a role on Substrate."""
        # First create the role
        create_result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then disable it
        result = substrate_sdk.rbac.disable_role(role_id=role_id)
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully disabled role {role_id}" in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_substrate_disable_group(self, substrate_sdk, group_id, group_name):
        """Test creating then disabling a group on Substrate."""
        # First create the group
        create_result = substrate_sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then disable it
        result = substrate_sdk.rbac.disable_group(group_id=group_id)
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully disabled group {group_id}" in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_substrate_disable_permission(self, substrate_sdk, permission_id, permission_name):
        """Test creating then disabling a permission on Substrate."""
        # First create the permission
        create_result = substrate_sdk.rbac.create_permission(permission_name=permission_name, permission_id=permission_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then disable it
        result = substrate_sdk.rbac.disable_permission(permission_id=permission_id)
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully disabled permission {permission_id}" in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_evm_disable_role(self, evm_sdk, role_id, role_name):
        """Test creating then disabling a role on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the role
        create_result = sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt.status == 1
        
        # Then disable it
        result = sdk.rbac.disable_role(role_id=role_id)
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully disabled role {role_id}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1
    
    def test_evm_disable_group(self, evm_sdk, group_id, group_name):
        """Test creating then disabling a group on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the group
        create_result = sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt.status == 1
        
        # Then disable it
        result = sdk.rbac.disable_group(group_id=group_id)
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully disabled group {group_id}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1
    
    def test_evm_disable_permission(self, evm_sdk, permission_id, permission_name):
        """Test creating then disabling a permission on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the permission
        create_result = sdk.rbac.create_permission(permission_name=permission_name, permission_id=permission_id)
        assert isinstance(create_result, WrittenTransactionResult)
        assert create_result.receipt.status == 1
        
        # Then disable it
        result = sdk.rbac.disable_permission(permission_id=permission_id)
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully disabled permission {permission_id}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1

class TestRBACUnassignmentOperations:
    """Test unassignment operations."""
    
    def test_substrate_unassign_permission_to_role(self, substrate_sdk, permission_name, permission_id, role_name, role_id):
        """Test creating, assigning, then unassigning a permission from a role on Substrate."""
        # First create the permission and role
        permission_result = substrate_sdk.rbac.create_permission(permission_name=permission_name, permission_id=permission_id)
        assert isinstance(permission_result, WrittenTransactionResult)
        assert permission_result.receipt['_ExtrinsicReceipt__is_success']
        
        role_result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(role_result, WrittenTransactionResult)
        assert role_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then assign permission to role
        assign_result = substrate_sdk.rbac.assign_permission_to_role(permission_id=permission_id, role_id=role_id)
        assert isinstance(assign_result, WrittenTransactionResult)
        assert assign_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Finally unassign
        result = substrate_sdk.rbac.unassign_permission_to_role(
            permission_id=permission_id, 
            role_id=role_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully unassigned permission {permission_id} from role {role_id}" in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_substrate_unassign_role_to_group(self, substrate_sdk, role_name, role_id, group_name, group_id):
        """Test creating, assigning, then unassigning a role from a group on Substrate."""
        # First create the role and group
        role_result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(role_result, WrittenTransactionResult)
        assert role_result.receipt['_ExtrinsicReceipt__is_success']
        
        group_result = substrate_sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(group_result, WrittenTransactionResult)
        assert group_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then assign role to group
        assign_result = substrate_sdk.rbac.assign_role_to_group(role_id=role_id, group_id=group_id)
        assert isinstance(assign_result, WrittenTransactionResult)
        assert assign_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Finally unassign
        result = substrate_sdk.rbac.unassign_role_to_group(
            role_id=role_id, 
            group_id=group_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully unassigned role {role_id} from group {group_id}" in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_substrate_unassign_role_to_user(self, substrate_sdk, role_name, role_id, user_id):
        """Test creating, assigning, then unassigning a role from a user on Substrate."""
        # First create the role
        role_result = substrate_sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(role_result, WrittenTransactionResult)
        assert role_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then assign role to user
        assign_result = substrate_sdk.rbac.assign_role_to_user(role_id=role_id, user_id=user_id)
        assert isinstance(assign_result, WrittenTransactionResult)
        assert assign_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Finally unassign
        result = substrate_sdk.rbac.unassign_role_to_user(
            role_id=role_id, 
            user_id=user_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully unassigned role {role_id} from user {user_id}" in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_substrate_unassign_user_to_group(self, substrate_sdk, user_id, group_name, group_id):
        """Test creating, assigning, then unassigning a user from a group on Substrate."""
        # First create the group
        group_result = substrate_sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(group_result, WrittenTransactionResult)
        assert group_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Then assign user to group
        assign_result = substrate_sdk.rbac.assign_user_to_group(user_id=user_id, group_id=group_id)
        assert isinstance(assign_result, WrittenTransactionResult)
        assert assign_result.receipt['_ExtrinsicReceipt__is_success']
        
        # Finally unassign
        result = substrate_sdk.rbac.unassign_user_to_group(
            user_id=user_id, 
            group_id=group_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully unassigned user {user_id} from group {group_id}" in result.message
        assert 'extrinsic_hash' in result.receipt
        assert result.receipt['_ExtrinsicReceipt__is_success']
    
    def test_evm_unassign_permission_to_role(self, evm_sdk, permission_name, permission_id, role_name, role_id):
        """Test creating, assigning, then unassigning a permission from a role on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the permission and role
        permission_result = sdk.rbac.create_permission(permission_name=permission_name, permission_id=permission_id)
        assert isinstance(permission_result, WrittenTransactionResult)
        assert permission_result.receipt.status == 1
        
        role_result = sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(role_result, WrittenTransactionResult)
        assert role_result.receipt.status == 1
        
        # Then assign permission to role
        assign_result = sdk.rbac.assign_permission_to_role(permission_id=permission_id, role_id=role_id)
        assert isinstance(assign_result, WrittenTransactionResult)
        assert assign_result.receipt.status == 1
        
        # Finally unassign
        result = sdk.rbac.unassign_permission_to_role(
            permission_id=permission_id, 
            role_id=role_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully unassigned permission {permission_id} from role {role_id}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1
    
    def test_evm_unassign_role_to_group(self, evm_sdk, role_name, role_id, group_name, group_id):
        """Test creating, assigning, then unassigning a role from a group on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the role and group
        role_result = sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(role_result, WrittenTransactionResult)
        assert role_result.receipt.status == 1
        
        group_result = sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(group_result, WrittenTransactionResult)
        assert group_result.receipt.status == 1
        
        # Then assign role to group
        assign_result = sdk.rbac.assign_role_to_group(role_id=role_id, group_id=group_id)
        assert isinstance(assign_result, WrittenTransactionResult)
        assert assign_result.receipt.status == 1
        
        # Finally unassign
        result = sdk.rbac.unassign_role_to_group(
            role_id=role_id, 
            group_id=group_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully unassigned role {role_id} from group {group_id}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1
    
    def test_evm_unassign_role_to_user(self, evm_sdk, role_name, role_id, user_id):
        """Test creating, assigning, then unassigning a role from a user on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the role
        role_result = sdk.rbac.create_role(role_name=role_name, role_id=role_id)
        assert isinstance(role_result, WrittenTransactionResult)
        assert role_result.receipt.status == 1
        
        # Then assign role to user
        assign_result = sdk.rbac.assign_role_to_user(role_id=role_id, user_id=user_id)
        assert isinstance(assign_result, WrittenTransactionResult)
        assert assign_result.receipt.status == 1
        
        # Finally unassign
        result = sdk.rbac.unassign_role_to_user(
            role_id=role_id, 
            user_id=user_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully unassigned role {role_id} from user {user_id}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1
    
    def test_evm_unassign_user_to_group(self, evm_sdk, user_id, group_name, group_id):
        """Test creating, assigning, then unassigning a user from a group on EVM."""
        sdk, base_wss = evm_sdk
        
        # First create the group
        group_result = sdk.rbac.create_group(group_name=group_name, group_id=group_id)
        assert isinstance(group_result, WrittenTransactionResult)
        assert group_result.receipt.status == 1
        
        # Then assign user to group
        assign_result = sdk.rbac.assign_user_to_group(user_id=user_id, group_id=group_id)
        assert isinstance(assign_result, WrittenTransactionResult)
        assert assign_result.receipt.status == 1
        
        # Finally unassign
        result = sdk.rbac.unassign_user_to_group(
            user_id=user_id, 
            group_id=group_id
        )
        assert isinstance(result, WrittenTransactionResult)
        assert f"Successfully unassigned user {user_id} from group {group_id}" in result.message
        assert hasattr(result.receipt, "transactionHash")
        assert result.receipt.status == 1

class TestRBACValidation:
    """Test input validation and error handling."""
    
    def test_invalid_role_id_length(self, substrate_sdk):
        """Test that invalid role ID length raises ValueError."""
        with pytest.raises(ValueError, match="Role Id length should be 32 char only"):
            substrate_sdk.rbac.create_role(role_name="test", role_id="short")
    
    def test_invalid_group_id_length(self, substrate_sdk):
        """Test that invalid group ID length raises ValueError."""
        with pytest.raises(ValueError, match="Group Id length should be 32 char only"):
            substrate_sdk.rbac.create_group(group_name="test", group_id="short")
    
    def test_invalid_permission_id_length(self, substrate_sdk):
        """Test that invalid permission ID length raises ValueError."""
        with pytest.raises(ValueError, match="Permission Id length should be 32 char only"):
            substrate_sdk.rbac.create_permission(permission_name="test", permission_id="short")
    
    def test_fetch_nonexistent_role_substrate(self, substrate_sdk, config):
        """Test fetching a non-existent role raises GetRbacError."""
        with pytest.raises(GetRbacError, match="Role id.*was not found"):
            substrate_sdk.rbac.fetch_role(
                owner=config['SUBSTRATE_ADDRESS'], 
                role_id="nonexistent-role-id-123456789012"
            )
    
    def test_fetch_nonexistent_role_evm(self, evm_sdk, config):
        """Test fetching a non-existent role raises GetRbacError on EVM."""
        sdk, base_wss = evm_sdk
        with pytest.raises(GetRbacError, match="Role id.*was not found"):
            sdk.rbac.fetch_role(
                owner=config['EVM_ADDRESS'], 
                role_id="nonexistent-role-id-123456789012",
                wss_base_url=base_wss
            )

class TestRBACIntegration:
    """Integration tests that combine multiple RBAC operations."""
    
    def test_substrate_full_rbac_workflow(self, substrate_sdk, config):
        """Test a complete RBAC workflow on Substrate: create -> assign -> fetch -> unassign -> disable."""
        # Create entities
        role_result = substrate_sdk.rbac.create_role(role_name="integration-role")
        group_result = substrate_sdk.rbac.create_group(group_name="integration-group")
        permission_result = substrate_sdk.rbac.create_permission(permission_name="integration-permission")
        
        # Extract IDs from messages (you might need to adjust this based on actual implementation)
        import re
        role_id = role_result.message.split("role id of ")[-1].split(".")[0]
        group_id = group_result.message.split("group id of ")[-1].split(".")[0]
        permission_id = permission_result.message.split("permission id of ")[-1].split(".")[0]
        user_id = "integration-test-user-id-123456"  # Exactly 32 chars
        
        # Test assignments
        substrate_sdk.rbac.assign_permission_to_role(permission_id=permission_id, role_id=role_id)
        substrate_sdk.rbac.assign_role_to_group(role_id=role_id, group_id=group_id)
        substrate_sdk.rbac.assign_role_to_user(role_id=role_id, user_id=user_id)
        substrate_sdk.rbac.assign_user_to_group(user_id=user_id, group_id=group_id)
        
        # Test fetch operations
        fetched_role = substrate_sdk.rbac.fetch_role(owner=config['SUBSTRATE_ADDRESS'], role_id=role_id)
        fetched_group = substrate_sdk.rbac.fetch_group(owner=config['SUBSTRATE_ADDRESS'], group_id=group_id)
        fetched_permission = substrate_sdk.rbac.fetch_permission(owner=config['SUBSTRATE_ADDRESS'], permission_id=permission_id)
        
        assert fetched_role.name == "integration-role"
        assert fetched_group.name == "integration-group"
        assert fetched_permission.name == "integration-permission"
        
        # Test updates
        substrate_sdk.rbac.update_role(role_id=role_id, role_name="updated-integration-role")
        substrate_sdk.rbac.update_group(group_id=group_id, group_name="updated-integration-group")
        substrate_sdk.rbac.update_permission(permission_id=permission_id, permission_name="updated-integration-permission")
        
        # Test unassignments
        substrate_sdk.rbac.unassign_permission_to_role(permission_id=permission_id, role_id=role_id)
        substrate_sdk.rbac.unassign_role_to_group(role_id=role_id, group_id=group_id)
        substrate_sdk.rbac.unassign_role_to_user(role_id=role_id, user_id=user_id)
        substrate_sdk.rbac.unassign_user_to_group(user_id=user_id, group_id=group_id)
        
        # Test disable operations
        substrate_sdk.rbac.disable_role(role_id=role_id)
        substrate_sdk.rbac.disable_group(group_id=group_id)
        substrate_sdk.rbac.disable_permission(permission_id=permission_id)
    
    def test_evm_full_rbac_workflow(self, evm_sdk, config):
        """Test a complete RBAC workflow on EVM: create -> assign -> fetch -> unassign -> disable."""
        sdk, base_wss = evm_sdk
        
        # Create entities
        role_result = sdk.rbac.create_role(role_name="integration-role")
        group_result = sdk.rbac.create_group(group_name="integration-group")
        permission_result = sdk.rbac.create_permission(permission_name="integration-permission")
        
        # Extract IDs from messages
        role_id = role_result.message.split("role id of ")[-1].split(".")[0]
        group_id = group_result.message.split("group id of ")[-1].split(".")[0]
        permission_id = permission_result.message.split("permission id of ")[-1].split(".")[0]
        user_id = "integration-test-user-id-123456"  # Exactly 32 chars
        
        # Test assignments
        sdk.rbac.assign_permission_to_role(permission_id=permission_id, role_id=role_id)
        sdk.rbac.assign_role_to_group(role_id=role_id, group_id=group_id)
        sdk.rbac.assign_role_to_user(role_id=role_id, user_id=user_id)
        sdk.rbac.assign_user_to_group(user_id=user_id, group_id=group_id)
        
        # Test fetch operations
        fetched_role = sdk.rbac.fetch_role(owner=config['EVM_ADDRESS'], role_id=role_id, wss_base_url=base_wss)
        fetched_group = sdk.rbac.fetch_group(owner=config['EVM_ADDRESS'], group_id=group_id, wss_base_url=base_wss)
        fetched_permission = sdk.rbac.fetch_permission(owner=config['EVM_ADDRESS'], permission_id=permission_id, wss_base_url=base_wss)
        
        assert fetched_role.name == "integration-role"
        assert fetched_group.name == "integration-group"
        assert fetched_permission.name == "integration-permission"
        
        # Test updates
        sdk.rbac.update_role(role_id=role_id, role_name="updated-integration-role")
        sdk.rbac.update_group(group_id=group_id, group_name="updated-integration-group")
        sdk.rbac.update_permission(permission_id=permission_id, permission_name="updated-integration-permission")
        
        # Test unassignments
        sdk.rbac.unassign_permission_to_role(permission_id=permission_id, role_id=role_id)
        sdk.rbac.unassign_role_to_group(role_id=role_id, group_id=group_id)
        sdk.rbac.unassign_role_to_user(role_id=role_id, user_id=user_id)
        sdk.rbac.unassign_user_to_group(user_id=user_id, group_id=group_id)
        
        # Test disable operations
        sdk.rbac.disable_role(role_id=role_id)
        sdk.rbac.disable_group(group_id=group_id)
        sdk.rbac.disable_permission(permission_id=permission_id)