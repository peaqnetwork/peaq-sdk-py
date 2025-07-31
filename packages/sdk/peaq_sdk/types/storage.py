"""objects used in storage class"""
# python native imports
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class GetItemResult(BaseModel):
    """Result object for storage item retrieval operations"""
    item_type: str = Field(..., description="Type identifier for the retrieved item")
    item: str = Field(..., description="The actual item content")
    
    def to_dict(self):
        """Convert result to dictionary format"""
        return {self.item_type: self.item}
    
class RemoveItemResult(BaseModel):
    """Result object for storage item removal operations"""
    message: str = Field(..., description="Success or informational message about the removal")
    receipt: dict = Field(..., description="Transaction receipt from the removal operation")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True  # Allow dict type for receipt
    )

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