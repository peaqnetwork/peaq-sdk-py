from src.modules.base import Base
from src.types.common import ChainType, SDKMetadata
from src.types.storage import CreateStorageOptions


class Storage(Base):
    def __init__(self, api, metadata) -> None:
        super().__init__()
        self._api = api
        self.__metadata: SDKMetadata = metadata
    def add_item(self, item_type: str, item: object):
        # check if args are correct
        args = CreateStorageOptions(item_type, item)
        
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
            'item': args.item,
            }
        )
        receipt = self.send_substrate_tx(call, keypair)
        return { 
            "message": f"Successfully added the storage item type {args.item_type} with item {args.item} for the address {keypair.ss58_address}",
            "block_hash": f"{receipt.block_hash}"
        }
        
    def read_item():
        pass
    def update_item():
        pass
    def remove_item():
        pass