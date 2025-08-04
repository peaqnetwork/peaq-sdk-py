"""TODO"""

from typing import List, Optional, Dict, Any, Union
from enum import Enum
from .base import TransactionStatusCallback, EvmSendResult
from web3.types import TxParams
from eth_utils import keccak
from pydantic import BaseModel, Field, ConfigDict

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
    
class UpdateConfigsOptions(BaseModel):
    """Options for updating machine station configuration"""
    key: MachineStationConfigKeys = Field(..., description="Configuration key to update")
    value: int = Field(..., description="New value for the configuration key")
    send_transaction: bool = Field(True, description="Whether to send transaction automatically")
    
class DeployMachineSmartAccountOptions(BaseModel):
    """Options for deploying machine smart account"""
    machine_owner_address: str = Field(..., description="Address of the machine account owner")
    nonce: int = Field(..., description="Nonce for the deployment")
    station_manager_signature: str = Field(..., description="Signature from station manager")
    send_transaction: bool = Field(True, description="Whether to send transaction automatically")
    
class AdminSignDeployMachineSmartAccountOptions(BaseModel):
    """Options for admin signing machine smart account deployment"""
    machine_owner_address: str = Field(..., description="Address of the machine account owner")
    nonce: int = Field(..., description="Nonce for the deployment")
    
MachineStationWriteResult = EvmSendResult

class DeployedSmartAccountResult(EvmSendResult):
    """Result object for smart account deployment containing both transaction info and the deployed address"""
    message: str = Field(..., description="Human-readable success message")
    deployed_address: str = Field(..., description="Address of the deployed smart account")
    receipt: Any = Field(..., description="Transaction receipt data")
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
# Base model for transaction data objects
class MachineStationTransactionData(BaseModel):
    """Base class for machine station transaction data when send_transaction=False"""
    transaction_data: TxParams = Field(..., description="Transaction parameters")
    message: str = Field(..., description="Human-readable message")
    machine_station_address: str = Field(..., description="Address of the machine station contract")
    function: str = Field(..., description="Name of the function being called")
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class UpdateConfigsTransactionData(MachineStationTransactionData):
    """Transaction data for update_configs function"""
    config_key: str = Field(..., description="Configuration key being updated")
    config_value: int = Field(..., description="New value for the configuration")
    required_role: str = Field(..., description="Role required to execute this transaction")

class DeployMachineSmartAccountTransactionData(MachineStationTransactionData):
    """Transaction data for deploy_machine_smart_account function"""
    machine_account_owner_address: str = Field(..., description="Address of the machine account owner")
    required_role: str = Field(..., description="Role required to execute this transaction")
    note: str = Field(..., description="Additional information about the transaction")

class TransferMachineStationBalanceTransactionData(MachineStationTransactionData):
    """Transaction data for execute_transfer_machine_station_balance function"""
    current_machine_station_address: str = Field(..., description="Current machine station address")
    new_machine_station_address: str = Field(..., description="New machine station address")
    required_role: str = Field(..., description="Role required to execute this transaction")

class ExecuteTransactionData(MachineStationTransactionData):
    """Transaction data for execute_transaction function"""
    target: str = Field(..., description="Target contract address")
    access_control: str = Field(..., description="Access control information")

class ExecuteMachineTransactionData(MachineStationTransactionData):
    """Transaction data for execute_machine_transaction function"""
    machine_account_address: str = Field(..., description="Machine account address")
    target: str = Field(..., description="Target contract address")
    access_control: str = Field(..., description="Access control information")

class ExecuteMachineBatchTransactionsData(MachineStationTransactionData):
    """Transaction data for execute_machine_batch_transactions function"""
    machine_account_addresses: List[str] = Field(..., description="List of machine account addresses")
    targets: List[str] = Field(..., description="List of target contract addresses")
    description: str = Field(..., description="Description of the batch transaction")
    access_control: str = Field(..., description="Access control information")

class ExecuteTransferMachineBalanceData(MachineStationTransactionData):
    """Transaction data for execute_transfer_machine_balance function"""
    machine_account_address: str = Field(..., description="Machine account address")
    recipient_address: str = Field(..., description="Recipient address")
    required_role: str = Field(..., description="Role required to execute this transaction")

# Signable message objects
class EIP712SignableMessage(BaseModel):
    """EIP-712 signable message object for frontend signing"""
    domain: Dict[str, Any] = Field(..., description="EIP-712 domain")
    types: Dict[str, Any] = Field(..., description="EIP-712 types")
    message: Dict[str, Any] = Field(..., description="EIP-712 message")
    primaryType: str = Field(..., description="Primary type for EIP-712")



# Admin signature options
class AdminSignTransferMachineStationBalanceOptions(BaseModel):
    """Options for admin signing machine station balance transfer"""
    new_machine_station_address: str = Field(..., description="New machine station address")
    nonce: int = Field(..., description="Nonce for the transaction")

class AdminSignTransactionOptions(BaseModel):
    """Options for admin signing transaction execution"""
    target: str = Field(..., description="Target contract address")
    calldata: str = Field(..., description="Transaction calldata")
    value: int = Field(..., description="Transaction value")
    nonce: int = Field(..., description="Nonce for the transaction")

class AdminSignMachineTransactionOptions(BaseModel):
    """Options for admin signing machine transaction"""
    machine_account_address: str = Field(..., description="Machine account address")
    target: str = Field(..., description="Target contract address")
    calldata: str = Field(..., description="Transaction calldata")
    value: int = Field(..., description="Transaction value")
    nonce: int = Field(..., description="Nonce for the transaction")
    refund_amount: Optional[int] = Field(0, description="Refund amount")

class AdminSignMachineBatchTransactionsOptions(BaseModel):
    """Options for admin signing batch machine transactions"""
    machine_account_addresses: List[str] = Field(..., description="List of machine account addresses")
    targets: List[str] = Field(..., description="List of target contract addresses")
    calldata_list: List[str] = Field(..., description="List of transaction calldata")
    values: List[int] = Field(..., description="List of transaction values")
    nonce: int = Field(..., description="Nonce for the transaction")

class AdminSignTransferMachineBalanceOptions(BaseModel):
    """Options for admin signing machine balance transfer"""
    machine_account_address: str = Field(..., description="Machine account address")
    recipient_address: str = Field(..., description="Recipient address")
    amount: int = Field(..., description="Transfer amount")
    nonce: int = Field(..., description="Nonce for the transaction")

# Machine signature options
class MachineSignMachineTransactionOptions(BaseModel):
    """Options for machine owner signing machine transaction"""
    machine_account_address: str = Field(..., description="Machine account address")
    target: str = Field(..., description="Target contract address")
    calldata: str = Field(..., description="Transaction calldata")
    value: int = Field(..., description="Transaction value")
    nonce: int = Field(..., description="Nonce for the transaction")

class MachineSignTransferMachineBalanceOptions(BaseModel):
    """Options for machine owner signing balance transfer"""
    machine_account_address: str = Field(..., description="Machine account address")
    recipient_address: str = Field(..., description="Recipient address")
    amount: int = Field(..., description="Transfer amount")
    nonce: int = Field(..., description="Nonce for the transaction")