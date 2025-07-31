# python native imports
from typing import Optional, Union, List
import json
from enum import Enum

# local imports
from peaq_sdk.base import Base
from peaq_sdk.types.base import TxOptions, StatusCallback
from peaq_sdk.utils.utils import parse_options

from peaq_sdk.types.common import (
    ChainType,
    SDKMetadata,
    PrecompileAddresses,
    CallModule,
    BuiltEvmTransactionResult,
    BuiltCallTransactionResult
)
from peaq_sdk.types.storage import (
    AddItemOptions,
    UpdateItemOptions,
    RemoveItemOptions,
    GetItemOptions,
    StorageFunctionSignatures,
    StorageCallFunction,
    GetItemResult,
    StorageWriteResult
)
from peaq_sdk.utils.utils import evm_to_address

# 3rd party imports
from substrateinterface.base import SubstrateInterface, GenericCall
from web3 import Web3
from web3.types import TxParams
from eth_abi import encode

class Storage(Base):
    """
    Provides methods to interact with the peaq on-chain storage precompile (EVM)
    or pallet (Substrate). Supports add, get, update, remove operations, and
    batch processing with various execution modes.
    """
    def __init__(self, api: Web3 | SubstrateInterface, metadata: SDKMetadata) -> None:
        """
        Initializes Storage with a connected API instance and shared SDK metadata.

        Args:
            api (Web3 | SubstrateInterface): The blockchain API connection.
                which may be a Web3 (EVM) or SubstrateInterface (Substrate).
            metadata (SDKMetadata): Shared metadata, including chain type,
                and optional signer.
        """
        super().__init__(api, metadata)

    async def add_item(
        self, 
        options: AddItemOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> StorageWriteResult:
        """
        Adds a new item to the on-chain storage.
        
        - EVM: Constructs a transaction to the `addItem` storage precompile contract.
        - Substrate: Composes an `add_item` extrinsic to the peaqStorage pallet.

        Args:
            options (AddItemOptions): Options containing item_type and item.
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TxOptions for EVM transactions.

        Returns:
            StorageWriteResult: A Union type that can be one of:
                - SubstrateSendResult: For signed Substrate transactions with txHash, unsubscribe, and finalize promise
                - EvmSendResult: For signed EVM transactions with txHash, unsubscribe, and receipt promise  
                - BuiltEvmTransactionResult: For unsigned EVM transactions with message and tx object
                - BuiltCallTransactionResult: For unsigned Substrate calls with message and extrinsic object
        """
        ops = parse_options(AddItemOptions, options, caller="storage.add_item()")
        
        # Extract values from options        
        item_type = ops.item_type
        item = ops.item
        
        # Prepare payload
        item_string = item if isinstance(item, str) else json.dumps(item)

        if self.metadata.chain_type is ChainType.EVM:
            return await self._add_item_evm(item_type, item_string, status_callback, tx_options)
        else:
            return self._add_item_substrate(item_type, item_string, status_callback)

    
        
    async def get_item(
        self, options: GetItemOptions
    ) -> Optional[GetItemResult]:
        """
        Retrieves a stored item by its `item_type` for the specified address.
        
        - EVM: Method converts the EVM address (either from the local keypair or 
            the passed `address` argument) to its Substrate format, then temporarily
            connects to a Substrate node via the existing baseUrl to fetch the on-chain storage.
        - Substrate: If called on a Substrate chain, it uses the existing Substrate API
            connection directly.

        Args:
            options (GetItemOptions): Options containing item_type and optional address.

        Returns:
            Optional[GetItemResult]: An object with the itemType as key and the stored value as string,
                or None if the item doesn't exist.

        Raises:
            TypeError: If no address can be determined (no local signer and no `address`).
        """
        ops = parse_options(GetItemOptions, options, caller="storage.get_item()")
        item_type = ops.item_type
        address = ops.address
        # Get the appropriate address and convert if needed
        account_address = address or getattr(self.metadata.pair, 'address', None) if self.metadata.pair else None
        
        if not account_address:
            raise TypeError('Address is required when no signer is set')
        
        # EVM chains: create temporary API connection to read from Substrate
        if self.metadata.chain_type == ChainType.EVM:
            substrate_address = evm_to_address(account_address)
            
            # Create temporary Substrate API connection
            temp_api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
            
            try:
                return await self._read_from_substrate(item_type, substrate_address, temp_api)
            finally:
                # Clean up temporary connection if needed
                # temp_api doesn't have disconnect in Python SubstrateInterface
                pass
        
        # For Substrate chains, use direct API access
        api = self.api
        return await self._read_from_substrate(item_type, account_address, api)


        
    async def update_item(
        self, 
        options: UpdateItemOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> StorageWriteResult:
        """
        Updates an existing item under `item_type` in on-chain storage by
        replacing its value with `item`.
        
        - EVM: Constructs a transaction to the `updateItem` storage precompile contract.
        - Substrate: Composes an `update_item` extrinsic to the peaqStorage
            pallet.

        Args:
            options (UpdateItemOptions): Options containing item_type and item.
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TxOptions for EVM transactions.

        Returns:
            StorageWriteResult: A Union type that can be one of:
                - SubstrateSendResult: For signed Substrate transactions with txHash, unsubscribe, and finalize promise
                - EvmSendResult: For signed EVM transactions with txHash, unsubscribe, and receipt promise  
                - BuiltEvmTransactionResult: For unsigned EVM transactions with message and tx object
                - BuiltCallTransactionResult: For unsigned Substrate calls with message and extrinsic object
        """        
        ops = parse_options(UpdateItemOptions, options, caller="storage.update_item()")
        
        # Extract values from options
        item_type = ops.item_type
        item = ops.item
        
        item_string = item if isinstance(item, str) else json.dumps(item)
        
        if self.metadata.chain_type is ChainType.EVM:
            return await self._update_item_evm(item_type, item_string, status_callback, tx_options)
        else:
            return self._update_item_substrate(item_type, item_string, status_callback)


            
    async def remove_item(
        self, 
        options: RemoveItemOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> StorageWriteResult:
        """
        Removes an on-chain item.
        
        - EVM: Constructs a transaction to the `removeItem` storage precompile contract.
        - Substrate: Composes a `remove_item` extrinsic to the peaqStorage pallet.

        Args:
            options (RemoveItemOptions): Options containing item_type.
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TxOptions for EVM transactions.

        Returns:
            StorageWriteResult: A Union type that can be one of:
                - SubstrateSendResult: For signed Substrate transactions with txHash, unsubscribe, and finalize promise
                - EvmSendResult: For signed EVM transactions with txHash, unsubscribe, and receipt promise  
                - BuiltEvmTransactionResult: For unsigned EVM transactions with message and tx object
                - BuiltCallTransactionResult: For unsigned Substrate calls with message and extrinsic object
        """
        ops = parse_options(RemoveItemOptions, options, caller="storage.remove_item()")
        
        # Extract values from options
        item_type = ops.item_type
        
        if self.metadata.chain_type is ChainType.EVM:
            return await self._remove_item_evm(item_type, status_callback, tx_options)
        else:
            return self._remove_item_substrate(item_type, status_callback)
    
    # ---------------  Helper methods ----------------
    async def _read_from_substrate(self, item_type: str, owner_address: str, api) -> Optional[GetItemResult]:
        """
        Helper method to read storage item from Substrate API.
        
        Args:
            item_type: The key under which the item was stored
            owner_address: The Substrate address of the owner
            api: The Substrate API instance to use for querying
            
        Returns:
            The storage item result or null if not found
        """
        # Query storage
        item_type_hex = "0x" + item_type.encode("utf-8").hex()
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            StorageCallFunction.GET_ITEM.value, [owner_address, item_type_hex, block_hash]
        )
        
        # Check result
        if resp['result'] is None:
            return None
        
        raw = resp['result']['item']
        decoded = bytes.fromhex(raw[2:]).decode("utf-8")
        return {item_type: decoded}
    
    # ---------------  EVM helpers ----------------
    async def _add_item_evm(self, item_type: str, item_string: str, status_callback: StatusCallback = None, tx_options: TxOptions = {}) -> StorageWriteResult:
        """Add item on EVM using the storage precompile."""
        add_item_function_selector = self.api.keccak(text=StorageFunctionSignatures.ADD_ITEM.value)[:4].hex()
        item_type_encoded = item_type.encode("utf-8").hex()
        final_item = item_string.encode("utf-8").hex()
        encoded_params = encode(
            ['bytes', 'bytes'],
            [bytes.fromhex(item_type_encoded), bytes.fromhex(final_item)]
        ).hex()
        
        tx: TxParams = {
            "to": PrecompileAddresses.STORAGE.value,
            "data": f"0x{add_item_function_selector}{encoded_params}"
        }
        
        return await self._handle_evm_tx(tx, f"add storage item {item_type}", status_callback, tx_options)
    
    async def _update_item_evm(self, item_type: str, item_string: str, status_callback: StatusCallback = None, tx_options: TxOptions = {}) -> StorageWriteResult:
        """Update item on EVM using the storage precompile."""
        update_item_function_selector = self.api.keccak(text=StorageFunctionSignatures.UPDATE_ITEM.value)[:4].hex()
        item_type_encoded = item_type.encode("utf-8").hex()
        final_item = item_string.encode("utf-8").hex()
        
        encoded_params = encode(
            ['bytes', 'bytes'],
            [bytes.fromhex(item_type_encoded), bytes.fromhex(final_item)]
        ).hex()
    
        tx: TxParams = {
            "to": PrecompileAddresses.STORAGE.value,
            "data": f"0x{update_item_function_selector}{encoded_params}"
        }
        
        return await self._handle_evm_tx(tx, f"update storage item {item_type}", status_callback, tx_options)
    
    async def _remove_item_evm(self, item_type: str, status_callback: StatusCallback = None, tx_options: TxOptions = {}) -> StorageWriteResult:
        """Remove item on EVM using the storage precompile."""
        remove_item_function_selector = self.api.keccak(text=StorageFunctionSignatures.REMOVE_ITEM.value)[:4].hex()
        item_type_encoded = item_type.encode("utf-8").hex()
        
        encoded_params = encode(
            ['bytes'],
            [bytes.fromhex(item_type_encoded)]
        ).hex()
        
        tx: TxParams = {
            "to": PrecompileAddresses.STORAGE.value,
            "data": f"0x{remove_item_function_selector}{encoded_params}"
        }
        
        return await self._handle_evm_tx(tx, f"remove storage item {item_type}", status_callback, tx_options)
    
    # ---------------  Substrate helpers ----------------
    def _add_item_substrate(self, item_type: str, item_string: str, status_callback: StatusCallback = None) -> StorageWriteResult:
        """Add item on Substrate using the peaqStorage pallet."""
        call = self.api.compose_call(
            call_module=CallModule.PEAQ_STORAGE.value,
            call_function=StorageCallFunction.ADD_ITEM.value,
            call_params={'item_type': item_type, 'item': item_string}
        )
        return self._handle_substrate_tx(call, f"add storage item {item_type}", status_callback)
    
    def _update_item_substrate(self, item_type: str, item_string: str, status_callback: StatusCallback = None) -> StorageWriteResult:
        """Update item on Substrate using the peaqStorage pallet."""
        call = self.api.compose_call(
            call_module=CallModule.PEAQ_STORAGE.value,
            call_function=StorageCallFunction.UPDATE_ITEM.value,
            call_params={'item_type': item_type, 'item': item_string}
        )
        return self._handle_substrate_tx(call, f"update storage item {item_type}", status_callback)
    
    def _remove_item_substrate(self, item_type: str, status_callback: StatusCallback = None) -> StorageWriteResult:
        """Remove item on Substrate using the peaqStorage pallet."""
        call = self.api.compose_call(
            call_module=CallModule.PEAQ_STORAGE.value,
            call_function=StorageCallFunction.REMOVE_ITEM.value,
            call_params={'item_type': item_type}
        )
        return self._handle_substrate_tx(call, f"remove storage item {item_type}", status_callback)
    
    # ---------------  Generalized handlers ----------------
    async def _handle_evm_tx(self, tx: TxParams, action: str, status_callback: StatusCallback = None, tx_options: TxOptions = {}) -> StorageWriteResult:
        """Generalized handler for EVM transactions."""
        if not self.metadata.pair:
            return BuiltEvmTransactionResult(
                message=f"Constructed {action} tx (unsigned).",
                tx=tx
            )
        try:
            return await self._send_evm_tx(tx, on_status=status_callback, opts=tx_options)
        except Exception as err:
            raise Exception(f"Failed to {action}: {str(err)}")
    
    def _handle_substrate_tx(self, call, action: str, status_callback: StatusCallback = None) -> StorageWriteResult:
        """Generalized handler for Substrate transactions."""
        if not self.metadata.pair:
            return BuiltCallTransactionResult(
                message=f"Constructed {action} call (unsigned).",
                call=call
            )
        try:
            return self._send_substrate_call_structured(call, on_status=status_callback)
        except Exception as err:
            raise Exception(f"Failed to {action}: {str(err)}")