"""
MSF Main class - Entry point for the Machine Station SDK.

The Main class serves as the primary interface for interacting with Machine Station Factory
smart contracts on EVM-compatible blockchains. It provides methods for initializing web3
signers, creating JsonRpcProvider connections, and managing machine station operations.
This is a standalone module that only supports EVM chains via web3.py.
"""

from typing import Union, Optional, Callable, Awaitable
from web3 import Web3, AsyncWeb3, AsyncHTTPProvider
from eth_account.signers.base import BaseAccount

from .base import Base
from .utils.utils import parse_options
from .machine_station import MachineStation
from .types.common import ChainType, SDKMetadata, CreateInstanceOptions
from .types.base import TransactionStatusCallback, StatusCallback, TxOptions
from .types.machine_station import (
    MachineStationWriteResult,
    DeployedSmartAccountResult,
    EIP712SignableMessage,
    UpdateConfigsTransactionData,
    UpdateConfigsOptions,
    DeployMachineSmartAccountOptions,
    AdminSignDeployMachineSmartAccountOptions,
    TransferMachineStationBalanceOptions,
    AdminSignTransferMachineStationBalanceOptions,
    ExecuteTransactionOptions,
    AdminSignExecuteTransactionOptions,
    ExecuteMachineTransactionOptions,
    AdminSignMachineTransactionOptions,
    MachineSignMachineTransactionOptions,
    ExecuteMachineBatchTransactionsOptions,
    AdminSignMachineBatchTransactionsOptions,
    ExecuteMachineTransferBalanceOptions,
    AdminSignTransferMachineBalanceOptions,
    MachineSignTransferMachineBalanceOptions,
    DeployMachineSmartAccountTransactionData,
    TransferMachineStationBalanceTransactionData,
    ExecuteTransactionData,
    ExecuteMachineTransactionData,
    ExecuteMachineBatchTransactionsData,
    ExecuteTransferMachineBalanceData
)


class Main(Base):
    """
    Entry point for the Machine Station SDK.
    
    The Main class serves as the primary interface for interacting with Machine Station Factory
    smart contracts on EVM-compatible blockchains. It provides methods for initializing web3
    signers, creating Web3 connections, and managing machine station operations.
    This is a standalone module that only supports EVM chains via web3.py.
    """

    def __init__(self, options: CreateInstanceOptions):
        """
        Initializes the Main class with machine station functionality for EVM operations.
        
        Args:
            options: Configuration options for the machine station instance including EVM RPC URL and signers
        """
        metadata = SDKMetadata(
            base_url=options.base_url,
            chain_type=ChainType.EVM,
            pair=None
        )

        api = self._create_api(metadata)
        super().__init__(api, metadata)

        # Initialize machine station with properly connected signers
        self._machine_station = MachineStation(
            api,
            metadata,
            options.machine_station_address,
            options.station_admin,
            options.station_manager
        )

    @classmethod
    async def create_instance(cls, options: CreateInstanceOptions) -> "Main":
        """
        Creates and returns a new instance of the Machine Station SDK configured for EVM operations.
        
        Args:
            options: Configuration options including EVM RPC base_url, machine_station_address, 
                    station_admin, and optional station_manager signers
                    
        Returns:
            An initialized Machine Station SDK instance ready for smart contract interactions
        """
        ops = parse_options(CreateInstanceOptions, options, caller="create_instance()")
        sdk = cls(ops)
        
        # Set the station admin as the primary signer for base operations
        sdk._set_signer(ops.station_admin)

        return sdk

    def _create_api(self, metadata: SDKMetadata) -> Web3:
        """
        Creates an EVM Web3 instance for connecting to EVM-compatible blockchains.
        """
        base_url = metadata.base_url
        chain_type = metadata.chain_type

        if chain_type == ChainType.EVM:
            if not base_url.startswith('https://'):
                raise ValueError('Invalid base URL for EVM chain. Must start with https://')
            return AsyncWeb3(AsyncHTTPProvider(base_url))

        else:
            raise ValueError('Only EVM chain type is supported by Machine Station SDK')

    # =====================================================================
    # CONFIGURATION METHODS
    # =====================================================================

    async def update_configs(
        self,
        options: UpdateConfigsOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> Union[MachineStationWriteResult, UpdateConfigsTransactionData]:
        """
        Updates configuration values in the machine station factory contract.
        
        **Transaction Execution**: Requires STATION_MANAGER_ROLE
        
        Args:
            options: UpdateConfigsOptions object containing 'key', 'value' and optional 'send_transaction'
            status_callback: Optional callback for monitoring transaction status
            tx_options: Optional transaction confirmation mode settings
            
        Returns:
            Promise resolving to transaction result or transaction data
        """
        return await self._machine_station.update_configs(options, status_callback, tx_options)

    # =====================================================================
    # SMART ACCOUNT DEPLOYMENT METHODS
    # =====================================================================

    async def deploy_machine_smart_account(
        self,
        options: DeployMachineSmartAccountOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> Union[DeployedSmartAccountResult, DeployMachineSmartAccountTransactionData]:
        """
        Deploys a new machine smart account through the factory contract.
        
        **Transaction Execution**: Requires STATION_MANAGER_ROLE
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: DeployMachineSmartAccountOptions object containing machine owner address, nonce, signature and optional send_transaction.
            status_callback: Optional callback for monitoring transaction status
            tx_options: Optional transaction confirmation mode settings
            
        Returns:
            Promise resolving to deployment result with the new account address or transaction data
        """
        return await self._machine_station.deploy_machine_smart_account(options, status_callback, tx_options)

    # =====================================================================
    # BALANCE TRANSFER METHODS
    # =====================================================================

    async def transfer_machine_station_balance(
        self,
        options: TransferMachineStationBalanceOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> Union[MachineStationWriteResult, TransferMachineStationBalanceTransactionData]:
        """
        Transfers the machine station balance to a new machine station address.
        
        **Transaction Execution**: Requires DEFAULT_ADMIN_ROLE
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: TransferMachineStationBalanceOptions object containing new address, nonce, signature and optional send_transaction
            status_callback: Optional callback for monitoring transaction status
            tx_options: Optional transaction confirmation mode settings
            
        Returns:
            Promise resolving to transfer result or transaction data
        """
        return await self._machine_station.transfer_machine_station_balance(options, status_callback, tx_options)

    # =====================================================================
    # TRANSACTION EXECUTION METHODS
    # =====================================================================

    async def execute_transaction(
        self,
        options: ExecuteTransactionOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> Union[MachineStationWriteResult, ExecuteTransactionData]:
        """
        Executes a transaction through the machine station factory.
        
        **Transaction Execution**: No specific role required (anyone can call)
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: ExecuteTransactionOptions object containing target, calldata, nonce, refund_amount, machine_station_owner_signature and optional send_transaction
            status_callback: Optional callback for monitoring transaction status
            tx_options: Optional transaction confirmation mode settings
            
        Returns:
            Promise resolving to transaction result or transaction data
        """
        return await self._machine_station.execute_transaction(options, status_callback, tx_options)

    async def execute_machine_transaction(
        self,
        options: ExecuteMachineTransactionOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> Union[MachineStationWriteResult, ExecuteMachineTransactionData]:
        """
        Executes a transaction on behalf of a machine smart account.
        
        **Transaction Execution**: No specific role required (anyone can call)
        **Signature Generation Machine**: Must be signed by the machine owner
        **Signature Generation Admin**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: ExecuteMachineTransactionOptions object containing machine_address, target, calldata, nonce, refund_amount, signatures and optional send_transaction
            status_callback: Optional callback for monitoring transaction status
            tx_options: Optional transaction confirmation mode settings
            
        Returns:
            Promise resolving to MachineStationWriteResult if sent, or ExecuteMachineTransactionData if send_transaction=False
        """
        return await self._machine_station.execute_machine_transaction(options, status_callback, tx_options)

    async def execute_machine_batch_transactions(
        self,
        options: ExecuteMachineBatchTransactionsOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> Union[MachineStationWriteResult, ExecuteMachineBatchTransactionsData]:
        """
        Executes multiple transactions in a batch on behalf of machine smart accounts.
        
        **Transaction Execution**: No specific role required (anyone can call)
        **Signature Generation Machine**: Must be signed by the machine owner
        **Signature Generation Admin**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: ExecuteMachineBatchTransactionsOptions object containing machine_addresses, targets, calldata_list, nonce, refund_amount, machine_nonces, signatures and optional send_transaction
            status_callback: Optional callback for monitoring transaction status
            tx_options: Optional transaction confirmation mode settings
            
        Returns:
            Promise resolving to MachineStationWriteResult if sent, or ExecuteMachineBatchTransactionsData if send_transaction=False
        """
        return await self._machine_station.execute_machine_batch_transactions(options, status_callback, tx_options)

    async def execute_machine_transfer_balance(
        self,
        options: ExecuteMachineTransferBalanceOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> Union[MachineStationWriteResult, ExecuteTransferMachineBalanceData]:
        """
        Transfers balance from a machine smart account to a recipient.
        
        **Transaction Execution**: Requires STATION_MANAGER_ROLE
        **Signature Generation Machine**: Must be signed by the machine owner
        **Signature Generation Admin**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: ExecuteMachineTransferBalanceOptions object containing machine_address, recipient_address, nonce, signatures and optional send_transaction
            status_callback: Optional callback for monitoring transaction status
            tx_options: Optional transaction confirmation mode settings
            
        Returns:
            Promise resolving to MachineStationWriteResult if sent, or ExecuteTransferMachineBalanceData if send_transaction=False
        """
        return await self._machine_station.execute_machine_transfer_balance(options, status_callback, tx_options)

    # =====================================================================
    # EIP-712 SIGNATURE GENERATION METHODS (ADMIN)
    # =====================================================================

    async def admin_sign_deploy_machine_smart_account(
        self,
        options: AdminSignDeployMachineSmartAccountOptions
    ) -> str:
        """
        Generates a signature for deploying a machine smart account.
        
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: AdminSignDeployMachineSmartAccountOptions object containing machine owner address and nonce
            
        Returns:
            The EIP-712 signature string
        """
        return await self._machine_station.admin_sign_deploy_machine_smart_account(options)

    async def admin_sign_transfer_machine_station_balance(
        self,
        options: AdminSignTransferMachineStationBalanceOptions
    ) -> str:
        """
        Generates a signature for transferring machine station balance.
        
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: AdminSignTransferMachineStationBalanceOptions object containing new address and nonce
            
        Returns:
            The EIP-712 signature string
        """
        return await self._machine_station.admin_sign_transfer_machine_station_balance(options)

    async def admin_sign_transaction(
        self,
        options: AdminSignExecuteTransactionOptions
    ) -> str:
        """
        Generates a signature for executing a transaction.
        
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: AdminSignExecuteTransactionOptions object containing target, calldata, nonce and refund_amount
            
        Returns:
            The EIP-712 signature string
        """
        return await self._machine_station.admin_sign_transaction(options)

    async def admin_sign_machine_transaction(
        self,
        options: AdminSignMachineTransactionOptions
    ) -> str:
        """
        Generates a signature for executing a machine transaction.
        
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: AdminSignMachineTransactionOptions object containing machine_address, target, calldata, nonce and refund_amount
            
        Returns:
            The EIP-712 signature string
        """
        return await self._machine_station.admin_sign_machine_transaction(options)

    async def admin_sign_machine_batch_transactions(
        self,
        options: AdminSignMachineBatchTransactionsOptions
    ) -> str:
        """
        Generates a signature for executing batch transactions.
        
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: AdminSignMachineBatchTransactionsOptions object containing machine_addresses, targets, calldata_list, nonce, refund_amount and machine_nonces
            
        Returns:
            The EIP-712 signature string
        """
        return await self._machine_station.admin_sign_machine_batch_transactions(options)

    async def admin_sign_transfer_machine_balance(
        self,
        options: AdminSignTransferMachineBalanceOptions
    ) -> str:
        """
        Generates a signature for transferring machine balance.
        
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: AdminSignTransferMachineBalanceOptions object containing machine_address, recipient_address and nonce
            
        Returns:
            The EIP-712 signature string
        """
        return await self._machine_station.admin_sign_transfer_machine_balance(options)

    # =====================================================================
    # EIP-712 SIGNATURE GENERATION METHODS (MACHINE)
    # =====================================================================

    async def machine_sign_machine_transaction(
        self,
        options: MachineSignMachineTransactionOptions,
        machine_owner_signer: Optional[BaseAccount] = None
    ) -> Union[str, EIP712SignableMessage]:
        """
        Creates a signable EIP-712 message for machine transaction execution.
        If machine_owner_signer is provided, signs the message and returns the signature.
        Otherwise, returns the message structure for frontend wallet signing.
        
        Args:
            options: MachineSignMachineTransactionOptions object containing machine_address, target, calldata, nonce
            machine_owner_signer: Optional signer to sign the message directly
            
        Returns:
            Either the signature string or EIP-712 signable message object
        """
        return await self._machine_station.machine_sign_machine_transaction(options, machine_owner_signer)

    async def machine_sign_transfer_machine_balance(
        self,
        options: MachineSignTransferMachineBalanceOptions,
        machine_owner_signer: Optional[BaseAccount] = None
    ) -> Union[str, EIP712SignableMessage]:
        """
        Creates a signable EIP-712 message for machine balance transfer.
        If machine_owner_signer is provided, signs the message and returns the signature.
        Otherwise, returns the message structure for frontend wallet signing.
        
        Args:
            options: MachineSignTransferMachineBalanceOptions object containing machine_address, recipient_address, nonce
            machine_owner_signer: Optional signer to sign the message directly
            
        Returns:
            Either the signature string or EIP-712 signable message object
        """
        return await self._machine_station.machine_sign_transfer_machine_balance(options, machine_owner_signer)