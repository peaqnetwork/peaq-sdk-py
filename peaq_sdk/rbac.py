from typing import Optional, List
import uuid
import binascii

from peaq_sdk.base import Base
from peaq_sdk.types.common import (
    ChainType,
    SDKMetadata,
    PrecompileAddresses,
    EvmTransaction,
    BuiltEvmTransactionResult,
    CallModule,
    WrittenTransactionResult,
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
    ResponseFetchUserGroups
)

from peaq_sdk.utils.utils import evm_to_address

# 3rd party imports
from substrateinterface.base import SubstrateInterface
from web3 import Web3
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
        
    def create_role(self, role_name: str, role_id: Optional[str] = None) -> None:
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully added the RBAC role under the role name of {role_name} with the role id of {role_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC create role call for the role name of {role_name} and role id of {role_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ADD_ROLE.value,
                call_params={
                    'role_id': role_id_bytes,
                    'name': role_name
                    }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully added the RBAC role under the role name of {role_name} with the role id of {role_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC create role call for the role name of {role_name} and role id of {role_id}. You must sign and send externally.",
                    call=call
                )

    def create_group(self, group_name: str, group_id: Optional[str] = None):
        """Creates a new group of the given name at the group id."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully added the RBAC group under the group name of {group_name} with the group id of {group_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC create group call for the group name of {group_name} and group id of {group_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ADD_GROUP.value,
                call_params={
                    'group_id': group_id_bytes,
                    'name': group_name
                    }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully added the RBAC group under the group name of {group_name} with the group id of {group_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC create group call for the group name of {group_name} and group id of {group_id}. You must sign and send externally.",
                    call=call
                )

    def create_permission(self, permission_name: str, permission_id: Optional[str] = None):
        """Creates a new permission of the given name at the permission id."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully added the RBAC permission under the permission name of {permission_name} with the permission id of {permission_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC create permission call for the permission name of {permission_name} and permission id of {permission_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ADD_PERMISSION.value,
                call_params={
                    'permission_id': permission_id_bytes,
                    'name': permission_name
                    }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully added the RBAC permission under the permission name of {permission_name} with the permission id of {permission_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC create permission call for the permission name of {permission_name} and permission id of {permission_id}. You must sign and send externally.",
                    call=call
                )

    def assign_permission_to_role(self, permission_id: str, role_id: str):
        """Assigns a permission to a role."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully assigned permission {permission_id} to role {role_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC assign permission to role call for permission {permission_id} and role {role_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ASSIGN_PERMISSION_TO_ROLE.value,
                call_params={
                    'permission_id': permission_id_bytes,
                    'role_id': role_id_bytes
                    }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully assigned permission {permission_id} to role {role_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC assign permission to role call for permission {permission_id} and role {role_id}. You must sign and send externally.",
                    call=call
                )

    def assign_role_to_group(self, role_id: str, group_id: str):
        """Assigns a role to a group."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully assigned role {role_id} to group {group_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC assign role to group call for role {role_id} and group {group_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ASSIGN_ROLE_TO_GROUP.value,
                call_params={
                    'role_id': role_id_bytes,
                    'group_id': group_id_bytes
                    }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully assigned role {role_id} to group {group_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC assign role to group call for role {role_id} and group {group_id}. You must sign and send externally.",
                    call=call
                )

    def assign_role_to_user(self, role_id: str, user_id: str):
        """Assigns a role to a user."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully assigned role {role_id} to user {user_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC assign role to user call for role {role_id} and user {user_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ASSIGN_ROLE_TO_USER.value,
                call_params={
                    'role_id': role_id_bytes,
                    'user_id': user_id_bytes
                    }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully assigned role {role_id} to user {user_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC assign role to user call for role {role_id} and user {user_id}. You must sign and send externally.",
                    call=call
                )

    def assign_user_to_group(self, user_id: str, group_id: str):
        """Assigns a user to a group."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully assigned user {user_id} to group {group_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC assign user to group call for user {user_id} and group {group_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.ASSIGN_USER_TO_GROUP.value,
                call_params={
                    'user_id': user_id_bytes,
                    'group_id': group_id_bytes
                    }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully assigned user {user_id} to group {group_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC assign user to group call for user {user_id} and group {group_id}. You must sign and send externally.",
                    call=call
                )
                
    def fetch_role(self, owner: str, role_id: str, wss_base_url: Optional[str] = None) -> FetchResponseData:
        if self.metadata.chain_type is ChainType.EVM:
            if not wss_base_url:
                raise BaseUrlError(f"Must pass a wss base url when reading from EVM.")
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=wss_base_url, ss58_format=42)
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

    def fetch_group(self, owner: str, group_id: str, wss_base_url: Optional[str] = None) -> FetchResponseData:
        """Fetches a group by owner and group id."""
        if self.metadata.chain_type is ChainType.EVM:
            if not wss_base_url:
                raise BaseUrlError(f"Must pass a wss base url when reading from EVM.")
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=wss_base_url, ss58_format=42)
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

    def fetch_permission(self, owner: str, permission_id: str, wss_base_url: Optional[str] = None) -> FetchResponseData:
        """Fetches a permission by owner and permission id."""
        if self.metadata.chain_type is ChainType.EVM:
            if not wss_base_url:
                raise BaseUrlError(f"Must pass a wss base url when reading from EVM.")
            owner_address = evm_to_address(owner)
            api = SubstrateInterface(url=wss_base_url, ss58_format=42)
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

    def disable_role(self, role_id: str):
        """Disables a role."""
        if len(role_id) != 32:
            raise ValueError("Role Id length should be 32 char only")
        
        role_id_bytes = role_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.DISABLE_ROLE.value)[:4].hex()
            encoded_params = encode(
                ['bytes32'],
                [bytes.fromhex(role_id_bytes.hex())]
            ).hex()
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully disabled role {role_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC disable role call for role {role_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.DISABLE_ROLE.value,
                call_params={'role_id': role_id_bytes}
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully disabled role {role_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC disable role call for role {role_id}. You must sign and send externally.",
                    call=call
                )

    def disable_group(self, group_id: str):
        """Disables a group."""
        if len(group_id) != 32:
            raise ValueError("Group Id length should be 32 char only")
        
        group_id_bytes = group_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.DISABLE_GROUP.value)[:4].hex()
            encoded_params = encode(
                ['bytes32'],
                [bytes.fromhex(group_id_bytes.hex())]
            ).hex()
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully disabled group {group_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC disable group call for group {group_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.DISABLE_GROUP.value,
                call_params={'group_id': group_id_bytes}
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully disabled group {group_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC disable group call for group {group_id}. You must sign and send externally.",
                    call=call
                )

    def disable_permission(self, permission_id: str):
        """Disables a permission."""
        if len(permission_id) != 32:
            raise ValueError("Permission Id length should be 32 char only")
        
        permission_id_bytes = permission_id.encode()
        
        if self.metadata.chain_type is ChainType.EVM:
            rbac_function_selector = self.api.keccak(text=RbacFunctionSignatures.DISABLE_PERMISSION.value)[:4].hex()
            encoded_params = encode(
                ['bytes32'],
                [bytes.fromhex(permission_id_bytes.hex())]
            ).hex()
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully disabled permission {permission_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC disable permission call for permission {permission_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.DISABLE_PERMISSION.value,
                call_params={'permission_id': permission_id_bytes}
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully disabled permission {permission_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC disable permission call for permission {permission_id}. You must sign and send externally.",
                    call=call
                )

    def update_role(self, role_id: str, role_name: str):
        """Updates a role name."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully updated role {role_id} with name {role_name}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC update role call for role {role_id} with name {role_name}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UPDATE_ROLE.value,
                call_params={
                    'role_id': role_id_bytes,
                    'name': role_name
                }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully updated role {role_id} with name {role_name}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC update role call for role {role_id} with name {role_name}. You must sign and send externally.",
                    call=call
                )

    def update_group(self, group_id: str, group_name: str):
        """Updates a group name."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully updated group {group_id} with name {group_name}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC update group call for group {group_id} with name {group_name}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UPDATE_GROUP.value,
                call_params={
                    'group_id': group_id_bytes,
                    'name': group_name
                }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully updated group {group_id} with name {group_name}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC update group call for group {group_id} with name {group_name}. You must sign and send externally.",
                    call=call
                )

    def update_permission(self, permission_id: str, permission_name: str):
        """Updates a permission name."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully updated permission {permission_id} with name {permission_name}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC update permission call for permission {permission_id} with name {permission_name}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UPDATE_PERMISSION.value,
                call_params={
                    'permission_id': permission_id_bytes,
                    'name': permission_name
                }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully updated permission {permission_id} with name {permission_name}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC update permission call for permission {permission_id} with name {permission_name}. You must sign and send externally.",
                    call=call
                )

    def unassign_permission_to_role(self, permission_id: str, role_id: str):
        """Unassigns a permission from a role."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully unassigned permission {permission_id} from role {role_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC unassign permission from role call for permission {permission_id} and role {role_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UNASSIGN_PERMISSION_TO_ROLE.value,
                call_params={
                    'permission_id': permission_id_bytes,
                    'role_id': role_id_bytes
                    }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully unassigned permission {permission_id} from role {role_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC unassign permission from role call for permission {permission_id} and role {role_id}. You must sign and send externally.",
                    call=call
                )

    def unassign_role_to_group(self, role_id: str, group_id: str):
        """Unassigns a role from a group."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully unassigned role {role_id} from group {group_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC unassign role from group call for role {role_id} and group {group_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UNASSIGN_ROLE_TO_GROUP.value,
                call_params={
                    'role_id': role_id_bytes,
                    'group_id': group_id_bytes
                    }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully unassigned role {role_id} from group {group_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC unassign role from group call for role {role_id} and group {group_id}. You must sign and send externally.",
                    call=call
                )

    def unassign_role_to_user(self, role_id: str, user_id: str):
        """Unassigns a role from a user."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully unassigned role {role_id} from user {user_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC unassign role from user call for role {role_id} and user {user_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UNASSIGN_ROLE_TO_USER.value,
                call_params={
                    'role_id': role_id_bytes,
                    'user_id': user_id_bytes
                    }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully unassigned role {role_id} from user {user_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC unassign role from user call for role {role_id} and user {user_id}. You must sign and send externally.",
                    call=call
                )

    def unassign_user_to_group(self, user_id: str, group_id: str):
        """Unassigns a user from a group."""
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
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.RBAC.value,
                "data": f"0x{rbac_function_selector}{encoded_params}"
            }
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully unassigned user {user_id} from group {group_id}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed RBAC unassign user from group call for user {user_id} and group {group_id}. You must sign and send externally.",
                    tx=tx
                )
        
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_RBAC.value,
                call_function=RbacCallFunction.UNASSIGN_USER_TO_GROUP.value,
                call_params={
                    'user_id': user_id_bytes,
                    'group_id': group_id_bytes
                    }
            )
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully unassigned user {user_id} from group {group_id}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed RBAC unassign user from group call for user {user_id} and group {group_id}. You must sign and send externally.",
                    call=call
                )

def _rpc_id(entity_id):
    return [ord(c) for c in entity_id]