from typing import Optional, List
import uuid

from peaq_sdk.base import Base
from peaq_sdk.types.base import TxOptions, StatusCallback
from peaq_sdk.utils.utils import parse_options
from peaq_sdk.types.common import (
    ChainType,
    SDKMetadata,
    PrecompileAddresses,
    BuiltEvmTransactionResult,
    CallModule,
    BuiltCallTransactionResult,
    BaseUrlError
)
from peaq_sdk.types.rbac import (
    RbacCallFunction,
    RbacFunctionSignatures,
    GetRbacError,
    FetchResponseData,
    FetchResponseRole2Permission,
    FetchResponseRole2Group,
    FetchResponseRole2User,
    ResponseFetchUserGroups,
    CreateRoleOptions,
    CreateGroupOptions,
    CreatePermissionOptions,
    AssignPermissionToRoleOptions,
    AssignRoleToGroupOptions,
    AssignRoleToUserOptions,
    AssignUserToGroupOptions,
    DisableRoleOptions,
    DisableGroupOptions,
    DisablePermissionOptions,
    UpdateRoleOptions,
    UpdateGroupOptions,
    UpdatePermissionOptions,
    UnassignPermissionToRoleOptions,
    UnassignRoleToGroupOptions,
    UnassignRoleToUserOptions,
    UnassignUserToGroupOptions,
    FetchRoleOptions,
    FetchGroupOptions,
    FetchPermissionOptions,
    FetchRolesOptions,
    FetchGroupsOptions,
    FetchPermissionsOptions,
    FetchUserRolesOptions,
    FetchGroupRolesOptions,
    FetchUserGroupsOptions,
    FetchRolePermissionsOptions,
    FetchUserPermissionsOptions,
    FetchGroupPermissionsOptions
)

from peaq_sdk.utils.utils import evm_to_address

# 3rd party imports
from substrateinterface.base import SubstrateInterface
from web3 import Web3
from web3.types import TxParams
from eth_abi import encode


class Rbac(Base):
    """
    Provides methods to interact with the peaq on-chain RBAC precompile (EVM)
    or pallet (Substrate). Supports role, group, and permission operations.
    """
    def __init__(self, api: Web3 | SubstrateInterface, metadata: SDKMetadata) -> None:
        """
        Initializes RBAC with a connected API instance and shared SDK metadata.

        Args:
            api (Web3 | SubstrateInterface): The blockchain API connection.
                which may be a Web3 (EVM) or SubstrateInterface (Substrate).
            metadata (SDKMetadata): Shared metadata, including chain type,
                and optional signer.
        """
        super().__init__(api, metadata)
        
    async def create_role(
        self, 
        options: CreateRoleOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        ops = parse_options(CreateRoleOptions, options, caller="rbac.create_role()")
        
        role_name = ops.role_name
        role_id = ops.role_id
        
        if role_id is None:
            role_id = str(uuid.uuid4())[:32]
        elif len(role_id) != 32:
            raise ValueError("Role Id length should be 32 char only")
        
        role_id_bytes = role_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.ADD_ROLE.value)[:4].hex()
            role_name_encoded = role_name.encode("utf-8").hex()
            encoded_params = encode(
                ['bytes32', 'bytes'],
                [bytes.fromhex(role_id_bytes.hex()), bytes.fromhex(role_name_encoded)]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"create RBAC role {role_name}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ADD_ROLE.value,
                call_params={
                    'role_id': role_id_bytes,
                    'name': role_name
                    }
            )
            return self._handle_substrate_tx(call, f"create RBAC role {role_name}", status_callback)

    

    async def create_group(
        self, 
        options: CreateGroupOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Creates a new group of the given name at the group id."""
        ops = parse_options(CreateGroupOptions, options, caller="rbac.create_group()")
        
        group_name = ops.group_name
        group_id = ops.group_id
        
        if group_id is None:
            group_id = str(uuid.uuid4())[:32]
        elif len(group_id) != 32:
            raise ValueError("Group Id length should be 32 char only")
        
        group_id_bytes = group_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.ADD_GROUP.value)[:4].hex()
            group_name_encoded = group_name.encode("utf-8").hex()
            encoded_params = encode(
                ['bytes32', 'bytes'],
                [bytes.fromhex(group_id_bytes.hex()), bytes.fromhex(group_name_encoded)]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"create RBAC group {group_name}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ADD_GROUP.value,
                call_params={
                    'group_id': group_id_bytes,
                    'name': group_name
                    }
            )
            return self._handle_substrate_tx(call, f"create RBAC group {group_name}", status_callback)

    async def create_permission(
        self, 
        options: CreatePermissionOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Creates a new permission of the given name at the permission id."""
        ops = parse_options(CreatePermissionOptions, options, caller="rbac.create_permission()")
        
        permission_name = ops.permission_name
        permission_id = ops.permission_id
        
        if permission_id is None:
            permission_id = str(uuid.uuid4())[:32]
        elif len(permission_id) != 32:
            raise ValueError("Permission Id length should be 32 char only")
        
        permission_id_bytes = permission_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.ADD_PERMISSION.value)[:4].hex()
            permission_name_encoded = permission_name.encode("utf-8").hex()
            encoded_params = encode(
                ['bytes32', 'bytes'],
                [bytes.fromhex(permission_id_bytes.hex()), bytes.fromhex(permission_name_encoded)]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"create RBAC permission {permission_name}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ADD_PERMISSION.value,
                call_params={
                    'permission_id': permission_id_bytes,
                    'name': permission_name
                    }
            )
            return self._handle_substrate_tx(call, f"create RBAC permission {permission_name}", status_callback)

    async def assign_permission_to_role(
        self, 
        options: AssignPermissionToRoleOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Assigns a permission to a role."""
        ops = parse_options(AssignPermissionToRoleOptions, options, caller="rbac.assign_permission_to_role()")
        
        permission_id = ops.permission_id
        role_id = ops.role_id
        
        if len(permission_id) != 32:
            raise ValueError("Permission Id length should be 32 char only")
        if len(role_id) != 32:
            raise ValueError("Role Id length should be 32 char only")
        
        permission_id_bytes = permission_id.encode()
        role_id_bytes = role_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.ASSIGN_PERMISSION_TO_ROLE.value)[:4].hex()
            encoded_params = encode(
                ['bytes32', 'bytes32'],
                [bytes.fromhex(permission_id_bytes.hex()), bytes.fromhex(role_id_bytes.hex())]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"assign permission {permission_id} to role {role_id}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ASSIGN_PERMISSION_TO_ROLE.value,
                call_params={
                    'permission_id': permission_id_bytes,
                    'role_id': role_id_bytes
                    }
            )
            return self._handle_substrate_tx(call, f"assign permission {permission_id} to role {role_id}", status_callback)

    async def assign_role_to_group(
        self, 
        options: AssignRoleToGroupOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Assigns a role to a group."""
        ops = parse_options(AssignRoleToGroupOptions, options, caller="rbac.assign_role_to_group()")
        
        role_id = ops.role_id
        group_id = ops.group_id
        
        if len(role_id) != 32:
            raise ValueError("Role Id length should be 32 char only")
        if len(group_id) != 32:
            raise ValueError("Group Id length should be 32 char only")
        
        role_id_bytes = role_id.encode()
        group_id_bytes = group_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.ASSIGN_ROLE_TO_GROUP.value)[:4].hex()
            encoded_params = encode(
                ['bytes32', 'bytes32'],
                [bytes.fromhex(role_id_bytes.hex()), bytes.fromhex(group_id_bytes.hex())]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"assign role {role_id} to group {group_id}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ASSIGN_ROLE_TO_GROUP.value,
                call_params={
                    'role_id': role_id_bytes,
                    'group_id': group_id_bytes
                    }
            )
            return self._handle_substrate_tx(call, f"assign role {role_id} to group {group_id}", status_callback)

    async def assign_role_to_user(
        self, 
        options: AssignRoleToUserOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Assigns a role to a user."""
        ops = parse_options(AssignRoleToUserOptions, options, caller="rbac.assign_role_to_user()")
        
        role_id = ops.role_id
        user_id = ops.user_id
        
        if len(role_id) != 32:
            raise ValueError("Role Id length should be 32 char only")
        if len(user_id) != 32:
            raise ValueError("User Id length should be 32 char only")
        
        role_id_bytes = role_id.encode()
        user_id_bytes = user_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.ASSIGN_ROLE_TO_USER.value)[:4].hex()
            encoded_params = encode(
                ['bytes32', 'bytes32'],
                [bytes.fromhex(role_id_bytes.hex()), bytes.fromhex(user_id_bytes.hex())]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"assign role {role_id} to user {user_id}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ASSIGN_ROLE_TO_USER.value,
                call_params={
                    'role_id': role_id_bytes,
                    'user_id': user_id_bytes
                    }
            )
            return self._handle_substrate_tx(call, f"assign role {role_id} to user {user_id}", status_callback)

    async def assign_user_to_group(
        self, 
        options: AssignUserToGroupOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Assigns a user to a group."""
        ops = parse_options(AssignUserToGroupOptions, options, caller="rbac.assign_user_to_group()")
        
        user_id = ops.user_id
        group_id = ops.group_id
        
        if len(user_id) != 32:
            raise ValueError("User Id length should be 32 char only")
        if len(group_id) != 32:
            raise ValueError("Group Id length should be 32 char only")
        
        user_id_bytes = user_id.encode()
        group_id_bytes = group_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.ASSIGN_USER_TO_GROUP.value)[:4].hex()
            encoded_params = encode(
                ['bytes32', 'bytes32'],
                [bytes.fromhex(user_id_bytes.hex()), bytes.fromhex(group_id_bytes.hex())]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"assign user {user_id} to group {group_id}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ASSIGN_USER_TO_GROUP.value,
                call_params={
                    'user_id': user_id_bytes,
                    'group_id': group_id_bytes
                    }
            )
            return self._handle_substrate_tx(call, f"assign user {user_id} to group {group_id}", status_callback)
                
    def fetch_role(self, options: FetchRoleOptions) -> FetchResponseData:
        ops = parse_options(FetchRoleOptions, options, caller="rbac.fetch_role()")
        
        owner = ops.owner
        role_id = ops.role_id
        
        if self.metadata.chain_type is ChainType.EVM:
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
        else:
            api = self.api
            owner_address = owner
        
        # Query storage
        role_id_bytes = _rpc_id(role_id)
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            RbacCallFunction.GET_ROLE.value, [owner_address, role_id_bytes, block_hash]
        )
        
        # Check result
        if 'Err' in resp['result']:
            raise GetRbacError(f"Role id of {role_id} was not found at the owner address of {owner}.") 
        
        ok = resp['result']['Ok']
        role_id_str   = bytes(ok['id']).decode('utf-8')
        role_name_str = bytes(ok['name']).decode('utf-8')
        
        return FetchResponseData(
            id=role_id_str,
            name=role_name_str,
            enabled=ok['enabled']
        )

    def fetch_group(self, options: FetchGroupOptions) -> FetchResponseData:
        """Fetches a group by owner and group id."""
        ops = parse_options(FetchGroupOptions, options, caller="rbac.fetch_group()")
        
        owner = ops.owner
        group_id = ops.group_id
        
        if self.metadata.chain_type is ChainType.EVM:
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
        else:
            api = self.api
            owner_address = owner
        
        # Query storage
        group_id_bytes = _rpc_id(group_id)
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            RbacCallFunction.GET_GROUP.value, [owner_address, group_id_bytes, block_hash]
        )
        
        # Check result
        if 'Err' in resp['result']:
            raise GetRbacError(f"Group id of {group_id} was not found at the owner address of {owner}.") 
        
        ok = resp['result']['Ok']
        group_id_str = bytes(ok['id']).decode('utf-8')
        group_name_str = bytes(ok['name']).decode('utf-8')
        
        return FetchResponseData(
            id=group_id_str,
            name=group_name_str,
            enabled=ok['enabled']
        )

    def fetch_permission(self, options: FetchPermissionOptions) -> FetchResponseData:
        """Fetches a permission by owner and permission id."""
        ops = parse_options(FetchPermissionOptions, options, caller="rbac.fetch_permission()")
        
        owner = ops.owner
        permission_id = ops.permission_id
        
        if self.metadata.chain_type is ChainType.EVM:
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
        else:
            api = self.api
            owner_address = owner
        
        # Query storage
        permission_id_bytes = _rpc_id(permission_id)
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            RbacCallFunction.GET_PERMISSION.value, [owner_address, permission_id_bytes, block_hash]
        )
        
        # Check result
        if 'Err' in resp['result']:
            raise GetRbacError(f"Permission id of {permission_id} was not found at the owner address of {owner}.") 
        
        ok = resp['result']['Ok']
        permission_id_str = bytes(ok['id']).decode('utf-8')
        permission_name_str = bytes(ok['name']).decode('utf-8')
        
        return FetchResponseData(
            id=permission_id_str,
            name=permission_name_str,
            enabled=ok['enabled']
        )

    def fetch_roles(self, options: FetchRolesOptions) -> List[FetchResponseData]:
        """Fetches all roles for the given owner."""
        ops = parse_options(FetchRolesOptions, options, caller="rbac.fetch_roles()")
        
        owner = ops.owner
        
        if self.metadata.chain_type is ChainType.EVM:
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
        else:
            api = self.api
            owner_address = owner
        
        # Query storage using RPC request
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            RbacCallFunction.GET_ROLES.value, [owner_address, block_hash]
        )
        
        # Check result
        if 'Err' in resp['result']:
            raise GetRbacError(f"Roles not found for owner address {owner}.")
        
        roles_data = resp['result']['Ok']
        response_data = []
        
        for role in roles_data:
            response_data.append(FetchResponseData(
                id=bytes(role['id']).decode('utf-8'),
                name=bytes(role['name']).decode('utf-8'),
                enabled=role['enabled']
            ))
        
        return response_data

    def fetch_groups(self, options: FetchGroupsOptions) -> List[FetchResponseData]:
        """Fetches all groups for the given owner."""
        ops = parse_options(FetchGroupsOptions, options, caller="rbac.fetch_groups()")
        
        owner = ops.owner
        
        if self.metadata.chain_type is ChainType.EVM:
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
        else:
            api = self.api
            owner_address = owner
        
        # Query storage using RPC request
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            RbacCallFunction.GET_GROUPS.value, [owner_address, block_hash]
        )
        
        # Check result
        if 'Err' in resp['result']:
            raise GetRbacError(f"Groups not found for owner address {owner}.")
        
        groups_data = resp['result']['Ok']
        response_data = []
        
        for group in groups_data:
            response_data.append(FetchResponseData(
                id=bytes(group['id']).decode('utf-8'),
                name=bytes(group['name']).decode('utf-8'),
                enabled=group['enabled']
            ))
        
        return response_data

    def fetch_permissions(self, options: FetchPermissionsOptions) -> List[FetchResponseData]:
        """Fetches all permissions for the given owner."""
        ops = parse_options(FetchPermissionsOptions, options, caller="rbac.fetch_permissions()")
        
        owner = ops.owner
        
        if self.metadata.chain_type is ChainType.EVM:
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
        else:
            api = self.api
            owner_address = owner
        
        # Query storage using RPC request
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            RbacCallFunction.GET_PERMISSIONS.value, [owner_address, block_hash]
        )
        
        # Check result
        if 'Err' in resp['result']:
            raise GetRbacError(f"Permissions not found for owner address {owner}.")
        
        permissions_data = resp['result']['Ok']
        response_data = []
        
        for permission in permissions_data:
            response_data.append(FetchResponseData(
                id=bytes(permission['id']).decode('utf-8'),
                name=bytes(permission['name']).decode('utf-8'),
                enabled=permission['enabled']
            ))
        
        return response_data

    def fetch_user_roles(self, options: FetchUserRolesOptions) -> List[FetchResponseRole2User]:
        """Fetches all roles assigned to a user."""
        ops = parse_options(FetchUserRolesOptions, options, caller="rbac.fetch_user_roles()")
        
        owner = ops.owner
        user_id = ops.user_id
        
        if len(user_id) != 32:
            raise GetRbacError("User Id length should be 32 char only")
            
        if self.metadata.chain_type is ChainType.EVM:
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
        else:
            api = self.api
            owner_address = owner
        
        # Query storage using RPC request
        user_id_bytes = _rpc_id(user_id)
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            RbacCallFunction.GET_USER_ROLES.value, [owner_address, user_id_bytes, block_hash]
        )
        
        # Check result
        if 'Err' in resp['result']:
            raise GetRbacError(f"No role is assigned to user {user_id}.")
        
        user_roles_data = resp['result']['Ok']
        response_data = []
        
        for item in user_roles_data:
            response_data.append(FetchResponseRole2User(
                role=bytes(item['role']).decode('utf-8'),
                user=bytes(item['user']).decode('utf-8')
            ))
        
        return response_data

    def fetch_group_roles(self, options: FetchGroupRolesOptions) -> List[FetchResponseRole2Group]:
        """Fetches all roles assigned to a group."""
        ops = parse_options(FetchGroupRolesOptions, options, caller="rbac.fetch_group_roles()")
        
        owner = ops.owner
        group_id = ops.group_id
        
        if len(group_id) != 32:
            raise GetRbacError("Group Id length should be 32 char only")
            
        if self.metadata.chain_type is ChainType.EVM:
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
        else:
            api = self.api
            owner_address = owner
        
        # Query storage using RPC request
        group_id_bytes = _rpc_id(group_id)
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            RbacCallFunction.GET_GROUP_ROLES.value, [owner_address, group_id_bytes, block_hash]
        )
        
        # Check result
        if 'Err' in resp['result']:
            raise GetRbacError(f"No roles found for group {group_id}.")
        
        group_roles_data = resp['result']['Ok']
        response_data = []
        
        for item in group_roles_data:
            response_data.append(FetchResponseRole2Group(
                role=bytes(item['role']).decode('utf-8'),
                group=bytes(item['group']).decode('utf-8')
            ))
        
        return response_data

    def fetch_user_groups(self, options: FetchUserGroupsOptions) -> List[ResponseFetchUserGroups]:
        """Fetches all groups assigned to a user."""
        ops = parse_options(FetchUserGroupsOptions, options, caller="rbac.fetch_user_groups()")
        
        owner = ops.owner
        user_id = ops.user_id
        
        if len(user_id) != 32:
            raise GetRbacError("User Id length should be 32 char only")
            
        if self.metadata.chain_type is ChainType.EVM:
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
        else:
            api = self.api
            owner_address = owner
        
        # Query storage using RPC request
        user_id_bytes = _rpc_id(user_id)
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            RbacCallFunction.GET_USER_GROUPS.value, [owner_address, user_id_bytes, block_hash]
        )
        
        # Check result
        if 'Err' in resp['result']:
            raise GetRbacError(f"No groups assigned to user {user_id}.")
        
        user_groups_data = resp['result']['Ok']
        response_data = []
        
        for item in user_groups_data:
            response_data.append(ResponseFetchUserGroups(
                user=bytes(item['user']).decode('utf-8'),
                group=bytes(item['group']).decode('utf-8')
            ))
        
        return response_data

    def fetch_role_permissions(self, options: FetchRolePermissionsOptions) -> List[FetchResponseRole2Permission]:
        """Fetches all permissions assigned to a role."""
        ops = parse_options(FetchRolePermissionsOptions, options, caller="rbac.fetch_role_permissions()")
        
        owner = ops.owner
        role_id = ops.role_id
        
        if len(role_id) != 32:
            raise GetRbacError("Role Id length should be 32 char only")
            
        if self.metadata.chain_type is ChainType.EVM:
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
        else:
            api = self.api
            owner_address = owner
        
        # Query storage using RPC request
        role_id_bytes = _rpc_id(role_id)
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            RbacCallFunction.GET_ROLE_PERMISSIONS.value, [owner_address, role_id_bytes, block_hash]
        )
        
        # Check result
        if 'Err' in resp['result']:
            raise GetRbacError(f"No permissions found for role {role_id}.")
        
        role_permissions_data = resp['result']['Ok']
        response_data = []
        
        for item in role_permissions_data:
            response_data.append(FetchResponseRole2Permission(
                permission=bytes(item['permission']).decode('utf-8'),
                role=bytes(item['role']).decode('utf-8')
            ))
        
        return response_data

    def fetch_user_permissions(self, options: FetchUserPermissionsOptions) -> List[FetchResponseData]:
        """Fetches all permissions available to a user (through direct role assignments and group memberships)."""
        ops = parse_options(FetchUserPermissionsOptions, options, caller="rbac.fetch_user_permissions()")
        
        owner = ops.owner
        user_id = ops.user_id
        
        if len(user_id) != 32:
            raise GetRbacError("User Id length should be 32 char only")
            
        if self.metadata.chain_type is ChainType.EVM:
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
        else:
            api = self.api
            owner_address = owner
        
        # Query storage using RPC request
        user_id_bytes = _rpc_id(user_id)
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            RbacCallFunction.GET_USER_PERMISSIONS.value, [owner_address, user_id_bytes, block_hash]
        )
        
        # Check result
        if 'Err' in resp['result']:
            raise GetRbacError(f"No permissions found for user {user_id}.")
        
        user_permissions_data = resp['result']['Ok']
        response_data = []
        
        for permission in user_permissions_data:
            response_data.append(FetchResponseData(
                id=bytes(permission['id']).decode('utf-8'),
                name=bytes(permission['name']).decode('utf-8'),
                enabled=permission['enabled']
            ))
        
        return response_data

    def fetch_group_permissions(self, options: FetchGroupPermissionsOptions) -> List[FetchResponseData]:
        """Fetches all permissions available to a group (through role assignments)."""
        ops = parse_options(FetchGroupPermissionsOptions, options, caller="rbac.fetch_group_permissions()")
        
        owner = ops.owner
        group_id = ops.group_id
        
        if len(group_id) != 32:
            raise GetRbacError("Group Id length should be 32 char only")
            
        if self.metadata.chain_type is ChainType.EVM:
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
        else:
            api = self.api
            owner_address = owner
        
        # Query storage using RPC request
        group_id_bytes = _rpc_id(group_id)
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            RbacCallFunction.GET_GROUP_PERMISSIONS.value, [owner_address, group_id_bytes, block_hash]
        )
        
        # Check result
        if 'Err' in resp['result']:
            raise GetRbacError(f"No permissions found for group {group_id}.")
        
        group_permissions_data = resp['result']['Ok']
        response_data = []
        
        for permission in group_permissions_data:
            response_data.append(FetchResponseData(
                id=bytes(permission['id']).decode('utf-8'),
                name=bytes(permission['name']).decode('utf-8'),
                enabled=permission['enabled']
            ))
        
        return response_data

    async def disable_role(
        self, 
        options: DisableRoleOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Disables a role."""
        ops = parse_options(DisableRoleOptions, options, caller="rbac.disable_role()")
        
        role_id = ops.role_id
        
        if len(role_id) != 32:
            raise ValueError("Role Id length should be 32 char only")
        
        role_id_bytes = role_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.DISABLE_ROLE.value)[:4].hex()
            encoded_params = encode(
                ['bytes32'],
                [bytes.fromhex(role_id_bytes.hex())]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"disable role {role_id}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.DISABLE_ROLE.value,
                call_params={'role_id': role_id_bytes}
            )
            return self._handle_substrate_tx(call, f"disable role {role_id}", status_callback)

    async def disable_group(
        self, 
        options: DisableGroupOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Disables a group."""
        ops = parse_options(DisableGroupOptions, options, caller="rbac.disable_group()")
        
        group_id = ops.group_id
        
        if len(group_id) != 32:
            raise ValueError("Group Id length should be 32 char only")
        
        group_id_bytes = group_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.DISABLE_GROUP.value)[:4].hex()
            encoded_params = encode(
                ['bytes32'],
                [bytes.fromhex(group_id_bytes.hex())]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"disable group {group_id}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.DISABLE_GROUP.value,
                call_params={'group_id': group_id_bytes}
            )
            return self._handle_substrate_tx(call, f"disable group {group_id}", status_callback)

    async def disable_permission(
        self, 
        options: DisablePermissionOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Disables a permission."""
        ops = parse_options(DisablePermissionOptions, options, caller="rbac.disable_permission()")
        
        permission_id = ops.permission_id
        
        if len(permission_id) != 32:
            raise ValueError("Permission Id length should be 32 char only")
        
        permission_id_bytes = permission_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.DISABLE_PERMISSION.value)[:4].hex()
            encoded_params = encode(
                ['bytes32'],
                [bytes.fromhex(permission_id_bytes.hex())]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"disable permission {permission_id}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.DISABLE_PERMISSION.value,
                call_params={'permission_id': permission_id_bytes}
            )
            return self._handle_substrate_tx(call, f"disable permission {permission_id}", status_callback)

    async def update_role(
        self, 
        options: UpdateRoleOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Updates a role name."""
        ops = parse_options(UpdateRoleOptions, options, caller="rbac.update_role()")
        
        role_id = ops.role_id
        role_name = ops.role_name
        
        if len(role_id) != 32:
            raise ValueError("Role Id length should be 32 char only")
        
        role_id_bytes = role_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.UPDATE_ROLE.value)[:4].hex()
            role_name_encoded = role_name.encode("utf-8").hex()
            encoded_params = encode(
                ['bytes32', 'bytes'],
                [bytes.fromhex(role_id_bytes.hex()), bytes.fromhex(role_name_encoded)]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"update role {role_id} with name {role_name}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UPDATE_ROLE.value,
                call_params={
                    'role_id': role_id_bytes,
                    'name': role_name
                }
            )
            return self._handle_substrate_tx(call, f"update role {role_id} with name {role_name}", status_callback)

    async def update_group(
        self, 
        options: UpdateGroupOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Updates a group name."""
        ops = parse_options(UpdateGroupOptions, options, caller="rbac.update_group()")
        
        group_id = ops.group_id
        group_name = ops.group_name
        
        if len(group_id) != 32:
            raise ValueError("Group Id length should be 32 char only")
        
        group_id_bytes = group_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.UPDATE_GROUP.value)[:4].hex()
            group_name_encoded = group_name.encode("utf-8").hex()
            encoded_params = encode(
                ['bytes32', 'bytes'],
                [bytes.fromhex(group_id_bytes.hex()), bytes.fromhex(group_name_encoded)]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"update group {group_id} with name {group_name}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UPDATE_GROUP.value,
                call_params={
                    'group_id': group_id_bytes,
                    'name': group_name
                }
            )
            return self._handle_substrate_tx(call, f"update group {group_id} with name {group_name}", status_callback)

    async def update_permission(
        self, 
        options: UpdatePermissionOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Updates a permission name."""
        ops = parse_options(UpdatePermissionOptions, options, caller="rbac.update_permission()")
        
        permission_id = ops.permission_id
        permission_name = ops.permission_name
        
        if len(permission_id) != 32:
            raise ValueError("Permission Id length should be 32 char only")
        
        permission_id_bytes = permission_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.UPDATE_PERMISSION.value)[:4].hex()
            permission_name_encoded = permission_name.encode("utf-8").hex()
            encoded_params = encode(
                ['bytes32', 'bytes'],
                [bytes.fromhex(permission_id_bytes.hex()), bytes.fromhex(permission_name_encoded)]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"update permission {permission_id} with name {permission_name}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UPDATE_PERMISSION.value,
                call_params={
                    'permission_id': permission_id_bytes,
                    'name': permission_name
                }
            )
            return self._handle_substrate_tx(call, f"update permission {permission_id} with name {permission_name}", status_callback)

    async def unassign_permission_to_role(
        self, 
        options: UnassignPermissionToRoleOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Unassigns a permission from a role."""
        ops = parse_options(UnassignPermissionToRoleOptions, options, caller="rbac.unassign_permission_to_role()")
        
        permission_id = ops.permission_id
        role_id = ops.role_id
        
        if len(permission_id) != 32:
            raise ValueError("Permission Id length should be 32 char only")
        if len(role_id) != 32:
            raise ValueError("Role Id length should be 32 char only")
        
        permission_id_bytes = permission_id.encode()
        role_id_bytes = role_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.UNASSIGN_PERMISSION_TO_ROLE.value)[:4].hex()
            encoded_params = encode(
                ['bytes32', 'bytes32'],
                [bytes.fromhex(permission_id_bytes.hex()), bytes.fromhex(role_id_bytes.hex())]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"unassign permission {permission_id} from role {role_id}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UNASSIGN_PERMISSION_TO_ROLE.value,
                call_params={
                    'permission_id': permission_id_bytes,
                    'role_id': role_id_bytes
                    }
            )
            return self._handle_substrate_tx(call, f"unassign permission {permission_id} from role {role_id}", status_callback)

    async def unassign_role_to_group(
        self, 
        options: UnassignRoleToGroupOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Unassigns a role from a group."""
        ops = parse_options(UnassignRoleToGroupOptions, options, caller="rbac.unassign_role_to_group()")
        
        role_id = ops.role_id
        group_id = ops.group_id
        
        if len(role_id) != 32:
            raise ValueError("Role Id length should be 32 char only")
        if len(group_id) != 32:
            raise ValueError("Group Id length should be 32 char only")
        
        role_id_bytes = role_id.encode()
        group_id_bytes = group_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.UNASSIGN_ROLE_TO_GROUP.value)[:4].hex()
            encoded_params = encode(
                ['bytes32', 'bytes32'],
                [bytes.fromhex(role_id_bytes.hex()), bytes.fromhex(group_id_bytes.hex())]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"unassign role {role_id} from group {group_id}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UNASSIGN_ROLE_TO_GROUP.value,
                call_params={
                    'role_id': role_id_bytes,
                    'group_id': group_id_bytes
                    }
            )
            return self._handle_substrate_tx(call, f"unassign role {role_id} from group {group_id}", status_callback)

    async def unassign_role_to_user(
        self, 
        options: UnassignRoleToUserOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Unassigns a role from a user."""
        ops = parse_options(UnassignRoleToUserOptions, options, caller="rbac.unassign_role_to_user()")
        
        role_id = ops.role_id
        user_id = ops.user_id
        
        if len(role_id) != 32:
            raise ValueError("Role Id length should be 32 char only")
        if len(user_id) != 32:
            raise ValueError("User Id length should be 32 char only")
        
        role_id_bytes = role_id.encode()
        user_id_bytes = user_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.UNASSIGN_ROLE_TO_USER.value)[:4].hex()
            encoded_params = encode(
                ['bytes32', 'bytes32'],
                [bytes.fromhex(role_id_bytes.hex()), bytes.fromhex(user_id_bytes.hex())]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"unassign role {role_id} from user {user_id}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UNASSIGN_ROLE_TO_USER.value,
                call_params={
                    'role_id': role_id_bytes,
                    'user_id': user_id_bytes
                    }
            )
            return self._handle_substrate_tx(call, f"unassign role {role_id} from user {user_id}", status_callback)

    async def unassign_user_to_group(
        self, 
        options: UnassignUserToGroupOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """Unassigns a user from a group."""
        ops = parse_options(UnassignUserToGroupOptions, options, caller="rbac.unassign_user_to_group()")
        
        user_id = ops.user_id
        group_id = ops.group_id
        
        if len(user_id) != 32:
            raise ValueError("User Id length should be 32 char only")
        if len(group_id) != 32:
            raise ValueError("Group Id length should be 32 char only")
        
        user_id_bytes = user_id.encode()
        group_id_bytes = group_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.UNASSIGN_USER_TO_GROUP.value)[:4].hex()
            encoded_params = encode(
                ['bytes32', 'bytes32'],
                [bytes.fromhex(user_id_bytes.hex()), bytes.fromhex(group_id_bytes.hex())]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            return await self._handle_evm_tx(tx, f"unassign user {user_id} from group {group_id}", status_callback, tx_options)
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UNASSIGN_USER_TO_GROUP.value,
                call_params={
                    'user_id': user_id_bytes,
                    'group_id': group_id_bytes
                    }
            )
            return self._handle_substrate_tx(call, f"unassign user {user_id} from group {group_id}", status_callback)
                
                
    # ---------------  Generalized handlers ----------------
    async def _handle_evm_tx(
        self, 
        tx: TxParams, 
        action: str, 
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """
        Generalized handler for EVM transactions.
        
        Args:
            tx (TxParams): The transaction parameters
            action (str): Description of the action being performed
            status_callback: Optional callback for transaction status
            tx_options: Optional transaction options
            
        Returns:
            Union[EvmSendResult, BuiltEvmTransactionResult]: 
                - EvmSendResult: For signed transactions with tx_hash, unsubscribe, and receipt promise
                - BuiltEvmTransactionResult: For unsigned transactions with message and tx object
        """
        if not self.metadata.pair:
            return BuiltEvmTransactionResult(
                message=f"Constructed {action} tx (unsigned).",
                tx=tx
            )
        try:
            return await self._send_evm_tx(tx, on_status=status_callback, opts=tx_options)
        except Exception as err:
            raise Exception(f"Failed to {action}: {str(err)}")

    def _handle_substrate_tx(
        self, 
        call, 
        action: str, 
        status_callback: StatusCallback = None
    ):
        """
        Generalized handler for Substrate transactions.
        
        Args:
            call: The Substrate call object
            action (str): Description of the action being performed
            status_callback: Optional callback for transaction status
            
        Returns:
            Union[SubstrateSendResult, BuiltCallTransactionResult]:
                - SubstrateSendResult: For signed transactions with tx_hash, unsubscribe, and finalize promise
                - BuiltCallTransactionResult: For unsigned transactions with message and call object
        """
        if not self.metadata.pair:
            return BuiltCallTransactionResult(
                message=f"Constructed {action} call (unsigned).",
                call=call
            )
        try:
            return self._send_substrate_tx(call, on_status=status_callback)
        except Exception as err:
            raise Exception(f"Failed to {action}: {str(err)}")

def _rpc_id(entity_id):
    return [ord(c) for c in entity_id]