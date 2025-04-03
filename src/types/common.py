"""commonly shared objects across the sdk"""
# python native imports
from enum import Enum


class ChainType(Enum):
    EVM = "evm"
    SUBSTRATE = "substrate"