import json
import os
from typing import Optional, Union, Any

# Import from the core SDK package
from peaq_msf.base import Base
from peaq_msf.types.base import TxOptions, StatusCallback, TransactionStatusCallback, EvmSendResult, BuiltEvmTransactionResult
from peaq_msf.types.common import (
    SDKMetadata
)
from peaq_msf.types.machine_station import (
    DeployedSmartAccountResult,
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
    MachineStationWriteResult,
    DeployMachineSmartAccountTransactionData,
    TransferMachineStationBalanceTransactionData,
    ExecuteTransactionData,
    ExecuteMachineTransactionData,
    ExecuteMachineBatchTransactionsData,
    ExecuteTransferMachineBalanceData,
    EIP712SignableMessage
)
from .utils.utils import parse_options


from web3 import Web3
from web3.types import TxParams
from eth_account import Account
from eth_account.signers.base import BaseAccount
from eth_account.messages import encode_typed_data


class MachineStation(Base):
    """
    Provides methods to interact with the peaq machine station factory smart contract.
    Supports configuration updates, smart account deployment, transaction execution, and EIP-712 signature generation.
    """
    
    # Constants
    ACCESS_CONTROL_ANYONE = "Anyone can call with proper signatures"
    
    def __init__(
        self, 
        api: Web3,
        metadata: SDKMetadata,
        machine_station_address: str,
        station_admin: BaseAccount,
        station_manager: Optional[BaseAccount] = None
    ) -> None:
        """
        Initializes MachineStation with a connected Web3 provider and admin signers.
        
        Args:
            api: The Web3 provider connection
            metadata: Shared metadata for EVM chain operations
            machine_station_address: The address of the machine station factory smart contract
            station_admin: BaseAccount signer for station admin operations (DEFAULT_ADMIN_ROLE)
            station_manager: Optional BaseAccount signer for station manager operations (STATION_MANAGER_ROLE). If not provided, admin will be used.
        """
        super().__init__(api, metadata)
        self.machine_station_address = machine_station_address
        self.station_admin_signer = station_admin
        self.station_manager_signer = station_manager if station_manager else self.station_admin_signer
        
        # Load ABI and create contract interface
        abi_path = os.path.join(os.path.dirname(__file__), 'abi', 'msf_abi.json')
        with open(abi_path, 'r') as f:
            self.abi = json.load(f)
        
        # Create contract interface
        self.iface = self._api.eth.contract(
            address=self.machine_station_address,
            abi=self.abi
        )

    # =====================================================================
    # CONFIGURATION METHODS
    # =====================================================================

    async def _handle_evm_tx(
        self,
        tx: TxParams,
        action: str,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {},
        signer: Optional[BaseAccount] = None
    ) -> Union[EvmSendResult, BuiltEvmTransactionResult]:
        """
        Helper method to handle EVM transaction execution with proper signer management.
        
        Args:
            tx: Transaction parameters
            action: Description of the action being performed
            status_callback: Optional callback for transaction status updates
            tx_options: Optional transaction options
            signer: Optional specific signer to use (temporarily overrides metadata.pair)
            iface: Optional contract interface for better error decoding
            
        Returns:
            EvmSendResult for executed transactions or BuiltEvmTransactionResult for unsigned transactions
        """
        if not self._metadata.pair and not signer:
            return BuiltEvmTransactionResult(
                message=f"Constructed {action} tx (unsigned).",
                tx=tx
            )
        
        try:
            # If a specific signer is provided, temporarily override the metadata.pair
            if signer:
                original_signer = self._metadata.pair
                self._metadata.pair = signer
                try:
                    return await self._send_evm_tx(tx, on_status=status_callback, opts=tx_options, iface=self.iface)
                finally:
                    # Restore the original signer
                    self._metadata.pair = original_signer
            else:
                return await self._send_evm_tx(tx, on_status=status_callback, opts=tx_options, iface=self.iface)
        except Exception as err:
            raise ValueError(f"Failed to {action}: {str(err)}")

    async def update_configs(
        self,
        options: UpdateConfigsOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {},
    ) -> Union[MachineStationWriteResult, UpdateConfigsTransactionData]:
        """
        Updates configuration values in the machine station factory contract.
        
        **Transaction Execution**: Requires STATION_MANAGER_ROLE
        
        Args:
            options: UpdateConfigsOptions object containing 'key', 'value' and optional 'send_transaction'
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[MachineStationWriteResult, UpdateConfigsTransactionData]: Update result if sent, or transaction data if send_transaction=False.
            
        Raises:
            ValueError: If the configuration update fails.
        """
        try:
            ops = parse_options(UpdateConfigsOptions, options, caller="update_configs()")
            key = ops.key
            value = ops.value
            send_transaction = ops.send_transaction
            
            data = self.iface.encode_abi(
                "updateConfigs",
                ["0x" + key.value, value],
            )
            tx: TxParams = {
                "to": self.machine_station_address,
                "data": data
            }
            
            if not send_transaction:
                return UpdateConfigsTransactionData(
                    transaction_data=tx,
                    message="Transaction data ready for manual submission",
                    machine_station_address=self.machine_station_address,
                    function="update_configs",
                    config_key=key.value,
                    config_value=value,
                    required_role="STATION_MANAGER_ROLE"
                )
            
            # Use the new helper method with station manager signer
            return await self._handle_evm_tx(
                tx=tx,
                action=f"update config '{key.value}' to {value}",
                status_callback=status_callback,
                tx_options=tx_options,
                signer=self.station_manager_signer
            )
        except Exception as e:
            raise ValueError(f"Failed to update configs: {str(e)}")

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
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[DeployedSmartAccountResult, DeployMachineSmartAccountTransactionData]: Deployment result if sent, or transaction data if send_transaction=False
            
        Raises:
            ValueError: If deployment fails
        """
        try:
            ops = parse_options(DeployMachineSmartAccountOptions, options, caller="deploy_machine_smart_account()")
            machine_owner_address = ops.machine_owner_address
            nonce = ops.nonce
            station_manager_signature = ops.station_manager_signature
            send_transaction = ops.send_transaction
            
            payload = self.iface.encode_abi(
                "deployMachineSmartAccount",
                [machine_owner_address, nonce, station_manager_signature]
            )
            
            tx: TxParams = {
                "to": self.machine_station_address,
                "data": payload
            }
            
            if not send_transaction:
                return DeployMachineSmartAccountTransactionData(
                    transaction_data=tx,
                    message="Transaction data ready for manual submission",
                    machine_station_address=self.machine_station_address,
                    function="deploy_machine_smart_account",
                    machine_account_owner_address=machine_owner_address,
                    required_role="STATION_MANAGER_ROLE",
                    note="After transaction is mined, listen for MachineSmartAccountDeployed event to get the deployed address"
                )
            
            # Use the new helper method with station manager signer
            result = await self._handle_evm_tx(
                tx=tx,
                action=f"deploy machine smart account for owner {machine_owner_address}",
                status_callback=status_callback,
                tx_options=tx_options,
                signer=self.station_manager_signer
            )
            receipt = await result.receipt
            machine_account_deployed_topic = self._api.keccak(text="MachineSmartAccountDeployed(address)").hex()
            
            for log in receipt["logs"]:
                # Handle both string and bytes topics
                topic_0 = log["topics"][0]
                topic_0_hex = topic_0.hex() if hasattr(topic_0, 'hex') else topic_0
                
                if topic_0_hex == machine_account_deployed_topic and len(log["topics"]) > 1:
                    topic_1 = log["topics"][1]
                    topic_1_hex = topic_1.hex() if hasattr(topic_1, 'hex') else topic_1
                    machine_account_address = Web3.to_checksum_address(f"0x{topic_1_hex[24:]}")
            
            return DeployedSmartAccountResult(
                message=f"Successfully deployed machine smart account at address {machine_account_address}.",
                tx_hash=getattr(result, 'tx_hash', None),
                receipt=receipt,
                deployed_address=machine_account_address
            )
        except Exception as e:
            raise ValueError(f"Failed to deploy machine smart account: {str(e)}")

    # =====================================================================
    # BALANCE TRANSFER METHODS
    # =====================================================================

    async def transfer_machine_station_balance(
        self,
        options: TransferMachineStationBalanceOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {},
    ) -> Union[MachineStationWriteResult, TransferMachineStationBalanceTransactionData]:
        """
        Transfers the machine station balance to a new machine station address.
        
        **Transaction Execution**: Requires DEFAULT_ADMIN_ROLE
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: TransferMachineStationBalanceOptions object containing new address, nonce, signature and optional send_transaction
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[MachineStationWriteResult, TransferMachineStationBalanceTransactionData]: Transfer result if sent, or transaction data if send_transaction=False
            
        Raises:
            ValueError: If transfer fails
        """
        try:
            ops = parse_options(TransferMachineStationBalanceOptions, options, caller="transfer_machine_station_balance()")
            new_machine_station_address = ops.new_machine_station_address
            nonce = ops.nonce
            station_admin_signature = ops.station_admin_signature
            send_transaction = ops.send_transaction
            
            payload = self.iface.encode_abi(
                "transferMachineStationBalance",
                [new_machine_station_address, nonce, station_admin_signature]
            )
            
            tx: TxParams = {
                "to": self.machine_station_address,
                "data": payload
            }
            
            if not send_transaction:
                return TransferMachineStationBalanceTransactionData(
                    transaction_data=tx,
                    message="Transaction data ready for manual submission",
                    machine_station_address=self.machine_station_address,
                    function="execute_transfer_machine_station_balance",
                    current_machine_station_address=self.machine_station_address,
                    new_machine_station_address=new_machine_station_address,
                    required_role="DEFAULT_ADMIN_ROLE"
                )
            
            # Use the new helper method with station admin signer
            return await self._handle_evm_tx(
                tx=tx,
                action=f"transfer machine station balance to {new_machine_station_address}",
                status_callback=status_callback,
                tx_options=tx_options,
                signer=self.station_admin_signer
            )
        except Exception as e:
            raise ValueError(f"Failed to transfer machine station balance: {str(e)}")

    # =====================================================================
    # TRANSACTION EXECUTION METHODS
    # =====================================================================

    async def execute_transaction(
        self,
        options: ExecuteTransactionOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {},
    ) -> Union[MachineStationWriteResult, ExecuteTransactionData]:
        """
        Executes a transaction through the machine station factory.
        
        **Transaction Execution**: No specific role required (anyone can call)
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: ExecuteTransactionOptions object containing target, calldata, nonce, refund_amount, machine_station_owner_signature and optional send_transaction
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[MachineStationWriteResult, ExecuteTransactionData]: Execution result if sent, or transaction data if send_transaction=False
            
        Raises:
            ValueError: If execution fails
        """
        try:
            ops = parse_options(ExecuteTransactionOptions, options, caller="execute_transaction()")
            target = ops.target
            calldata = ops.calldata
            nonce = ops.nonce
            refund_amount = ops.refund_amount
            machine_station_owner_signature = ops.machine_station_owner_signature
            send_transaction = ops.send_transaction
            
            payload = self.iface.encode_abi(
                "executeTransaction",
                [target, calldata, nonce, refund_amount, machine_station_owner_signature]
            )
            
            tx: TxParams = {
                "to": self.machine_station_address,
                "data": payload
            }
            
            if not send_transaction:
                return ExecuteTransactionData(
                    transaction_data=tx,
                    message="Transaction data ready for manual submission",
                    machine_station_address=self.machine_station_address,
                    function="execute_transaction",
                    target=target,
                    access_control="Anyone can call with proper signatures"
                )
            
            # Use the new helper method with station admin signer
            return await self._handle_evm_tx(
                tx=tx,
                action=f"execute transaction to {target}",
                status_callback=status_callback,
                tx_options=tx_options,
                signer=self.station_admin_signer
            )
        except Exception as e:
            raise ValueError(f"Failed to execute transaction: {str(e)}")

    async def execute_machine_transaction(
        self,
        options: ExecuteMachineTransactionOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {},
    ) -> Union[EvmSendResult, ExecuteMachineTransactionData]:
        """
        Executes a transaction on behalf of a machine smart account.
        
        **Transaction Execution**: No specific role required (anyone can call)
        **Signature Generation Machine**: Must be signed by the machine owner
        **Signature Generation Admin**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: ExecuteMachineTransactionOptions object containing machine_address, target, calldata, nonce, refund_amount, signatures and optional send_transaction
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[EvmSendResult, ExecuteMachineTransactionData]: Transaction result if sent, or transaction data if send_transaction=False
            
        Raises:
            ValueError: If the transaction execution fails
        """
        try:
            ops = parse_options(ExecuteMachineTransactionOptions, options, caller="execute_machine_transaction()")
            machine_address = ops.machine_address
            target = ops.target
            calldata = ops.calldata
            nonce = ops.nonce
            refund_amount = ops.refund_amount
            machine_station_owner_signature = ops.machine_station_owner_signature
            machine_owner_signature = ops.machine_owner_signature
            send_transaction = ops.send_transaction
            
            payload = self.iface.encode_abi(
                "executeMachineTransaction",
                [machine_address, target, calldata, nonce, refund_amount, machine_station_owner_signature, machine_owner_signature]
            )
            
            tx: TxParams = {
                "to": self.machine_station_address,
                "data": payload
            }
            
            if not send_transaction:
                return ExecuteMachineTransactionData(
                    transaction_data=tx,
                    message="Transaction data ready for manual submission",
                    machine_station_address=self.machine_station_address,
                    function="execute_machine_transaction",
                    machine_account_address=machine_address,
                    target=target,
                    access_control="Anyone can call with proper signatures"
                )
            
            # Use the new helper method with station admin signer
            return await self._handle_evm_tx(
                tx=tx,
                action=f"execute machine transaction to {target}",
                status_callback=status_callback,
                tx_options=tx_options,
                signer=self.station_manager_signer
            )
        except Exception as e:
            raise ValueError(f"Failed to execute machine transaction: {str(e)}")

    async def execute_machine_batch_transactions(
        self,
        options: ExecuteMachineBatchTransactionsOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {},
    ) -> Union[EvmSendResult, ExecuteMachineBatchTransactionsData]:
        """
        Executes multiple transactions in a batch on behalf of machine smart accounts.
        
        **Transaction Execution**: No specific role required (anyone can call)
        **Signature Generation Machine**: Must be signed by the machine owner
        **Signature Generation Admin**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: ExecuteMachineBatchTransactionsOptions object containing machine_addresses, targets, calldata_list, nonce, refund_amount, machine_nonces, signatures and optional send_transaction
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[MachineStationWriteResult, ExecuteMachineBatchTransactionsData]: Transaction result if sent, or transaction data if send_transaction=False
            
        Raises:
            ValueError: If the batch transaction execution fails
        """
        try:
            ops = parse_options(ExecuteMachineBatchTransactionsOptions, options, caller="execute_machine_batch_transactions()")
            machine_addresses = ops.machine_addresses
            targets = ops.targets
            calldata_list = ops.calldata_list
            nonce = ops.nonce
            refund_amount = ops.refund_amount
            machine_nonces = ops.machine_nonces
            machine_station_owner_signature = ops.machine_station_owner_signature
            machine_owner_signatures = ops.machine_owner_signatures
            send_transaction = ops.send_transaction
            
            payload = self.iface.encode_abi(
                "executeMachineBatchTransactions",
                [machine_addresses, targets, calldata_list, nonce, refund_amount, machine_nonces, machine_station_owner_signature, machine_owner_signatures]
            )
            
            tx: TxParams = {
                "to": self.machine_station_address,
                "data": payload
            }
            
            if not send_transaction:
                accounts_str = ", ".join(machine_addresses)
                targets_str = ", ".join(targets)
                return ExecuteMachineBatchTransactionsData(
                    transaction_data=tx,
                    message="Transaction data ready for manual submission",
                    machine_station_address=self.machine_station_address,
                    function="execute_machine_batch_transactions",
                    machine_account_addresses=machine_addresses,
                    targets=targets,
                    description=f"Batch transactions from accounts [{accounts_str}] on targets [{targets_str}]",
                    access_control="Anyone can call with proper signatures"
                )
            
            # Use the new helper method with station manager signer
            return await self._handle_evm_tx(
                tx=tx,
                action=f"execute batch transaction for {len(machine_addresses)} machines",
                status_callback=status_callback,
                tx_options=tx_options,
                signer=self.station_manager_signer
            )
        except Exception as e:
            raise ValueError(f"Failed to execute machine batch transactions: {str(e)}")

    async def execute_machine_transfer_balance(
        self,
        options: ExecuteMachineTransferBalanceOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {},
    ) -> Union[MachineStationWriteResult, ExecuteTransferMachineBalanceData]:
        """
        Transfers balance from a machine smart account to a recipient.
        
        **Transaction Execution**: Requires STATION_MANAGER_ROLE
        **Signature Generation Machine**: Must be signed by the machine owner
        **Signature Generation Admin**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: ExecuteMachineTransferBalanceOptions object containing machine_address, recipient_address, nonce, signatures and optional send_transaction
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[MachineStationWriteResult, ExecuteTransferMachineBalanceData]: Result containing success message and transaction receipt if sent, 
                or transaction data if send_transaction=False
            
        Raises:
            ValueError: If the balance transfer execution fails
        """
        try:
            ops = parse_options(ExecuteMachineTransferBalanceOptions, options, caller="execute_machine_transfer_balance()")
            machine_address = ops.machine_address
            recipient_address = ops.recipient_address
            nonce = ops.nonce
            station_manager_signature = ops.station_manager_signature
            machine_owner_signature = ops.machine_owner_signature
            send_transaction = ops.send_transaction
            
            payload = self.iface.encode_abi(
                "executeMachineTransferBalance",
                [machine_address, recipient_address, nonce, station_manager_signature, machine_owner_signature]
            )
            
            tx: TxParams = {
                "to": self.machine_station_address,
                "data": payload
            }
            
            if not send_transaction:
                return ExecuteTransferMachineBalanceData(
                    transaction_data=tx,
                    message="Transaction data ready for manual submission",
                    machine_station_address=self.machine_station_address,
                    function="execute_machine_transfer_balance",
                    machine_account_address=machine_address,
                    recipient_address=recipient_address,
                    required_role="STATION_MANAGER_ROLE"
                )
            
            # Use the new helper method with station manager signer
            return await self._handle_evm_tx(
                tx=tx,
                action=f"transfer balance from machine {machine_address} to {recipient_address}",
                status_callback=status_callback,
                tx_options=tx_options,
                signer=self.station_manager_signer
            )
        except Exception as e:
            raise ValueError(f"Failed to execute machine transfer balance: {str(e)}")

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
            str: Hex-encoded signature (0x prefixed) from the station manager or admin
            
        Raises:
            Exception: If signature generation fails
        """
        try:
            ops = parse_options(AdminSignDeployMachineSmartAccountOptions, options, caller="admin_sign_deploy_machine_smart_account()")
            machine_owner_address = ops.machine_owner_address
            nonce = ops.nonce
            
            domain = await self._get_machine_station_domain("MachineStationFactory")
            types = {
                "DeployMachineSmartAccount": [
                    {"name": "machineOwner", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                ],
            }
            message = {
                "machineOwner": machine_owner_address,
                "nonce": nonce
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.station_manager_signer.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            raise ValueError(f"Failed to sign deploy machine smart account: {str(e)}")

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
            str: Hex-encoded signature (0x prefixed) from the station admin or manager
            
        Raises:
            Exception: If signature generation fails
        """
        try:
            ops = parse_options(AdminSignTransferMachineStationBalanceOptions, options, caller="admin_sign_transfer_machine_station_balance()")
            new_machine_station_address = ops.new_machine_station_address
            nonce = ops.nonce
            
            domain = await self._get_machine_station_domain("MachineStationFactory")
            types = {
                "TransferMachineStationBalance": [
                    {"name": "newMachineStationAddress", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                ],
            }
            message = {
                "newMachineStationAddress": new_machine_station_address,
                "nonce": nonce
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.station_admin_signer.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            raise ValueError(f"Failed to sign transfer machine station balance: {str(e)}")

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
            str: Hex-encoded signature (0x prefixed) from the station admin or manager
            
        Raises:
            Exception: If signature generation fails
        """
        try:
            ops = parse_options(AdminSignExecuteTransactionOptions, options, caller="admin_sign_transaction()")
            target = ops.target
            calldata = ops.calldata
            nonce = ops.nonce
            refund_amount = ops.refund_amount
            
            domain = await self._get_machine_station_domain("MachineStationFactory")
            types = {
                "ExecuteTransaction": [
                    {"name": "target", "type": "address"},
                    {"name": "data", "type": "bytes"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "refundAmount", "type": "uint256"},
                ],
            }
            message = {
                "target": target,
                "data": calldata,
                "nonce": nonce,
                "refundAmount": refund_amount
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.station_admin_signer.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            raise ValueError(f"Failed to sign execute transaction: {str(e)}")

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
            str: Hex-encoded signature (0x prefixed) from the station admin or manager
            
        Raises:
            Exception: If signature generation fails
        """
        try:
            ops = parse_options(AdminSignMachineTransactionOptions, options, caller="admin_sign_machine_transaction()")
            machine_address = ops.machine_address
            target = ops.target
            calldata = ops.calldata
            nonce = ops.nonce
            refund_amount = ops.refund_amount
            
            domain = await self._get_machine_station_domain("MachineStationFactory")  
            types = {
                "ExecuteMachineTransaction": [
                    {"name": "machineAddress", "type": "address"},
                    {"name": "target", "type": "address"},
                    {"name": "data", "type": "bytes"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "refundAmount", "type": "uint256"},
                ],
            }
            message = {
                "machineAddress": machine_address,
                "target": target,
                "data": calldata,
                "nonce": nonce,
                "refundAmount": refund_amount
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.station_admin_signer.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            raise ValueError(f"Failed to sign machine transaction: {str(e)}")

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
            str: Hex-encoded signature (0x prefixed) from the station admin or manager
            
        Raises:
            Exception: If signature generation fails
        """
        try:
            ops = parse_options(AdminSignMachineBatchTransactionsOptions, options, caller="admin_sign_machine_batch_transactions()")
            machine_addresses = ops.machine_addresses
            targets = ops.targets
            calldata_list = ops.calldata_list
            nonce = ops.nonce
            refund_amount = ops.refund_amount
            machine_nonces = ops.machine_nonces
            
            domain = await self._get_machine_station_domain("MachineStationFactory")
            types = {
                "ExecuteMachineBatchTransactions": [
                    {"name": "machineAddresses", "type": "address[]"},
                    {"name": "targets", "type": "address[]"},
                    {"name": "data", "type": "bytes[]"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "refundAmount", "type": "uint256"},
                    {"name": "machineNonces", "type": "uint256[]"},
                ],
            }
            message = {
                "machineAddresses": machine_addresses,
                "targets": targets,
                "data": calldata_list,
                "nonce": nonce,
                "refundAmount": refund_amount,
                "machineNonces": machine_nonces
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.station_admin_signer.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            raise ValueError(f"Failed to sign machine batch transactions: {str(e)}")

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
            str: Hex-encoded signature (0x prefixed) from the station admin or manager
            
        Raises:
            Exception: If signature generation fails
        """
        try:
            ops = parse_options(AdminSignTransferMachineBalanceOptions, options, caller="admin_sign_transfer_machine_balance()")
            machine_address = ops.machine_address
            recipient_address = ops.recipient_address
            nonce = ops.nonce
            
            domain = await self._get_machine_station_domain("MachineStationFactory")
            types = {
                "ExecuteMachineTransferBalance": [
                    {"name": "machineAddress", "type": "address"},
                    {"name": "recipientAddress", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                ],
            }
            message = {
                "machineAddress": machine_address,
                "recipientAddress": recipient_address,
                "nonce": nonce,
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.station_admin_signer.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            raise ValueError(f"Failed to sign transfer machine balance: {str(e)}")

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
            machine_owner_signer: Optional machine owner signer for direct signing
            
        Returns:
            Union[str, EIP712SignableMessage]: Either the signature string or EIP-712 signable message object
        
        Raises:
            ValueError: If the signable message generation fails
        """
        try:
            ops = parse_options(MachineSignMachineTransactionOptions, options, caller="machine_sign_machine_transaction()")
            machine_address = ops.machine_address
            target = ops.target
            calldata = ops.calldata
            nonce = ops.nonce
            
            domain = await self._get_machine_account_domain("MachineSmartAccount", machine_address)
            types = {
                "Execute": [
                    {"name": "target", "type": "address"},
                    {"name": "data", "type": "bytes"},
                    {"name": "nonce", "type": "uint256"},
                ],
            }
            message = {
                "target": target,
                "data": calldata,
                "nonce": nonce
            }
            
            # If signer is provided, sign the message and return signature
            if machine_owner_signer:
                signable_message = encode_typed_data(domain, types, message)
                signature = machine_owner_signer.sign_message(signable_message).signature.hex()
                return "0x" + signature
            
            # Otherwise return the signable message object for frontend signing
            return EIP712SignableMessage(
                domain=domain,
                types=types,
                message=message,
                primaryType="Execute"
            )
        except Exception as e:
            raise ValueError(f"Failed to create signable message for machine transaction: {str(e)}")

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
            machine_owner_signer: Optional machine owner signer for direct signing
            
        Returns:
            Union[str, EIP712SignableMessage]: Either the signature string or EIP-712 signable message object
        
        Raises:
            ValueError: If the signable message generation fails
        """
        try:
            ops = parse_options(MachineSignTransferMachineBalanceOptions, options, caller="machine_sign_transfer_machine_balance()")
            machine_address = ops.machine_address
            recipient_address = ops.recipient_address
            nonce = ops.nonce
            
            domain = await self._get_machine_account_domain("MachineSmartAccount", machine_address)
            types = {
                "TransferMachineBalance": [
                    {"name": "recipientAddress", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                ],
            }
            message = {
                "recipientAddress": recipient_address,
                "nonce": nonce,
            }
            
            # If signer is provided, sign the message and return signature
            if machine_owner_signer:
                signable_message = encode_typed_data(domain, types, message)
                signature = machine_owner_signer.sign_message(signable_message).signature.hex()
                return "0x" + signature
            
            # Otherwise return the signable message object for frontend signing
            return EIP712SignableMessage(
                domain=domain,
                types=types,
                message=message,
                primaryType="TransferMachineBalance"
            )
        except Exception as e:
            raise ValueError(f"Failed to create signable message for machine balance transfer: {str(e)}")

    # =====================================================================
    # PRIVATE HELPER METHODS
    # =====================================================================

    async def _get_machine_station_domain(self, name: str) -> dict:
        """
        Generates an EIP-712 domain for MachineStationFactory contract.
        
        Args:
            name: The domain name
            
        Returns:
            dict: The EIP-712 domain object
        """
        return {
            "name": name,
            "version": "2",
            "chainId": await self.get_chain_id(),
            "verifyingContract": self.machine_station_address
        }

    async def _get_machine_account_domain(self, name: str, verifying_contract: str) -> dict:
        """
        Generates an EIP-712 domain for MachineSmartAccount contract.
        
        Args:
            name: The domain name
            verifying_contract: The machine smart account address
            
        Returns:
            dict: The EIP-712 domain object
        """
        return {
            "name": name,
            "version": "2",
            "chainId": await self.get_chain_id(),
            "verifyingContract": verifying_contract
        }