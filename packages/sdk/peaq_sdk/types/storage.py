"""objects used in storage class"""
# python native imports
from typing import Optional, Union, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

# Import the structured return types
from peaq_sdk.types.base import (
    SubstrateSendResult,
    EvmSendResult,
    BuiltEvmTransactionResult,
    BuiltCallTransactionResult
)

# Storage operation option types
class AddItemOptions(BaseModel):
    """Options for adding an item to storage"""
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    item_type: str = Field(..., alias="itemType", description="The key under which to store the item")
    item: Any = Field(..., description="The value to store (string or any serializable object)")

class RemoveItemOptions(BaseModel):
    """Options for removing an item from storage"""
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    item_type: str = Field(..., alias="itemType", description="The key of the item to remove")

class UpdateItemOptions(BaseModel):
    """Options for updating an item in storage"""
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    item_type: str = Field(..., alias="itemType", description="The key of the item to update")
    item: Any = Field(..., description="The new value to replace the existing stored value")

class GetItemOptions(BaseModel):
    """Options for retrieving an item from storage"""
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    item_type: str = Field(..., alias="itemType", description="The key under which the item was stored")
    address: Optional[str] = Field(None, description="Optional address whose data is being queried. If not provided, the address from the local signer (if any) is used")

# Storage result types
StorageWriteResult = Union[SubstrateSendResult, EvmSendResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]

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