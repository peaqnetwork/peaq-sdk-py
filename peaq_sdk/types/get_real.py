"""TODO"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

# Used for Storage EVM precompiles
class MachineStartionFactoryFunctionSignatures(str, Enum):
    ADD_ATTRIBUTE = "addAttribute(address,bytes,bytes,uint32)"
    READ_ATTRIBUTE = "readAttribute(address,bytes)"
    UPDATE_ATTRIBUTE = "updateAttribute(address,bytes,bytes,uint32)"
    REMOVE_ATTRIBUTE = "removeAttribute(address,bytes)"

