from typing import Optional
import uuid

from peaq_sdk.base import Base
from peaq_sdk.types.common import (
    ChainType,
    SDKMetadata,
    PrecompileAddresses,
    EvmTransaction,
    BuiltEvmTransactionResult,
    CallModule,
    WrittenTransactionResult,
    BuiltCallTransactionResult
)
from peaq_sdk.types.rbac import (
    RbacCallFunction,
    RbacFunctionSignatures
)

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