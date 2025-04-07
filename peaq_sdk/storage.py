# python native imports
from typing import Optional, Union
import json
from enum import Enum

# local imports
from peaq_sdk.base import Base
from peaq_sdk.types.common import (
    ChainType,
    SDKMetadata,
    PrecompileAddresses,
    CallModule,
    EvmTransaction,
    SeedError,
    WrittenTransactionResult,
    BuiltEvmTransactionResult,
    BuiltCallTransactionResult,
)
from peaq_sdk.types.storage import (
    GetItemError,
    StorageFunctionSignatures,
    StorageCallFunction,
    GetItemResult,
    UpdateItemResult,
    RemoveItemResult,
)
from peaq_sdk.utils.utils import evm_to_address

# 3rd party imports
from substrateinterface.base import SubstrateInterface
from web3 import Web3
from eth_abi import encode

class Storage(Base):
    """
    Provides methods to interact with the peaq on‑chain storage precompile (EVM)
    or pallet (Substrate). Supports add, get, update, and remove operations
    for arbitrary typed items.
    """
    def __init__(self, api: Web3 | SubstrateInterface, metadata: SDKMetadata) -> None:
        """
        Initializes Storage with a connected API instance and shared SDK metadata.

        Args:
            api (Web3 | SubstrateInterface): The blockchain API connection.
            metadata (SDKMetadata): Shared SDK metadata including signer info.
        """
        super().__init__()
        self._api = api
        self.__metadata: SDKMetadata = metadata

    def add_item(self, item_type: str, item: object) -> Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
        """
        Adds a new item under the given type to on-chain storage.

        For EVM chains, this invokes the storage precompile via a transaction
        to the fixed precompile address. For Substrate chains, it calls the
        peaqStorage pallet's `add_item` extrinsic directly.

        Args:
            item_type (str): A string key categorizing the item.
            item (object): The value to store (will be JSON-stringified if not a str).

        Returns:
            AddItemResult: Contains a success message and the transaction receipt.

        Raises:
            SeedError: If no signer (seed) has been initialized.
        """
 
        # Prepare payload
        item_string = item if isinstance(item, str) else json.dumps(item)

        if self.__metadata.chain_type is ChainType.EVM:
            add_item_function_selector = self._api.keccak(text=StorageFunctionSignatures.ADD_ITEM.value)[:4].hex()
            item_type_encoded = item_type.encode("utf-8").hex()
            final_item = item_string.encode("utf-8").hex()
            encoded_params = encode(
                ['bytes', 'bytes'],
                [bytes.fromhex(item_type_encoded), bytes.fromhex(final_item)]
            ).hex()
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.STORAGE.value,
                "data": f"0x{add_item_function_selector}{encoded_params}"
            }
            
            if self.__metadata.pair:
                account = self.__metadata.pair
                receipt = self._send_evm_tx(tx, self.__metadata.pair)
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
            call = self._api.compose_call(
                call_module=CallModule.PEAQ_STORAGE.value,
                call_function=StorageCallFunction.ADD_ITEM.value,
                call_params={'item_type': item_type, 'item': item_string}
            )
            
            if self.__metadata.pair:
                keypair = self.__metadata.pair
                receipt = self._send_substrate_tx(call, self.__metadata.pair)
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
        self, item_type: str, address: Optional[str] = None, wss_base_url: Optional[str] = None
    ) -> GetItemResult:
        """
        Retrieves a stored item by type for a given address.

        For EVM chains, it converts the EVM address to SS58, opens a temporary
        Substrate WS connection, and queries the storage pallet RPC. For
        Substrate chains, it uses the existing connection.

        Args:
            item_type (str): The key under which the item was stored.
            address (Optional[str]): The EVM or SS58 address to query. If not
                provided, uses the initialized signer's address.
            wss_base_url (Optional[str]): Required for EVM queries: a substrate
                WS URL for RPC reads.

        Returns:
            GetItemResult: Contains the item type and the decoded string value.

        Raises:
            TypeError: If no address can be determined.
            GetItemError: If no item exists under that type for the address.
        """
        if self.__metadata.chain_type is ChainType.EVM:
            evm_address = (
                getattr(self.__metadata.pair, 'address', address)
                if self.__metadata.pair
                else address
            )
            if not evm_address:
                raise TypeError(f"Address is set to {evm_address}. Please either set seed at instance creation or pass an address.")
            owner_address = evm_to_address(evm_address)
            api = SubstrateInterface(url=wss_base_url, ss58_format=42)
        else:
            owner_address = (
                getattr(self.__metadata.pair, 'ss58_address', address)
                if self.__metadata.pair
                else address
            )
            if not owner_address:
                raise TypeError(f"Address is set to {owner_address}. Please either set seed at instance creation or pass an address.")
            api = self._api
        
        # Query storage
        item_type_hex = "0x" + item_type.encode("utf-8").hex()
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            StorageCallFunction.GET_ITEM.value, [owner_address, item_type_hex, block_hash]
        )
        
        # Check result
        if resp['result'] is None:
            raise GetItemError(f"Item type of {item_type} was not found at address {owner_address}.") 
        
        raw = resp['result']['item']
        decoded = bytes.fromhex(raw[2:]).decode("utf-8")
        return GetItemResult(item_type=item_type, item=decoded).to_dict()
        
    def update_item(self, item_type: str, item: object) -> Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
        """
        Updates an existing item under the given type in on-chain storage. Mirrors `add_item` 
        but calls the `update_item` precompile or pallet extrinsic.

        Args:
            item_type (str): The key categorizing the item.
            item (object): The new value (JSON-stringified if not a str).

        Returns:
            UpdateItemResult: Contains a success message and the transaction receipt.

        Raises:
            SeedError: If no signer (seed) has been initialized.
        """        
        item_string = item if isinstance(item, str) else json.dumps(item)
        
        if self.__metadata.chain_type is ChainType.EVM:
            update_item_function_selector = self._api.keccak(text=StorageFunctionSignatures.UPDATE_ITEM.value)[:4].hex()
            item_type_encoded = item_type.encode("utf-8").hex()
            final_item = item_string.encode("utf-8").hex()
            
            encoded_params = encode(
                ['bytes', 'bytes'],
                [bytes.fromhex(item_type_encoded), bytes.fromhex(final_item)]
            ).hex()
        
            tx: EvmTransaction = {
                "to": PrecompileAddresses.STORAGE.value,
                "data": f"0x{update_item_function_selector}{encoded_params}"
            }
            
            if self.__metadata.pair:
                account = self.__metadata.pair
                receipt = self._send_evm_tx(tx, self.__metadata.pair)
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
            call = self._api.compose_call(
                call_module=CallModule.PEAQ_STORAGE.value,
                call_function=StorageCallFunction.UPDATE_ITEM.value,
                call_params={'item_type': item_type, 'item': item_string}
            )
            
            if self.__metadata.pair:
                keypair = self.__metadata.pair
                receipt = self._send_substrate_tx(call, self.__metadata.pair)
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
        Removes an item under the given type from on-chain storage.

        On EVM this will currently raise an error until the precompile is upgraded.
        On Substrate it invokes the peaqStorage pallet's `remove_item` extrinsic directly.

        Args:
            item_type (str): The key categorizing the item to remove.

        Returns:
            RemoveItemResult: Contains a success message and the transaction receipt.

        Raises:
            SeedError: If no signer (seed) has been initialized.
            ValueError: If called on EVM (not yet supported).
        """
        # check if EVM or Substrate
        if self.__metadata.chain_type is ChainType.EVM:
            raise ValueError("Precompile for peaq Storage Remove Item will be included in the next runtime update.")
            # uncomment below when upgrade deployed
            remove_item_function_selector = self._api.keccak(text=StorageFunctionSignatures.REMOVE_ITEM.value)[:4].hex()
            item_type_encoded = item_type.encode("utf-8").hex()
            
            # Create the encoded parameters to create calldata
            encoded_params = encode(
                ['bytes'],
                [bytes.fromhex(item_type_encoded)]
            ).hex()
            
            payload = "0x" + remove_item_function_selector + encoded_params
            tx: EvmTransaction = {
                "to": PrecompileAddresses.STORAGE.value,
                "data": payload
            }
            
            if self.__metadata.pair:
                account = self.__metadata.pair
                receipt = self._send_evm_tx(tx, self.__metadata.pair)
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
            call = self._api.compose_call(
                call_module=CallModule.PEAQ_STORAGE.value,
                call_function=StorageCallFunction.REMOVE_ITEM.value,
                call_params={'item_type': item_type}
            )
            
            if self.__metadata.pair:
                keypair = self.__metadata.pair
                receipt = self._send_substrate_tx(call, self.__metadata.pair)
                return WrittenTransactionResult(
                    message=f"Successfully removed the storage item type {item_type} for the address {keypair.ss58_address}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed remove_item call object for peaq storage with item type {item_type}. You must sign and send it externally.",
                    call=call
                )