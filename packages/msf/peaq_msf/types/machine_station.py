"""TODO"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from .common import WrittenTransactionResult, TxOptions, EvmSendResult
from .base import TransactionStatusCallback
from web3.types import TxParams
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

@dataclass(kw_only=True)
class DeployedSmartAccountResult(EvmSendResult):
    """Result object for smart account deployment containing both transaction info and the deployed address"""
    message: str
    deployed_address: str

# Base dataclass for transaction data objects
@dataclass
class MachineStationTransactionData:
    """Base class for machine station transaction data when send_transaction=False"""
    transaction_data: TxParams
    message: str
    machine_station_address: str
    function: str

@dataclass
class UpdateConfigsTransactionData(MachineStationTransactionData):
    """Transaction data for update_configs function"""
    config_key: str
    config_value: int
    required_role: str

@dataclass
class DeployMachineSmartAccountTransactionData(MachineStationTransactionData):
    """Transaction data for deploy_machine_smart_account function"""
    machine_account_owner_address: str
    required_role: str
    note: str

@dataclass
class TransferMachineStationBalanceTransactionData(MachineStationTransactionData):
    """Transaction data for execute_transfer_machine_station_balance function"""
    current_machine_station_address: str
    new_machine_station_address: str
    required_role: str

@dataclass
class ExecuteTransactionData(MachineStationTransactionData):
    """Transaction data for execute_transaction function"""
    target: str
    access_control: str

@dataclass
class ExecuteMachineTransactionData(MachineStationTransactionData):
    """Transaction data for execute_machine_transaction function"""
    machine_account_address: str
    target: str
    access_control: str

@dataclass
class ExecuteMachineBatchTransactionsData(MachineStationTransactionData):
    """Transaction data for execute_machine_batch_transactions function"""
    machine_account_addresses: List[str]
    targets: List[str]
    description: str
    access_control: str

@dataclass
class ExecuteTransferMachineBalanceData(MachineStationTransactionData):
    """Transaction data for execute_transfer_machine_balance function"""
    machine_account_address: str
    recipient_address: str
    required_role: str

# Signable message objects
@dataclass
class EIP712SignableMessage:
    """EIP-712 signable message object for frontend signing"""
    domain: Dict[str, Any]
    types: Dict[str, Any]
    message: Dict[str, Any]
    primaryType: str

# Result types
@dataclass(kw_only=True)
class MachineStationWriteResult(WrittenTransactionResult):
    """Result for machine station write operations"""
    pass


# Admin signature options
@dataclass
class AdminSignDeployMachineSmartAccountOptions:
    """Options for admin signing machine smart account deployment"""
    machine_account_owner_address: str
    nonce: int
    note: Optional[str] = None

@dataclass
class AdminSignTransferMachineStationBalanceOptions:
    """Options for admin signing machine station balance transfer"""
    new_machine_station_address: str
    nonce: int

@dataclass
class AdminSignTransactionOptions:
    """Options for admin signing transaction execution"""
    target: str
    calldata: str
    value: int
    nonce: int

@dataclass
class AdminSignMachineTransactionOptions:
    """Options for admin signing machine transaction"""
    machine_account_address: str
    target: str
    calldata: str
    value: int
    nonce: int
    refund_amount: Optional[int] = 0

@dataclass
class AdminSignMachineBatchTransactionsOptions:
    """Options for admin signing batch machine transactions"""
    machine_account_addresses: List[str]
    targets: List[str]
    calldata_list: List[str]
    values: List[int]
    nonce: int

@dataclass
class AdminSignTransferMachineBalanceOptions:
    """Options for admin signing machine balance transfer"""
    machine_account_address: str
    recipient_address: str
    amount: int
    nonce: int

# Machine signature options
@dataclass
class MachineSignMachineTransactionOptions:
    """Options for machine owner signing machine transaction"""
    machine_account_address: str
    target: str
    calldata: str
    value: int
    nonce: int

@dataclass
class MachineSignTransferMachineBalanceOptions:
    """Options for machine owner signing balance transfer"""
    machine_account_address: str
    recipient_address: str
    amount: int
    nonce: int