"""TODO"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from peaq_sdk.types.common import WrittenTransactionResult
from eth_utils import keccak

# Used for Machine Station Factory Smart Contract
class MachineStationFactoryFunctionSignatures(str, Enum):
    UPDATE_CONFIGS = "updateConfigs(bytes32,uint256)"
    DEPLOY_MACHINE_SMART_ACCOUNT = "deployMachineSmartAccount(address,uint256,bytes)"
    TRANSFER_MACHINE_STATION_BALANCE = "transferMachineStationBalance(address,uint256,bytes)"
    EXECUTE_TRANSACTION = "executeTransaction(address,bytes,uint256,uint256,bytes)"
    EXECUTE_MACHINE_TRANSACTION = "executeMachineTransaction(address,address,bytes,uint256,uint256,bytes,bytes)"
    EXECUTE_MACHINE_BATCH_TRANSACTIONS = "executeMachineBatchTransactions(address[],address[],bytes[],uint256,uint256,uint256[],bytes,bytes[])"
    EXECUTE_MACHINE_TRANSFER_BALANCE = "executeMachineTransferBalance(address,address,uint256,bytes,bytes)"

# Configuration keys for Machine Station Factory Smart Contract
class MachineStationConfigKeys(str, Enum):
    TX_FEE_REFUND_AMOUNT_KEY = keccak(text="TX_FEE_REFUND_AMOUNT").hex()
    IS_REFUND_ENABLED_KEY = keccak(text="IS_REFUND_ENABLED").hex()
    CHECK_REFUND_MIN_BALANCE_KEY = keccak(text="CHECK_REFUND_MIN_BALANCE").hex()
    MIN_BALANCE_KEY = keccak(text="MIN_BALANCE").hex() 
    FUNDING_AMOUNT_KEY = keccak(text="FUNDING_AMOUNT").hex()

@dataclass
class DeployedSmartAccountResult(WrittenTransactionResult):
    """Result object for smart account deployment containing both transaction info and the deployed address"""
    deployed_address: str