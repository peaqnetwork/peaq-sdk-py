# python native imports
from typing import Optional
import json
from enum import Enum

# local imports
from src.modules.base import Base
from src.types.common import ChainType, SDKMetadata, PrecompileAddresses, CallModule, EvmTransaction
from src.types.storage import CreateStorageOptions, GetItemOptions, GetItemError, StorageFunctionSignatures, StorageCallFunction
from src.utils.utils import evm_to_address

# 3rd party imports
from substrateinterface.base import SubstrateInterface
from web3 import Web3
from eth_abi import encode

class Storage(Base):
    def __init__(self, api, metadata) -> None:
        super().__init__()
        self._api = api
        self.__metadata: SDKMetadata = metadata

    def add_item(self, item_type: str, item: object):
        # check if args are correct
        args = CreateStorageOptions(item_type, item)
        
        # convert in case user wants to set a dict value
        item_string = item if isinstance(item, str) else json.dumps(item)
                
        # check if EVM or Substrate
        if self.__metadata.chain_type is ChainType.EVM:
            account = self.__metadata.pair
            add_item_function_selector = self._api.keccak(text=StorageFunctionSignatures.ADD_ITEM.value)[:4].hex()
            item_type = item_type.encode("utf-8").hex()
            final_item = item_string.encode("utf-8").hex()
            
            # Create the encoded parameters to create calldata
            encoded_params = encode(
                ['bytes', 'bytes'],
                [bytes.fromhex(item_type), bytes.fromhex(final_item)]
            ).hex()
            
            payload = "0x" + add_item_function_selector + encoded_params
            tx: EvmTransaction = {
                "to": PrecompileAddresses.STORAGE.value,
                "data": payload
            }
            
            receipt = self.send_evm_tx(tx, account)
            return receipt
        else:
            # Will be substrate if EVM is not set
            # Check if api is connected
            keypair = self.__metadata.pair
            call = self._api.compose_call(
                call_module=CallModule.PEAQ_STORAGE.value,
                call_function=StorageCallFunction.ADD_ITEM.value,
                call_params={
                'item_type': args.item_type,
                'item': item_string,
                }
            )
            receipt = self.send_substrate_tx(call, keypair)
            return { 
                "message": f"Successfully added the storage item type {args.item_type} with item {args.item} for the address {keypair.ss58_address}",
                "block_hash": f"{receipt.block_hash}"
            }
        
    def get_item(self, item_type: str, address: Optional[str] = None, wss_base_url: Optional[str] = None): 
        args = GetItemOptions(item_type, address)
        
        # check if EVM or Substrate
        if self.__metadata.chain_type is ChainType.EVM:
            account = self.__metadata.pair
            kp_address = evm_to_address(account.address)
            
            # force api change for easy read; why wss is required
            self._api = SubstrateInterface(url=wss_base_url, ss58_format=42)
            # convert address to substrate if evm; can use the same logic
        else:
            keypair = self.__metadata.pair
            kp_address = keypair.ss58_address
        
        # same read logic
        item_type_hex = "0x" + args.item_type.encode("utf-8").hex()
        block_hash = self._api.get_block_hash(None)
        data = self._api.rpc_request(
            StorageCallFunction.GET_ITEM.value,
            [
                kp_address, 
                item_type_hex, 
                block_hash
            ]
        )
        
        # Check result
        if data['result'] is None:
            raise GetItemError(f"Item type of {args.item_type} was not found at address {kp_address}.") 
        
        get_item = data['result']['item']
        human_readable_item = bytes.fromhex(get_item[2:]).decode("utf-8")
        return {
            args.item_type: human_readable_item
        }
        
    def update_item():
        pass
    def remove_item():
        pass