"""TODO"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

# Used for Machine Station Factory Smart Contract
class MachineStationFactoryFunctionSignatures(str, Enum):
    DEPLOY_MACHINE_SMART_ACCOUNT = "deployMachineSmartAccount(address,uint256,bytes)"
    TRANSFER_MACHINE_STATION_BALANCE = "transferMachineStationBalance(address,uint256,bytes)"
    EXECUTE_TRANSACTION = "executeTransaction(address,bytes,uint256,bytes)"
    EXECUTE_MACHINE_TRANSACTION = "executeMachineTransaction(address,address,bytes,uint256,bytes,bytes)"
    EXECUTE_MACHINE_BATCH_TRANSACTIONS = "executeMachineBatchTransactions(address[],address[],bytes[],uint256,uint256[],bytes,bytes[])"
    EXECUTE_MACHINE_TRANSFER_BALANCE = "executeMachineTransferBalance(address,address,uint256,bytes,bytes)"
    
    

