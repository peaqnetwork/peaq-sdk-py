from typing import Optional

from peaq_sdk.base import Base
from peaq_sdk.types.common import (
    SDKMetadata,
    EvmTransaction,
    WrittenTransactionResult
)
from peaq_sdk.types.machine_station import (
    MachineStationFactoryFunctionSignatures,
    MachineStationConfigKeys,
    DeployedSmartAccountResult
)

from substrateinterface.base import SubstrateInterface
from web3 import Web3
from eth_abi import encode
from eth_account import Account
from eth_account.messages import encode_typed_data



class MachineStation(Base):
    """
    Provides methods to interact with peaq's Machine Station Factory contract - an account
    abstraction solution that allows for gas funding, new account creation, batching transactions, etc.
    
    """
    def __init__(
        self, 
        sdk, 
        machine_station_address: str, 
        machine_station_owner_private_key: str, 
        api: Web3 | SubstrateInterface, 
        metadata: SDKMetadata) -> None:
        """
        Initializes the MachineStation class for interacting with peaq's Machine Station Factory contract.
        
        Args:
            sdk: The main SDK instance
            machine_station_address (str): Address of the deployed machine station contract
            machine_station_owner_private_key (str): Private key of the machine station owner (admin)
            api: The blockchain API connection
            metadata: Shared metadata for the SDK
        """
        super().__init__(api, metadata)
        self.sdk = sdk
        
        self.chain_id = self._api.eth.chain_id
        self.machine_station_address = machine_station_address

        # Create a wallet to sign DePIN as owner transactions
        self.machine_station_owner_private_key = Account.from_key(machine_station_owner_private_key)
        


    def update_configs(self, key: MachineStationConfigKeys, value: int):
        """
        Updates configuration values in the machine station contract.
        
        Args:
            key (str): The configuration key to update. Must be one of the valid config keys.
            value (int): The new value to set for the configuration key.
            send_transaction (bool): If True, sends the transaction automatically. If False, returns transaction data for frontend wallet submission.
            
        Returns:
            Union[WrittenTransactionResult, dict]: Update result if sent, or transaction data if send_transaction=False.
            
        Raises:
            ValueError: If the key is not found in valid configuration keys.
        """
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.UPDATE_CONFIGS.value)[:4].hex()
            
            encoded_params = encode(
                ['bytes32', 'uint256'],
                [bytes.fromhex(key.value), value]
            ).hex()
            
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{function_selector}{encoded_params}"
            }
            
            receipt = self._send_evm_tx(tx)
            
            return WrittenTransactionResult(
                message=f"Successfully updated config '{key}' to {value} through machine station {self.machine_station_address}.",
                receipt=receipt
            )
        except Exception as e:
            raise ValueError(f"Failed to update configs: {str(e)}")
         
        
    # EIP-712 signatures
    def admin_sign_deploy_machine_smart_account(self, machine_account_owner_address, nonce):
        """
        TODO
        """
        try:
            domain = {
                "name": "MachineStationFactory",
                "version": "2",
                "chainId": self.chain_id,
                "verifyingContract": self.machine_station_address
            }
            types = {
                "DeployMachineSmartAccount": [
                    {"name": "machineOwner", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                ],
            }
            message = {
                "machineOwner": machine_account_owner_address,
                "nonce": nonce
            }
            
            signable_message = encode_typed_data(domain, types, message)
            machine_station_owner_signature = self.machine_station_owner_private_key.sign_message(signable_message).signature.hex()
            return "0x" + machine_station_owner_signature
        except Exception as e:
            # TODO custom error
            raise
        
    def admin_sign_transfer_machine_station_balance(self, new_machine_station_address, nonce):
        """
        TODO
        """
        try: 
            domain = {
                "name": "MachineStationFactory",
                "version": "2",
                "chainId": self.chain_id,
                "verifyingContract": self.machine_station_address
            }
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
            machine_station_owner_signature = self.machine_station_owner_private_key.sign_message(signable_message).signature.hex()
            return "0x" + machine_station_owner_signature
        except Exception as e:
            # TODO custom error
            raise
        
    def admin_sign_transaction(self, target, calldata, nonce, refund_amount: Optional[int] = None):
        """
        TODO
        """
        if refund_amount is None:
            refund_amount = 0
            
        try:
            domain = {
                "name": "MachineStationFactory",
                "version": "2",
                "chainId": self.chain_id,
                "verifyingContract": self.machine_station_address
            }
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
            machine_station_owner_signature = self.machine_station_owner_private_key.sign_message(signable_message).signature.hex()
            return "0x" + machine_station_owner_signature
        except Exception as e:
            # TODO custom error
            raise
        
    def machine_sign_machine_transaction(self, machine_account_address, target, calldata, nonce):
        """
        Generates an EIP-712 signable message for machine transaction execution.
        
        This method returns the signable message object that should be sent to the frontend
        for the machine account owner to sign with their private key.
        
        Args:
            machine_account_address (str): Address of the machine account
            target (str): Target contract address
            calldata (str): Encoded function call data
            nonce (int): Transaction nonce
            
        Returns:
            dict: EIP-712 signable message object with domain, types, and message
        """
        try:
            domain = {
                "name": "MachineSmartAccount",
                "version": "2",
                "chainId": self.chain_id,
                "verifyingContract": machine_account_address
            }
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
            return {
                "domain": domain,
                "types": types,
                "message": message,
                "primaryType": "Execute"
            }
        except Exception as e:
            # TODO custom error
            raise
        
    def admin_sign_machine_transaction(self, machine_account_address, target, calldata, nonce, refund_amount: Optional[int] = None):
        if refund_amount is None:
            refund_amount = 0
            
        try:
            domain = {
                "name": "MachineStationFactory",
                "version": "2",
                "chainId": self.chain_id,
                "verifyingContract": self.machine_station_address
            }
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
                "machineAddress": machine_account_address,
                "target": target,
                "data": calldata,
                "nonce": nonce,
                "refundAmount": refund_amount
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.machine_station_owner_private_key.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            # TODO custom error
            raise
        
    def admin_sign_machine_batch_transactions(self, machine_account_addresses, targets, calldata_list, nonce, refund_amount: Optional[int] = None, machine_nonces: Optional[list] = None):
        if refund_amount is None:
            refund_amount = 0
            
        try:
            domain = {
                "name": "MachineStationFactory",
                "version": "2",
                "chainId": self.chain_id,
                "verifyingContract": self.machine_station_address
            }
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
                "machineAddresses": machine_account_addresses,
                "targets": targets,
                "data": calldata_list,
                "nonce": nonce,
                "refundAmount": refund_amount,
                "machineNonces": machine_nonces
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.machine_station_owner_private_key.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            # TODO custom error
            raise
        
    def machine_sign_transfer_machine_balance(self, machine_account_address, recipient_address, nonce):
        """
        Generates an EIP-712 signable message for machine balance transfer.
        
        This method returns the signable message object that should be sent to the frontend
        for the machine account owner to sign with their private key.
        
        Args:
            machine_account_address (str): Address of the machine account
            recipient_address (str): Address to receive the balance
            nonce (int): Transaction nonce
            
        Returns:
            dict: EIP-712 signable message object with domain, types, and message
        """
        try:
            domain = {
                "name": "MachineSmartAccount",
                "version": "2",
                "chainId": self.chain_id,
                "verifyingContract": machine_account_address
            }
            types = {
                "TransferMachineBalance": [
                    {"name": "recipientAddress", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                ],
            }
            message = {
                "recipientAddress": recipient_address,
                "nonce": nonce
            }
            
            # Return the complete signable message object for frontend signing
            return {
                "domain": domain,
                "types": types,
                "message": message,
                "primaryType": "TransferMachineBalance"
            }
        except Exception as e:
            # TODO custom error
            raise
        
    def admin_sign_transfer_machine_balance(self, machine_account_address, recipient_address, nonce):
        try: 
            domain = {
                "name": "MachineStationFactory",
                "version": "2",
                "chainId": self.chain_id,
                "verifyingContract": self.machine_station_address
            }
            types = {
                "ExecuteMachineTransferBalance": [
                    {"name": "machineAddress", "type": "address"},
                    {"name": "recipientAddress", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                ],
            }
            message = {
                "machineAddress": machine_account_address,
                "recipientAddress": recipient_address,
                "nonce": nonce
            }
            signable_message = encode_typed_data(domain, types, message)
            signature = self.machine_station_owner_private_key.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            # TODO custom error
            raise 
        
        
    # execute transactions
    def deploy_machine_smart_account(self, machine_account_owner_address, nonce, machine_station_owner_signature, send_transaction: bool = False):
        """
        Deploys a new machine smart account contract.
        
        Args:
            machine_account_owner_address (str): The address that will own the deployed smart account
            nonce (int): Unique nonce for the transaction
            machine_station_owner_signature (str): Signature from the machine station owner authorizing deployment
            send_transaction (bool): If True, sends the transaction automatically. If False, returns transaction data for frontend wallet submission.
            
        Returns:
            Union[DeployedSmartAccountResult, dict]: Deployment result if sent, or transaction data if send_transaction=False
        """
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.DEPLOY_MACHINE_SMART_ACCOUNT.value)[:4].hex()
            signature_bytes = bytes.fromhex(machine_station_owner_signature[2:])
            encoded_params = encode(
                ['address', 'uint256', 'bytes'],
                [machine_account_owner_address, nonce, signature_bytes]
            ).hex()
            
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{function_selector}{encoded_params}"
            }
            
            if not send_transaction:
                return {
                    "transaction_data": tx,
                    "message": "Transaction data ready for frontend wallet submission",
                    "machine_account_owner_address": machine_account_owner_address,
                    "machine_station_address": self.machine_station_address,
                    "function": "deploy_machine_smart_account",
                    "note": "After transaction is mined, listen for MachineSmartAccountDeployed event to get the deployed address"
                }
            
            receipt = self._send_evm_tx(tx)
            machine_account_deployed_topic = self.api.keccak(text="MachineSmartAccountDeployed(address)").hex()
            
            for log in receipt["logs"]:
                if log["topics"][0].hex() == machine_account_deployed_topic and len(log["topics"]) > 1:
                    machine_account_address = Web3.to_checksum_address(log["topics"][1].hex()[24:])
                    return DeployedSmartAccountResult(
                        message=f"Successfully deployed machine smart account at address {machine_account_address}.",
                        receipt=receipt,
                        deployed_address=machine_account_address
                    )

            raise ValueError("MachineSmartAccountDeployed event not found in logs")
        except Exception as e:
            raise ValueError(f"Failed to deploy machine smart account: {str(e)}")
        
    def execute_transfer_machine_station_balance(self, new_machine_station_address, nonce, machine_station_owner_signature, send_transaction: bool = False):
        """
        Transfers the balance from the current machine station to a new one.
        
        Args:
            new_machine_station_address (str): The address of the new machine station to transfer balance to
            nonce (int): Unique nonce for the transaction
            machine_station_owner_signature (str): Signature from the machine station owner authorizing transfer
            send_transaction (bool): If True, sends the transaction automatically. If False, returns transaction data for frontend wallet submission.
            
        Returns:
            Union[WrittenTransactionResult, dict]: Transfer result if sent, or transaction data if send_transaction=False
        """
        try:
            selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.TRANSFER_MACHINE_STATION_BALANCE.value)[:4].hex()
            signature_bytes = bytes.fromhex(machine_station_owner_signature[2:])
            encoded_params = encode(
                ['address', 'uint256', 'bytes'],
                [new_machine_station_address, nonce, signature_bytes]
            ).hex()
            
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{selector}{encoded_params}"
            }
            
            if not send_transaction:
                return {
                    "transaction_data": tx,
                    "message": "Transaction data ready for frontend wallet submission",
                    "current_machine_station_address": self.machine_station_address,
                    "new_machine_station_address": new_machine_station_address,
                    "function": "execute_transfer_machine_station_balance"
                }
            
            receipt = self._send_evm_tx(tx)
            
            return WrittenTransactionResult(
                message=f"Successfully transferred balance from {self.machine_station_address} to {new_machine_station_address}.",
                receipt=receipt
            )
        except Exception as e:
            raise ValueError(f"Failed to transfer machine station balance: {str(e)}")
        
    def execute_transaction(self, target, calldata, nonce, refund_amount: Optional[int] = None, machine_station_owner_signature: Optional[str] = None, send_transaction: bool = False):
        """
        Executes a transaction through the machine station.
        
        Args:
            target (str): The target contract address
            calldata (str): The encoded function call data
            nonce (int): Unique nonce for the transaction
            refund_amount (Optional[int]): Optional refund amount. If not provided, defaults to 0.
            machine_station_owner_signature (str): Signature from the machine station owner authorizing the transaction
            send_transaction (bool): If True, sends the transaction automatically. If False, returns transaction data for frontend wallet submission.
            
        Returns:
            Union[WrittenTransactionResult, dict]: Transaction result if sent, or transaction data if send_transaction=False
        """
        if refund_amount is None:
            refund_amount = 0
            
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_TRANSACTION.value)[:4].hex()
            calldata_bytes = bytes.fromhex(calldata[2:])
            signature_bytes = bytes.fromhex(machine_station_owner_signature[2:])
            encoded_params = encode(
                ['address', 'bytes', 'uint256', 'uint256', 'bytes'],
                [target, calldata_bytes, nonce, refund_amount, signature_bytes]
            ).hex()
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{function_selector}{encoded_params}"
            }
            
            if not send_transaction:
                return {
                    "transaction_data": tx,
                    "message": "Transaction data ready for frontend wallet submission",
                    "target": target,
                    "machine_station_address": self.machine_station_address,
                    "function": "execute_transaction"
                }
            
            receipt = self._send_evm_tx(tx)
            
            return WrittenTransactionResult(
                message=f"Successfully executed transaction on target {target} through machine station {self.machine_station_address}.",
                receipt=receipt
            )
        except Exception as e:
            raise ValueError(f"Failed to execute transaction: {str(e)}")
    
    # By default return back the tx 
    def execute_machine_transaction(self, machine_account_address, target, calldata, nonce, refund_amount: Optional[int] = None, machine_station_owner_signature: Optional[str] = None, machine_account_owner_signature: Optional[str] = None, send_transaction: bool = False):
        if refund_amount is None:
            refund_amount = 0
            
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_MACHINE_TRANSACTION.value)[:4].hex()
            calldata_bytes = bytes.fromhex(calldata[2:])
            depin_owner_signature_bytes = bytes.fromhex(machine_station_owner_signature[2:])
            machine_account_owner_signature_bytes = bytes.fromhex(machine_account_owner_signature[2:])
            
            encoded_params = encode(
                ['address', 'address', 'bytes', 'uint256', 'uint256', 'bytes', 'bytes'],
                [machine_account_address, target, calldata_bytes, nonce, refund_amount, depin_owner_signature_bytes, machine_account_owner_signature_bytes]
            ).hex()
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{function_selector}{encoded_params}"
            }
            
            if not send_transaction:
                return {
                    "transaction_data": tx,
                    "message": "Transaction data ready for frontend wallet submission",
                    "machine_account_address": machine_account_address,
                    "target": target,
                    "machine_station_address": self.machine_station_address,
                    "function": "execute_machine_transaction"
                }
            
            receipt = self._send_evm_tx(tx)
            
            return WrittenTransactionResult(
                message=f"Successfully executed machine transaction from {machine_account_address} on target {target} through machine station {self.machine_station_address}.",
                receipt=receipt
            )
        except Exception as e:
            raise ValueError(f"Failed to execute machine transaction: {str(e)}")
        
    def execute_machine_batch_transactions(self, machine_account_addresses, targets, calldata_list, nonce, refund_amount: Optional[int] = None, machine_nonces: Optional[list] = None, machine_station_owner_signature: Optional[str] = None, machine_account_owner_signatures: Optional[list] = None, send_transaction: bool = False):
        if refund_amount is None:
            refund_amount = 0
            
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_MACHINE_BATCH_TRANSACTIONS.value)[:4].hex()
            
            calldata_list_bytes = [
                bytes.fromhex(d[2:])
                for d in calldata_list
            ]
            depin_owner_signature_bytes = bytes.fromhex(machine_station_owner_signature[2:])
            machine_account_owner_signatures_bytes = [
                bytes.fromhex(s[2:])
                for s in machine_account_owner_signatures
            ]
            
            encoded_params = encode(
                ['address[]', 'address[]', 'bytes[]', 'uint256', 'uint256', 'uint256[]', 'bytes', 'bytes[]'],
                [machine_account_addresses, targets, calldata_list_bytes, nonce, refund_amount, machine_nonces, depin_owner_signature_bytes, machine_account_owner_signatures_bytes]
            ).hex()
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{function_selector}{encoded_params}"
            }
            
            if not send_transaction:
                accounts_str = ", ".join(machine_account_addresses)
                targets_str = ", ".join(targets)
                return {
                    "transaction_data": tx,
                    "message": "Transaction data ready for frontend wallet submission",
                    "machine_account_addresses": machine_account_addresses,
                    "targets": targets,
                    "machine_station_address": self.machine_station_address,
                    "function": "execute_machine_batch_transactions",
                    "description": f"Batch transactions from accounts [{accounts_str}] on targets [{targets_str}]"
                }
            
            receipt = self._send_evm_tx(tx)
            
            # Create a descriptive message for the batch operation
            accounts_str = ", ".join(machine_account_addresses)
            targets_str = ", ".join(targets)
            return WrittenTransactionResult(
                message=f"Successfully executed batch transactions from accounts [{accounts_str}] on targets [{targets_str}] through machine station {self.machine_station_address}.",
                receipt=receipt
            )
        except Exception as e:
            raise ValueError(f"Failed to execute machine batch transaction: {str(e)}")
        
    def execute_transfer_machine_balance(self, machine_account_address, recipient_address, nonce, machine_station_owner_signature, machine_account_owner_signature):
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_MACHINE_TRANSFER_BALANCE.value)[:4].hex()
            depin_owner_signature_bytes = bytes.fromhex(machine_station_owner_signature[2:])
            machine_account_owner_signature_bytes = bytes.fromhex(machine_account_owner_signature[2:])
            
            encoded_params = encode(
                ['address', 'address', 'uint256', 'bytes', 'bytes'],
                [machine_account_address, recipient_address, nonce, depin_owner_signature_bytes, machine_account_owner_signature_bytes]
            ).hex()
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{function_selector}{encoded_params}"
            }
            receipt = self._send_evm_tx(tx)
            
            return WrittenTransactionResult(
                message=f"Successfully transferred balance from {machine_account_address} to {recipient_address} through machine station {self.machine_station_address}.",
                receipt=receipt
            )
        except Exception as e:
            raise ValueError(f"Failed to execute machine transfer balance: {str(e)}")