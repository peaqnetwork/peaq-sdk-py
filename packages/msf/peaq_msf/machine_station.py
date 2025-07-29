import json
import os
from typing import Optional, Union

# Import from the core SDK package
from peaq_msf.base import Base
from peaq_msf.types.base import TransactionOptions
from peaq_msf.types.common import (
    SDKMetadata,
    WrittenTransactionResult
)
from peaq_msf.types.machine_station import (
    DeployedSmartAccountResult,
    UpdateConfigsTransactionData,
    DeployMachineSmartAccountTransactionData,
    TransferMachineStationBalanceTransactionData,
    ExecuteTransactionData,
    ExecuteMachineTransactionData,
    ExecuteMachineBatchTransactionsData,
    ExecuteTransferMachineBalanceData,
    EIP712SignableMessage
)

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
        self.chain_id = self._api.eth.chain_id
        
        # Store signers directly
        self.station_admin_signer = station_admin
        # Use station_manager if provided, otherwise use station_admin for manager operations
        self.station_manager_signer = station_manager if station_manager else self.station_admin_signer
        
        # Load ABI and create contract interface
        abi_path = os.path.join(os.path.dirname(__file__), 'abi', 'msf_abi.json')
        with open(abi_path, 'r') as f:
            self.abi = json.load(f)
        
        # Create contract interface
        self.contract = self._api.eth.contract(
            address=self.machine_station_address,
            abi=self.abi
        )

    # =====================================================================
    # CONFIGURATION METHODS
    # =====================================================================

    def update_configs(
        self,
        options: dict,
        status_callback = None,
        tx_options = None,
        send_transaction: bool = True,
    ) -> Union[WrittenTransactionResult, UpdateConfigsTransactionData]:
        """
        Updates configuration values in the machine station factory contract.
        
        **Transaction Execution**: Requires STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'key' and 'value'
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            send_transaction: If True, sends the transaction automatically using the admin key. 
                If False, returns transaction data for manual submission. Defaults to True.
            
        Returns:
            Union[WrittenTransactionResult, UpdateConfigsTransactionData]: Update result if sent, or transaction data if send_transaction=False.
            
        Raises:
            ValueError: If the configuration update fails.
        """
        try:
            data = self.contract.encode_abi(
                "updateConfigs",
                ["0x" + options['key'].value, options["value"]],
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
                    config_key=options['key'].value,
                    config_value=options['value'],
                    required_role="STATION_MANAGER_ROLE"
                )
            
            opts = tx_options if tx_options else TransactionOptions()
            result = self._send_evm_tx(tx, on_status=status_callback, opts=opts)
            
            return WrittenTransactionResult(
                message=f"Successfully updated config '{options['key'].value}' to {options['value']} through machine station {self.machine_station_address}.",
                success=True,
                transaction_hash=result.get('transactionHash') if isinstance(result, dict) else None,
                block_number=result.get('blockNumber') if isinstance(result, dict) else None,
                gas_used=result.get('gasUsed') if isinstance(result, dict) else None
            )
        except Exception as e:
            raise ValueError(f"Failed to update configs: {str(e)}")

    # =====================================================================
    # SMART ACCOUNT DEPLOYMENT METHODS
    # =====================================================================

    def deploy_machine_smart_account(
        self,
        options: dict,
        status_callback = None,
        tx_options = None
    ) -> Union[DeployedSmartAccountResult, DeployMachineSmartAccountTransactionData]:
        """
        Deploys a new machine smart account through the factory contract.
        
        **Transaction Execution**: Requires STATION_MANAGER_ROLE
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'machineOwnerAddress', 'nonce', 'stationManagerSignature', and optional 'sendTransaction'
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[DeployedSmartAccountResult, DeployMachineSmartAccountTransactionData]: Deployment result if sent, or transaction data if send_transaction=False
            
        Raises:
            ValueError: If deployment fails
        """
        try:
            send_transaction = options.get('sendTransaction', True)
            machine_owner_address = options['machine_owner_address']
            nonce = options['nonce']
            station_manager_signature = options['station_manager_signature']
            
            payload = self.contract.encode_abi(
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
            
            opts = tx_options if tx_options else TransactionOptions()
            receipt = self._send_evm_tx(tx, on_status=status_callback, opts=opts)
            machine_account_deployed_topic = self._api.keccak(text="MachineSmartAccountDeployed(address)").hex()
            
            for log in receipt["logs"]:
                if log["topics"][0].hex() == machine_account_deployed_topic and len(log["topics"]) > 1:
                    machine_account_address = Web3.to_checksum_address(log["topics"][1].hex()[24:])
                    return DeployedSmartAccountResult(
                        message=f"Successfully deployed machine smart account at address {machine_account_address}.",
                        tx_hash=receipt.get('transactionHash'),
                        receipt=receipt,
                        deployed_address=machine_account_address
                    )

            raise ValueError("MachineSmartAccountDeployed event not found in logs")
        except Exception as e:
            raise ValueError(f"Failed to deploy machine smart account: {str(e)}")

    # =====================================================================
    # BALANCE TRANSFER METHODS
    # =====================================================================

    def transfer_machine_station_balance(
        self,
        options: dict,
        status_callback = None,
        tx_options = None
    ) -> Union[WrittenTransactionResult, TransferMachineStationBalanceTransactionData]:
        """
        Transfers the machine station balance to a new machine station address.
        
        **Transaction Execution**: Requires DEFAULT_ADMIN_ROLE
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'newMachineStationAddress', 'nonce', 'stationAdminSignature', and optional 'sendTransaction'
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[WrittenTransactionResult, TransferMachineStationBalanceTransactionData]: Transfer result if sent, or transaction data if send_transaction=False
            
        Raises:
            ValueError: If transfer fails
        """
        try:
            send_transaction = options.get('sendTransaction', True)
            new_machine_station_address = options['newMachineStationAddress']
            nonce = options['nonce']
            station_admin_signature = options['stationAdminSignature']
            
            payload = self.contract.encode_abi(
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
            
            opts = tx_options if tx_options else TransactionOptions()
            receipt = self._send_evm_tx(tx, on_status=status_callback, opts=opts)
            
            return WrittenTransactionResult(
                message=f"Successfully transferred balance from {self.machine_station_address} to {new_machine_station_address}.",
                success=True,
                transaction_hash=receipt.get('transactionHash') if isinstance(receipt, dict) else None,
                block_number=receipt.get('blockNumber') if isinstance(receipt, dict) else None,
                gas_used=receipt.get('gasUsed') if isinstance(receipt, dict) else None
            )
        except Exception as e:
            raise ValueError(f"Failed to transfer machine station balance: {str(e)}")

    # =====================================================================
    # TRANSACTION EXECUTION METHODS
    # =====================================================================

    def execute_transaction(
        self,
        options: dict,
        status_callback = None,
        tx_options = None
    ) -> Union[WrittenTransactionResult, ExecuteTransactionData]:
        """
        Executes a transaction through the machine station factory.
        
        **Transaction Execution**: No specific role required (anyone can call)
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'target', 'calldata', 'nonce', optional 'refundAmount', 'machineStationOwnerSignature', and 'sendTransaction'
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[WrittenTransactionResult, ExecuteTransactionData]: Transaction result if sent, or transaction data if send_transaction=False
            
        Raises:
            ValueError: If transaction execution fails
        """

        try:
            send_transaction = options.get('sendTransaction', False)
            target = options['target']
            calldata = options['calldata']
            nonce = options['nonce']
            refund_amount = options.get('refundAmount', 0)
            machine_station_owner_signature = options.get('machineStationOwnerSignature')
            payload = self.contract.encode_abi(
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
                    message="Transaction data ready for frontend wallet submission",
                    machine_station_address=self.machine_station_address,
                    function="execute_transaction",
                    target=target,
                    access_control=self.ACCESS_CONTROL_ANYONE
                )
            
            opts = tx_options if tx_options else TransactionOptions()
            receipt = self._send_evm_tx(tx, on_status=status_callback, opts=opts)
            
            return WrittenTransactionResult(
                message=f"Successfully executed transaction on target {target} through machine station {self.machine_station_address}.",
                success=True,
                transaction_hash=receipt.get('transactionHash') if isinstance(receipt, dict) else None,
                block_number=receipt.get('blockNumber') if isinstance(receipt, dict) else None,
                gas_used=receipt.get('gasUsed') if isinstance(receipt, dict) else None
            )
        except Exception as e:
            raise ValueError(f"Failed to execute transaction: {str(e)}")

    def execute_machine_transaction(
        self,
        options: dict,
        status_callback = None,
        tx_options = None
    ) -> Union[WrittenTransactionResult, ExecuteMachineTransactionData]:
        """
        Executes a transaction on behalf of a machine smart account.
        
        **Transaction Execution**: No specific role required (anyone can call)
        **Signature Generation Machine**: Must be signed by the machine owner
        **Signature Generation Admin**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'machineAddress', 'target', 'calldata', 'nonce', optional 'refundAmount', 'machineStationOwnerSignature', 'machineOwnerSignature', and 'sendTransaction'
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[WrittenTransactionResult, ExecuteMachineTransactionData]: Transaction result if sent, or transaction data if send_transaction=False
            
        Raises:
            ValueError: If the transaction execution fails
        """
        try:
            send_transaction = options.get('sendTransaction', False)
            machine_address = options['machineAddress']
            target = options['target']
            calldata = options['calldata']
            nonce = options['nonce']
            refund_amount = options.get('refundAmount', 0)
            machine_station_owner_signature = options.get('machineStationOwnerSignature')
            machine_owner_signature = options.get('machineOwnerSignature')
            
            payload = self.contract.encode_abi(
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
                    message="Transaction data ready for frontend wallet submission",
                    machine_station_address=self.machine_station_address,
                    function="execute_machine_transaction",
                    machine_account_address=machine_address,
                    target=target,
                    access_control=self.ACCESS_CONTROL_ANYONE
                )
            
            opts = tx_options if tx_options else TransactionOptions()
            receipt = self._send_evm_tx(tx, on_status=status_callback, opts=opts)
            
            return WrittenTransactionResult(
                message=f"Successfully executed machine transaction from {machine_address} on target {target} through machine station {self.machine_station_address}.",
                success=True,
                transaction_hash=receipt.get('transactionHash') if isinstance(receipt, dict) else None,
                block_number=receipt.get('blockNumber') if isinstance(receipt, dict) else None,
                gas_used=receipt.get('gasUsed') if isinstance(receipt, dict) else None
            )
        except Exception as e:
            raise ValueError(f"Failed to execute machine transaction: {str(e)}")

    def execute_machine_batch_transactions(
        self,
        options: dict,
        status_callback = None,
        tx_options = None
    ) -> Union[WrittenTransactionResult, ExecuteMachineBatchTransactionsData]:
        """
        Executes multiple transactions in a batch on behalf of machine smart accounts.
        
        **Transaction Execution**: No specific role required (anyone can call)
        **Signature Generation Machine**: Must be signed by the machine owner
        **Signature Generation Admin**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'machineAddresses', 'targets', 'calldataList', 'nonce', optional 'refundAmount', optional 'machineNonces', optional 'machineStationOwnerSignature', optional 'machineOwnerSignatures', and optional 'sendTransaction'
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[WrittenTransactionResult, ExecuteMachineBatchTransactionsData]: Transaction result if sent, or transaction data if send_transaction=False
            
        Raises:
            ValueError: If the batch transaction execution fails
        """
        try:
            machine_addresses = options['machineAddresses']
            targets = options['targets']
            calldata_list = options['calldataList']
            nonce = options['nonce']
            refund_amount = options.get('refundAmount', 0)
            machine_nonces = options.get('machineNonces', [])
            machine_station_owner_signature = options.get('machineStationOwnerSignature')
            machine_owner_signatures = options.get('machineOwnerSignatures', [])
            send_transaction = options.get('sendTransaction', False)
            
            payload = self.contract.encode_abi(
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
                    message="Transaction data ready for frontend wallet submission",
                    machine_station_address=self.machine_station_address,
                    function="execute_machine_batch_transactions",
                    machine_account_addresses=machine_addresses,
                    targets=targets,
                    description=f"Batch transactions from accounts [{accounts_str}] on targets [{targets_str}]",
                    access_control=self.ACCESS_CONTROL_ANYONE
                )
            
            opts = tx_options if tx_options else TransactionOptions()
            receipt = self._send_evm_tx(tx, on_status=status_callback, opts=opts)
            
            # Create a descriptive message for the batch operation
            accounts_str = ", ".join(machine_addresses)
            targets_str = ", ".join(targets)
            return WrittenTransactionResult(
                message=f"Successfully executed batch transactions from accounts [{accounts_str}] on targets [{targets_str}] through machine station {self.machine_station_address}.",
                success=True,
                transaction_hash=receipt.get('transactionHash') if isinstance(receipt, dict) else None,
                block_number=receipt.get('blockNumber') if isinstance(receipt, dict) else None,
                gas_used=receipt.get('gasUsed') if isinstance(receipt, dict) else None
            )
        except Exception as e:
            raise ValueError(f"Failed to execute machine batch transaction: {str(e)}")

    def execute_machine_transfer_balance(
        self,
        options: dict,
        status_callback = None,
        tx_options = None
    ) -> Union[WrittenTransactionResult, ExecuteTransferMachineBalanceData]:
        """
        Transfers balance from a machine smart account to a recipient.
        
        **Transaction Execution**: Requires STATION_MANAGER_ROLE
        **Signature Generation Machine**: Must be signed by the machine owner
        **Signature Generation Admin**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'machineAddress', 'recipientAddress', 'nonce', 'stationManagerSignature', 'machineOwnerSignature', and optional 'sendTransaction'
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TransactionOptions for EVM transactions.
            
        Returns:
            Union[WrittenTransactionResult, ExecuteTransferMachineBalanceData]: Result containing success message and transaction receipt if sent, 
                or transaction data if send_transaction=False
            
        Raises:
            ValueError: If the balance transfer execution fails
        """
        try:
            machine_address = options['machineAddress']
            recipient_address = options['recipientAddress']
            nonce = options['nonce']
            station_manager_signature = options['stationManagerSignature']
            machine_owner_signature = options['machineOwnerSignature']
            send_transaction = options.get('sendTransaction', False)
            
            payload = self.contract.encode_abi(
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
                    function="execute_transfer_machine_balance",
                    machine_account_address=machine_address,
                    recipient_address=recipient_address,
                    required_role="STATION_MANAGER_ROLE"
                )
            
            opts = tx_options if tx_options else TransactionOptions()
            receipt = self._send_evm_tx(tx, on_status=status_callback, opts=opts)
            
            return WrittenTransactionResult(
                message=f"Successfully transferred balance from {machine_address} to {recipient_address} through machine station {self.machine_station_address}.",
                success=True,
                transaction_hash=receipt.get('transactionHash') if isinstance(receipt, dict) else None,
                block_number=receipt.get('blockNumber') if isinstance(receipt, dict) else None,
                gas_used=receipt.get('gasUsed') if isinstance(receipt, dict) else None
            )
        except Exception as e:
            raise ValueError(f"Failed to execute machine transfer balance: {str(e)}")

    # =====================================================================
    # EIP-712 SIGNATURE GENERATION METHODS (ADMIN)
    # =====================================================================

    def admin_sign_deploy_machine_smart_account(
        self,
        options: dict
    ) -> str:
        """
        Generates a signature for deploying a machine smart account.
        
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'machineOwnerAddress' and 'nonce'
            
        Returns:
            str: Hex-encoded signature (0x prefixed) from the station manager or admin
            
        Raises:
            Exception: If signature generation fails
        """
        try:
            machine_owner_address = options['machine_owner_address']
            nonce = options['nonce']
            
            domain = self._get_machine_station_domain("MachineStationFactory")
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

    def admin_sign_transfer_machine_station_balance(
        self,
        options: dict
    ) -> str:
        """
        Generates a signature for transferring machine station balance.
        
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'newMachineStationAddress' and 'nonce'
            
        Returns:
            str: Hex-encoded signature (0x prefixed) from the station admin or manager
            
        Raises:
            Exception: If signature generation fails
        """
        try:
            new_machine_station_address = options['newMachineStationAddress']
            nonce = options['nonce']
            
            domain = self._get_machine_station_domain("MachineStationFactory")
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

    def admin_sign_transaction(
        self,
        options: dict
    ) -> str:
        """
        Generates a signature for executing a transaction.
        
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'target', 'calldata', 'nonce', and optional 'refundAmount'
            
        Returns:
            str: Hex-encoded signature (0x prefixed) from the station admin or manager
            
        Raises:
            Exception: If signature generation fails
        """
            
        try:
            domain = self._get_machine_station_domain("MachineStationFactory")
            types = {
                "ExecuteTransaction": [
                    {"name": "target", "type": "address"},
                    {"name": "data", "type": "bytes"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "refundAmount", "type": "uint256"},
                ],
            }
            message = {
                "target": options['target'],
                "data": options['calldata'],
                "nonce": options['nonce'],
                "refundAmount": options.get('refundAmount', 0)
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.station_admin_signer.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            raise ValueError(f"Failed to sign transaction: {str(e)}")

    def admin_sign_machine_transaction(
        self,
        options: dict
    ) -> str:
        """
        Generates a signature for executing a machine transaction.
        
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'machineAddress', 'target', 'calldata', 'nonce', and optional 'refundAmount'
            
        Returns:
            str: Hex-encoded signature (0x prefixed) from the station admin or manager
            
        Raises:
            Exception: If signature generation fails
        """
            
        try:
            domain = self._get_machine_station_domain("MachineStationFactory")
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
                "machineAddress": options['machineAddress'],
                "target": options['target'],
                "data": options['calldata'],
                "nonce": options['nonce'],
                "refundAmount": options.get('refundAmount', 0)
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.station_admin_signer.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            raise ValueError(f"Failed to sign machine transaction: {str(e)}")

    def admin_sign_machine_batch_transactions(
        self,
        options: dict
    ) -> str:
        """
        Generates a signature for executing batch transactions.
        
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'machineAddresses', 'targets', 'calldataList', 'nonce', optional 'refundAmount', and optional 'machineNonces'
            
        Returns:
            str: Hex-encoded signature (0x prefixed) from the station admin or manager
            
        Raises:
            Exception: If signature generation fails
        """
        try:
            machine_addresses = options['machineAddresses']
            targets = options['targets']
            calldata_list = options['calldataList']
            nonce = options['nonce']
            refund_amount = options.get('refundAmount', 0)
            machine_nonces = options.get('machineNonces', [])
            
            domain = self._get_machine_station_domain("MachineStationFactory")
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

    def admin_sign_transfer_machine_balance(
        self,
        options: dict
    ) -> str:
        """
        Generates a signature for transferring machine balance.
        
        **Signature Generation**: Can be signed by either DEFAULT_ADMIN_ROLE or STATION_MANAGER_ROLE
        
        Args:
            options: Dictionary containing 'machineAddress', 'recipientAddress', and 'nonce'
            
        Returns:
            str: Hex-encoded signature (0x prefixed) from the station admin or manager
            
        Raises:
            Exception: If signature generation fails
        """
        try:
            machine_address = options['machineAddress']
            recipient_address = options['recipientAddress']
            nonce = options['nonce']
            
            domain = self._get_machine_station_domain("MachineStationFactory")
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

    def machine_sign_machine_transaction(
        self,
        options: dict
    ) -> EIP712SignableMessage:
        """
        Creates a signable EIP-712 message for machine transaction execution.
        Returns the message structure for frontend wallet signing.
        
        Args:
            options: Dictionary containing 'machineAddress', 'target', 'calldata', and 'nonce'
            
        Returns:
            EIP712SignableMessage: EIP-712 signable message object with domain, types, and message
        
        Raises:
            ValueError: If the signable message generation fails
        """
        try:
            machine_address = options['machineAddress']
            target = options['target']
            calldata = options['calldata']
            nonce = options['nonce']
            
            domain = self._get_machine_account_domain("MachineSmartAccount", machine_address)
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
            
            # Return the complete signable message object for frontend signing
            return EIP712SignableMessage(
                domain=domain,
                types=types,
                message=message,
                primaryType="Execute"
            )
        except Exception as e:
            raise ValueError(f"Failed to send back a signable message for machine transaction: {str(e)}")

    def machine_sign_transfer_machine_balance(
        self,
        options: dict
    ) -> EIP712SignableMessage:
        """
        Creates a signable EIP-712 message for machine balance transfer.
        Returns the message structure for frontend wallet signing.
        
        Args:
            options: Dictionary containing 'machineAddress', 'recipientAddress', and 'nonce'
            
        Returns:
            EIP712SignableMessage: EIP-712 signable message object with domain, types, and message
        
        Raises:
            ValueError: If the signable message generation fails
        """
        try:
            machine_address = options['machineAddress']
            recipient_address = options['recipientAddress']
            nonce = options['nonce']
            
            domain = self._get_machine_account_domain("MachineSmartAccount", machine_address)
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
            
            # Return the complete signable message object for frontend signing
            return EIP712SignableMessage(
                domain=domain,
                types=types,
                message=message,
                primaryType="TransferMachineBalance"
            )
        except Exception as e:
            raise ValueError(f"Failed to send back a signable message for machine balance transfer: {str(e)}")

    # =====================================================================
    # PRIVATE HELPER METHODS
    # =====================================================================

    def _get_machine_station_domain(self, name: str) -> dict:
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
            "chainId": self.chain_id,
            "verifyingContract": self.machine_station_address
        }

    def _get_machine_account_domain(self, name: str, verifying_contract: str) -> dict:
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
            "chainId": self.chain_id,
            "verifyingContract": verifying_contract
        }