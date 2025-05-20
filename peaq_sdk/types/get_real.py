"""TODO"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

# Used for Machine Station Factory Smart Contract
class MachineStationFactoryFunctionSignatures(str, Enum):
    DEPLOY_MACHINE_SMART_ACCOUNT = "deployMachineSmartAccount(address,uint256,bytes)"
    TRANSFER_MACHINE_STATION_BALANCE = "transferMachineStationBalance(address,uint256,bytes)"
    EXECUTE_TRANSACTION = "executeTransaction(address,bytes,uint256,bytes)"
    REMOVE_ATTRIBUTE = "removeAttribute(address,bytes)"

