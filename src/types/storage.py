"""objects used in storage class"""
# python native imports
from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateStorageOptions:
    item_type: str
    item: object

@dataclass
class GetItemOptions:
    item_type: str
    address: Optional[str]
    



# Custom Errors
class GetItemError(Exception):
    """Raised when there is a failure to the function get item."""
    pass