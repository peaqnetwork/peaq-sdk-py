# python native imports
from typing import Optional
import json
from enum import Enum

# local imports
from src.modules.base import Base
from src.types.common import ChainType, SDKMetadata, PrecompileAddresses, CallModule, EvmTransaction, TransactionResult, SeedError
from src.types.storage import CreateStorageOptions, GetItemOptions, GetItemError, StorageFunctionSignatures, StorageCallFunction, UpdateStorageOptions, AddItemResult, GetItemResult, UpdateItemResult, RemoveItemResult
from src.utils.utils import evm_to_address

# 3rd party imports
from substrateinterface.base import SubstrateInterface
from web3 import Web3
from eth_abi import encode

"""Storage class that performs EVM and Substrate txs to utilize the peaq
storage capabilities."""
class Storage(Base):
    def __init__(self, api, metadata) -> None:
        """Sets previously set api and metadata to be used in the class."""
        super().__init__()
        self._api = api
        self.__metadata: SDKMetadata = metadata

    def add_item(
        self, 
        item_type: str, 
        item: object
        ) -> AddItemResult:
        if not self.__metadata.pair:
            raise SeedError(f"No seed/private key set for the operation 'add_item'. Unable to perform the write transaction.")
        
        # convert in case user wants to set a dict value
        item_string = item if isinstance(item, str) else json.dumps(item)
                
        # check if EVM or Substrate
        if self.__metadata.chain_type is ChainType.EVM:
            account = self.__metadata.pair
            add_item_function_selector = self._api.keccak(text=StorageFunctionSignatures.ADD_ITEM.value)[:4].hex()
            item_type_encoded = item_type.encode("utf-8").hex()
            final_item = item_string.encode("utf-8").hex()
            
            # Create the encoded parameters to create calldata
            encoded_params = encode(
                ['bytes', 'bytes'],
                [bytes.fromhex(item_type_encoded), bytes.fromhex(final_item)]
            ).hex()
            
            payload = "0x" + add_item_function_selector + encoded_params
            tx: EvmTransaction = {
                "to": PrecompileAddresses.STORAGE.value,
                "data": payload
            }
            
            receipt = self.send_evm_tx(tx, account)
            return AddItemResult(
                message=f"Successfully added the storage item type {item_type} with item {item} for the address {account.address}",
                receipt=receipt
            )
        else:
            # Will be substrate if EVM is not set
            # Check if api is connected
            keypair = self.__metadata.pair
            call = self._api.compose_call(
                call_module=CallModule.PEAQ_STORAGE.value,
                call_function=StorageCallFunction.ADD_ITEM.value,
                call_params={
                'item_type': item_type,
                'item': item_string,
                }
            )
            receipt = self.send_substrate_tx(call, keypair)
            return AddItemResult(
                message=f"Successfully added the storage item type {item_type} with item {item} for the address {keypair.ss58_address}",
                receipt=receipt
            )
        
    def get_item(
        self, 
        item_type: str, 
        address: Optional[str] = None, 
        wss_base_url: Optional[str] = None
        ) -> GetItemResult:
        
        # check if EVM or Substrate
        if self.__metadata.chain_type is ChainType.EVM:
            evm_address = getattr(self.__metadata.pair, 'address', address) if self.__metadata.pair else address
            if not evm_address:
                raise TypeError(f"Address is set to {evm_address}. Please either set seed at instance creation or pass an address.")
            # convert address to substrate if evm
            owner_address = evm_to_address(evm_address)
            
            # force api change for easy read - which is why wss is required
            api = SubstrateInterface(url=wss_base_url, ss58_format=42)
        else:
            owner_address = getattr(self.__metadata.pair, 'ss58_address', address) if self.__metadata.pair else address
            if not owner_address:
                raise TypeError(f"Address is set to {owner_address}. Please either set seed at instance creation or pass an address.")
            api = self._api
        
        # same read logic
        item_type_hex = "0x" + item_type.encode("utf-8").hex()
        block_hash = api.get_block_hash(None)
        data = api.rpc_request(
            StorageCallFunction.GET_ITEM.value,
            [
                owner_address, 
                item_type_hex, 
                block_hash
            ]
        )
        
        # Check result
        if data['result'] is None:
            raise GetItemError(f"Item type of {item_type} was not found at address {owner_address}.") 
        
        get_item = data['result']['item']
        human_readable_item = bytes.fromhex(get_item[2:]).decode("utf-8")
        return GetItemResult(
            item_type=item_type,
            item=human_readable_item).to_dict()
        
    def update_item(
        self, 
        item_type: str, 
        item: object
    ) -> UpdateItemResult:
        if not self.__metadata.pair:
            raise SeedError(f"No seed/private key set for the operation 'update_item'. Unable to perform the write transaction.")
        
        # convert in case user wants to set a dict value
        item_string = item if isinstance(item, str) else json.dumps(item)
        
        # check if EVM or Substrate
        if self.__metadata.chain_type is ChainType.EVM:
            account = self.__metadata.pair
            update_item_function_selector = self._api.keccak(text=StorageFunctionSignatures.UPDATE_ITEM.value)[:4].hex()
            item_type_encoded = item_type.encode("utf-8").hex()
            final_item = item_string.encode("utf-8").hex()
            
            # Create the encoded parameters to create calldata
            encoded_params = encode(
                ['bytes', 'bytes'],
                [bytes.fromhex(item_type_encoded), bytes.fromhex(final_item)]
            ).hex()
            
            payload = "0x" + update_item_function_selector + encoded_params
            tx: EvmTransaction = {
                "to": PrecompileAddresses.STORAGE.value,
                "data": payload
            }
            
            receipt = self.send_evm_tx(tx, account)
            return UpdateItemResult(
                message=f"Successfully updated the storage item type {item_type} with item {item} for the address {account.address}",
                receipt=receipt
            )
        else:
            # Will be substrate if EVM is not set
            # Check if api is connected
            keypair = self.__metadata.pair
            call = self._api.compose_call(
                call_module=CallModule.PEAQ_STORAGE.value,
                call_function=StorageCallFunction.UPDATE_ITEM.value,
                call_params={
                'item_type': item_type,
                'item': item_string,
                }
            )
            receipt = self.send_substrate_tx(call, keypair)
            return UpdateItemResult(
                message=f"Successfully updated the storage item type {item_type} with item {item} for the address {keypair.ss58_address}",
                receipt=receipt
            )
            
    def remove_item(
        self,
        item_type: str,
    ) -> RemoveItemResult:
        if not self.__metadata.pair:
            raise SeedError(f"No seed/private key set for the operation 'add_item'. Unable to perform the write transaction.")
        
        # check if EVM or Substrate
        if self.__metadata.chain_type is ChainType.EVM:
            raise ValueError("Precompile for peaq Storage Remove Item will be included in the next runtime update.")
            account = self.__metadata.pair
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
            
            receipt = self.send_evm_tx(tx, account)
            return RemoveItemResult(
                message=f"Successfully removed the storage item type {item_type} for the address {account.address}",
                receipt=receipt
            )
        else:
            # Will be substrate if EVM is not set
            # Check if api is connected
            keypair = self.__metadata.pair
            call = self._api.compose_call(
                call_module=CallModule.PEAQ_STORAGE.value,
                call_function=StorageCallFunction.REMOVE_ITEM.value,
                call_params={
                'item_type': item_type
                }
            )
            receipt = self.send_substrate_tx(call, keypair)
            return RemoveItemResult(
                message=f"Successfully removed the storage item type {item_type} for the address {keypair.ss58_address}",
                receipt=receipt
            )