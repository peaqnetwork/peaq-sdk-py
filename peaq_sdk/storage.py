# python native imports
from typing import Optional, Union, List
import json
from enum import Enum

# local imports
from peaq_sdk.base import Base
from peaq_sdk.types.common import (
    ChainType,
    SDKMetadata,
    PrecompileAddresses,
    CallModule,
    SeedError,
    WrittenTransactionResult,
    BuiltEvmTransactionResult,
    BuiltCallTransactionResult,
    BaseUrlError
)
from peaq_sdk.types.storage import (
    GetItemError,
    StorageFunctionSignatures,
    StorageCallFunction,
    GetItemResult
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

    def add_item(self, item_type: str, item: object) -> Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
        """
        Adds a new item of `item_type` to the on-chain storage, storing `item`
        as its value.
        
        - EVM: Constructs a transaction to the `addItem` storage precompile contract.
        - Substrate: Composes an `add_item` extrinsic to the peaqStorage
            pallet.

        Args:
            item_type (str): A string key used to categorize or identify the item.
            item (object): The value to store. If not already a string, it is
                serialized to JSON before being sent on-chain.

        Returns:
            Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
                - WrittenTransactionResult: The transaction or extrinsic was signed and broadcasted.
                    Returned with a message and receipt.
                - BuiltEvmTransactionResult or BuiltCallTransactionResult: The tx/call was constructed
                    but not signed (no local signer). Returned with message and tx/call.
        """
 
        # Prepare payload
        item_string = item if isinstance(item, str) else json.dumps(item)

        if self.metadata.chain_type is ChainType.EVM:
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
            
            if self.metadata.pair and not self.metadata.machine_station:
                account = self.metadata.pair
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully added the storage item type {item_type} with item {item} for the address {account.address}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed add_item tx object for peaq storage with item type {item_type} and item {item}. You must sign and send it externally.",
                    tx=tx
                )
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_STORAGE.value,
                call_function=StorageCallFunction.ADD_ITEM.value,
                call_params={'item_type': item_type, 'item': item_string}
            )
            
            if self.metadata.pair:
                keypair = self.metadata.pair
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully added the storage item type {item_type} with item {item} for the address {keypair.ss58_address}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed add_item call object for peaq storage with item type {item_type} and item {item}. You must sign and send it externally.",
                    call=call
                )

    
        
    def get_item(
        self, item_type: str, address: Optional[str] = None
    ) -> GetItemResult:
        """
        Retrieves a stored item by its `item_type` for the specified address.
        
        - EVM: Method converts the EVM address (either from the local keypair or 
            the passed `address` argument) to its Substrate format, then temporarily
            connects to a Substrate node via `wss_base_url` to fetch the on-chain storage.
        - Substrate: If called on a Substrate chain, it uses the existing Substrate API
            connection directly.

        Args:
            item_type (str): The key under which the item was stored.
            address (Optional[str]): The address whose data is being queried. If not provided,
                the address from the local signer (if any) is used.


        Returns:
            GetItemResult:
                - `item_type`: The key requested.
                - `item`: The decoded value (as a string).

        Raises:
            TypeError: If no address can be determined (no local signer and no `address`).
            GetItemError: If the item does not exist on-chain under that key.
        """
        if self.metadata.chain_type is ChainType.EVM:
            evm_address = (
                getattr(self.metadata.pair, 'address', address)
                if self.metadata.pair and not self.metadata.machine_station
                else address
            )
            if not evm_address:
                raise TypeError(f"Address is set to {evm_address}. Please either set seed at instance creation or pass an address.")
            owner_address = evm_to_address(evm_address)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
            display_address = evm_address
            
        else:
            owner_address = (
                getattr(self.metadata.pair, 'ss58_address', address)
                if self.metadata.pair
                else address
            )
            if not owner_address:
                raise TypeError(f"Address is set to {owner_address}. Please either set seed at instance creation or pass an address.")
            api = self.api
            display_address = owner_address
        
        # Query storage
        item_type_hex = "0x" + item_type.encode("utf-8").hex()
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            StorageCallFunction.GET_ITEM.value, [owner_address, item_type_hex, block_hash]
        )
        
        # Check result
        if resp['result'] is None:
            raise GetItemError(f"Item type of {item_type} was not found at address {display_address}.") 
        
        raw = resp['result']['item']
        decoded = bytes.fromhex(raw[2:]).decode("utf-8")
        return GetItemResult(item_type=item_type, item=decoded).to_dict()


        
    def update_item(self, item_type: str, item: object) -> Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
        """
        Updates an existing item under `item_type` in on-chain storage by
        replacing its value with `item`.
        
        - EVM: Constructs a transaction to the `updateItem` storage precompile contract.
        - Substrate: Composes an `update_item` extrinsic to the peaqStorage
            pallet.

        Args:
            item_type (str): The key used for the on-chain item.
            item (object): The new value for that key (JSON-stringified if not a str).

        Returns:
            Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
                - WrittenTransactionResult: The transaction or extrinsic was signed and broadcasted.
                    Returned with a message and receipt.
                - BuiltEvmTransactionResult or BuiltCallTransactionResult: The tx/call was constructed
                    but not signed (no local signer). Returned with message and tx/call.
        """        
        item_string = item if isinstance(item, str) else json.dumps(item)
        
        if self.metadata.chain_type is ChainType.EVM:
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
            
            if self.metadata.pair:
                account = self.metadata.pair
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully updated the storage item type {item_type} with item {item} for the address {account.address}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed update_item tx object for peaq storage with item type {item_type} and item {item}. You must sign and send it externally.",
                    tx=tx
                )
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_STORAGE.value,
                call_function=StorageCallFunction.UPDATE_ITEM.value,
                call_params={'item_type': item_type, 'item': item_string}
            )
            
            if self.metadata.pair:
                keypair = self.metadata.pair
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully updated the storage item type {item_type} with item {item} for the address {keypair.ss58_address}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed update_item call object for peaq storage with item type {item_type} and item {item}. You must sign and send it externally.",
                    call=call
                )


            
    def remove_item(self, item_type: str) -> Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
        """
        Removes an on-chain item under `item_type`.
        
        - EVM: Currently not supported until the storage precompile is
          upgraded. Calling this on EVM raises a ValueError. (An implementation
          outline is provided in the code for future use.)
        - Substrate: Composes a `remove_item` extrinsic to the peaqStorage
            pallet.

        Args:
            item_type (str): The key for the item to remove.

        Returns:
            Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
                - WrittenTransactionResult: The transaction or extrinsic was signed and broadcasted.
                    Returned with a message and receipt.
                - BuiltEvmTransactionResult or BuiltCallTransactionResult: The tx/call was constructed
                    but not signed (no local signer). Returned with message and tx/call.

        Raises:
            ValueError: If called on EVM (not yet supported).
        """
        if self.metadata.chain_type is ChainType.EVM:
            # raise ValueError("Precompile for peaq Storage Remove Item will be included in the next runtime update.")
            # remove error when upgrade deployed
            remove_item_function_selector = self.api.keccak(text=StorageFunctionSignatures.REMOVE_ITEM.value)[:4].hex()
            item_type_encoded = item_type.encode("utf-8").hex()
            
            # Create the encoded parameters to create calldata
            encoded_params = encode(
                ['bytes'],
                [bytes.fromhex(item_type_encoded)]
            ).hex()
            
            payload = "0x" + remove_item_function_selector + encoded_params
            tx: TxParams = {
                "to": PrecompileAddresses.STORAGE.value,
                "data": payload
            }
            
            if self.metadata.pair and not self.metadata.machine_station:
                account = self.metadata.pair
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully removed the storage item type {item_type} for the address {account.address}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed remove_item tx object for peaq storage with item type {item_type}. You must sign and send it externally.",
                    tx=tx
                )
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_STORAGE.value,
                call_function=StorageCallFunction.REMOVE_ITEM.value,
                call_params={'item_type': item_type}
            )
            
            if self.metadata.pair:
                keypair = self.metadata.pair
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully removed the storage item type {item_type} for the address {keypair.ss58_address}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed remove_item call object for peaq storage with item type {item_type}. You must sign and send it externally.",
                    call=call
                )