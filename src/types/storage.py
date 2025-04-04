"""objects used in storage class"""
# python native imports
from dataclasses import dataclass
from typing import Optional
from enum import Enum

@dataclass
class CreateStorageOptions:
    item_type: str
    item: object

@dataclass
class GetItemOptions:
    item_type: str
    address: Optional[str]
    

# Used for Storage EVM precompiles
class StorageFunctionSignatures(str, Enum):
    ADD_ITEM = "addItem(bytes,bytes)"
    GET_ITEM = "getItem(address,bytes)"
    UPDATE_ITEM = "updateItem(bytes,bytes)"
    REMOVE_ITEM = "removeItem(bytes)"

class StorageCallFunction(str, Enum):
    ADD_ITEM = 'add_item'
    GET_ITEM = 'peaqstorage_readAttribute'
    UPDATE_ITEM = 'update_item'
    REMOVE_ITEM = 'remove_item'

# Custom Errors
class GetItemError(Exception):
    """Raised when there is a failure to the function get item."""
    pass