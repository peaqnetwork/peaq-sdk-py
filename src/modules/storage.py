from src.modules.base import Base
from src.types.common import ChainType, SDKMetadata
from src.types.storage import CreateStorageOptions, GetItemOptions, GetItemError

from typing import Optional
import json



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
            pass
        
        # Check if api is connected
        keypair = self.__metadata.pair
        call = self._api.compose_call(
            call_module='PeaqStorage',
            call_function='add_item',
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
        
    def get_item(self, item_type: str, address: Optional[str] = None): 
        args = GetItemOptions(item_type, address)
        
        # check if EVM or Substrate
        if self.__metadata.chain_type is ChainType.EVM:
            pass
        
        # logic to check if address is set, use that -> if not use keypair
        
        keypair = self.__metadata.pair
        kp_address = keypair.ss58_address
        item_type_hex = "0x" + args.item_type.encode("utf-8").hex()
        block_hash = self._api.get_block_hash(None)
        data = self._api.rpc_request(
            'peaqstorage_readAttribute',
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