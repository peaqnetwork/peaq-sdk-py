"""objects used in storage class"""
# python native imports
from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateStorageOptions:
    item_type: str
    item: object