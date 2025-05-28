import requests
import secrets

from typing import Optional, Union

from peaq_sdk.base import Base
from peaq_sdk.types.common import (
    SDKMetadata,
    EvmTransaction,
    PrecompileAddresses
)
from peaq_sdk.types.did import (
    CustomDocumentFields, 
    Verification,
    Service,
)
from peaq_sdk.types.get_real import (
    MachineStationFactoryFunctionSignatures
)

from substrateinterface.base import SubstrateInterface
from web3 import Web3
from eth_abi import encode
from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import keccak, to_hex



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
        machine_account_owner_private_key: str, 
        api: Web3 | SubstrateInterface, 
        metadata: SDKMetadata) -> None:
        """
        TODO
        """
        super().__init__(api, metadata)
        self.sdk = sdk
        
        self.chain_id = self._api.eth.chain_id
        self.machine_station_address = machine_station_address

        # Create a wallet to sign DePIN as owner transactions
        self.machine_station_owner_private_key = Account.from_key(machine_station_owner_private_key)
        
        # TODO How can a user initialize this at a better time
        self.machine_account = Account.from_key(machine_account_owner_private_key)
        
        
        
        # EIP-721 signatures
    def depin_owner_sign_typed_data_deploy_machine_smart_account(self, machine_smart_account_owner_address, nonce):
        """
        TODO
        """
        try:
            domain = {
                "name": "MachineStationFactory",
                "version": "1",
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
                "machineOwner": machine_smart_account_owner_address,
                "nonce": nonce
            }
            
            signable_message = encode_typed_data(domain, types, message)
            depin_signature = self.machine_station_owner_private_key.sign_message(signable_message).signature.hex()
            return "0x" + depin_signature
        except Exception as e:
            # TODO custom error
            raise
        
    def depin_owner_sign_typed_data_transfer_machine_station_balance(self, new_machine_station_address, nonce):
        """
        TODO
        """
        try: 
            domain = {
                "name": "MachineStationFactory",
                "version": "1",
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
            depin_signature = self.machine_station_owner_private_key.sign_message(signable_message).signature.hex()
            return "0x" + depin_signature
        except Exception as e:
            # TODO custom error
            raise
        
    def depin_owner_sign_typed_data_execute_transaction(self, target, calldata, nonce):
        """
        TODO
        """
        try:
            domain = {
                "name": "MachineStationFactory",
                "version": "1",
                "chainId": self.chain_id,
                "verifyingContract": self.machine_station_address
            }
            types = {
                "ExecuteTransaction": [
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
            
            signable_message = encode_typed_data(domain, types, message)
            depin_signature = self.machine_station_owner_private_key.sign_message(signable_message).signature.hex()
            return "0x" + depin_signature
        except Exception as e:
            # TODO custom error
            raise
        
    def machine_owner_sign_typed_data_execute_machine_transaction(self, smart_account_address, target, calldata, nonce):
        try:
            domain = {
                "name": "MachineSmartAccount",
                "version": "1",
                "chainId": self.chain_id,
                "verifyingContract": smart_account_address
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
            
            signable_message = encode_typed_data(domain, types, message)
            # TODO have return the signature message back to the user if they don't have access to their private key
            signature = self.machine_account.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            # TODO custom error
            raise
        
    def depin_owner_sign_typed_data_execute_machine_transaction(self, smart_account_address, target, calldata, nonce):
        try:
            domain = {
                "name": "MachineStationFactory",
                "version": "1",
                "chainId": self.chain_id,
                "verifyingContract": self.machine_station_address
            }
            types = {
                "ExecuteMachineTransaction": [
                    {"name": "machineAddress", "type": "address"},
                    {"name": "target", "type": "address"},
                    {"name": "data", "type": "bytes"},
                    {"name": "nonce", "type": "uint256"},
                ],
            }
            message = {
                "machineAddress": smart_account_address,
                "target": target,
                "data": calldata,
                "nonce": nonce
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.machine_station_owner_private_key.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            # TODO custom error
            raise
        
    def depin_owner_sign_typed_data_execute_machine_batch_transactions(self, smart_account_addresses, targets, calldata_list, nonce, machine_nonces):
        try:
            domain = {
                "name": "MachineStationFactory",
                "version": "1",
                "chainId": self.chain_id,
                "verifyingContract": self.machine_station_address
            }
            types = {
                "ExecuteMachineBatchTransactions": [
                    {"name": "machineAddresses", "type": "address[]"},
                    {"name": "targets", "type": "address[]"},
                    {"name": "data", "type": "bytes[]"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "machineNonces", "type": "uint256[]"},
                ],
            }
            message = {
                "machineAddresses": smart_account_addresses,
                "targets": targets,
                "data": calldata_list,
                "nonce": nonce,
                "machineNonces": machine_nonces
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.machine_station_owner_private_key.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            # TODO custom error
            raise
        
    def machine_sign_typed_data_transfer_machine_balance(self, smart_account_address, recipient_address, nonce):
        try:
            domain = {
                "name": "MachineSmartAccount",
                "version": "1",
                "chainId": self.chain_id,
                "verifyingContract": smart_account_address
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
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.machine_account.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            # TODO custom error
            raise
        
    def owner_sign_typed_data_transfer_machine_balance(self, smart_account_address, recipient_address, nonce):
        try: 
            domain = {
                "name": "MachineStationFactory",
                "version": "1",
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
                "machineAddress": smart_account_address,
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
    def deploy_machine_smart_account(self, machine_smart_account_owner_address, nonce, machine_station_owner_signature):
        """
        TODO
        """
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.DEPLOY_MACHINE_SMART_ACCOUNT.value)[:4].hex()
            signature_bytes = bytes.fromhex(machine_station_owner_signature[2:])
            encoded_params = encode(
                ['address', 'uint256', 'bytes'],
                [machine_smart_account_owner_address, nonce, signature_bytes]
            ).hex()
            
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{function_selector}{encoded_params}"
            }
            receipt = self._send_evm_tx(tx)
            smart_account_address = keccak(text="MachineSmartAccountDeployed(address)").hex()
            
            for log in receipt["logs"]:
                if log["topics"][0].hex() == smart_account_address and len(log["topics"]) > 1:
                    smart_account_address = Web3.to_checksum_address(log["topics"][1].hex()[24:])
                    return smart_account_address

            raise ValueError("MachineSmartAccountDeployed event not found in logs")
        except Exception as e:
            # TODO custom error
            raise
        
    def execute_transfer_machine_station_balance(self, new_machine_station_address, nonce, machine_station_owner_signature):
        """
        TODO
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
            self._send_evm_tx(tx)
            
            # TODO return the receipt and a relevant message
        except Exception as e:
            raise
        
    def execute_transaction(self, target, calldata, nonce, machine_station_owner_signature):
        """
        TODO
        """
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_TRANSACTION.value)[:4].hex()
            calldata_bytes = bytes.fromhex(calldata[2:])
            signature_bytes = bytes.fromhex(machine_station_owner_signature[2:])
            encoded_params = encode(
                ['address', 'bytes', 'uint256', 'bytes'],
                [target, calldata_bytes, nonce, signature_bytes]
            ).hex()
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{function_selector}{encoded_params}"
            }
            self._send_evm_tx(tx)
            
            # TODO return the receipt and a relevant message
        except Exception as e:
            # TODO custom error
            raise
    
    def execute_machine_transaction(self, smart_account_address, target, calldata, nonce, machine_station_owner_signature, smart_account_owner_signature):
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_MACHINE_TRANSACTION.value)[:4].hex()
            calldata_bytes = bytes.fromhex(calldata[2:])
            depin_owner_signature_bytes = bytes.fromhex(machine_station_owner_signature[2:])
            smart_account_owner_signature_bytes = bytes.fromhex(smart_account_owner_signature[2:])
            
            encoded_params = encode(
                ['address', 'address', 'bytes', 'uint256', 'bytes', 'bytes'],
                [smart_account_address, target, calldata_bytes, nonce, depin_owner_signature_bytes, smart_account_owner_signature_bytes]
            ).hex()
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{function_selector}{encoded_params}"
            }
            self._send_evm_tx(tx)
            
            # TODO return the receipt and a relevant message
        except Exception as e:
            # TODO custom error
            raise
        
    def execute_machine_batch_transaction(self, smart_account_addresses, targets, calldata_list, nonce, machine_nonces, machine_station_owner_signature, smart_account_owner_signatures):
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_MACHINE_BATCH_TRANSACTIONS.value)[:4].hex()
            
            calldata_list_bytes = [
                bytes.fromhex(d[2:])
                for d in calldata_list
            ]
            depin_owner_signature_bytes = bytes.fromhex(machine_station_owner_signature[2:])
            smart_account_owner_signatures_bytes = [
                bytes.fromhex(s[2:])
                for s in smart_account_owner_signatures
            ]
            
            encoded_params = encode(
                ['address[]', 'address[]', 'bytes[]', 'uint256', 'uint256[]', 'bytes', 'bytes[]'],
                [smart_account_addresses, targets, calldata_list_bytes, nonce, machine_nonces, depin_owner_signature_bytes, smart_account_owner_signatures_bytes]
            ).hex()
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{function_selector}{encoded_params}"
            }
            self._send_evm_tx(tx)
            # TODO return the receipt and a relevant message
            
        except Exception as e:
            # TODO custom error
            raise
        
    def execute_machine_transfer_balance(self, smart_account_address, recipient_address, nonce, machine_station_owner_signature, smart_account_owner_signature):
        try:
            
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_MACHINE_TRANSFER_BALANCE.value)[:4].hex()
            depin_owner_signature_bytes = bytes.fromhex(machine_station_owner_signature[2:])
            smart_account_owner_signature_bytes = bytes.fromhex(smart_account_owner_signature[2:])
            
            encoded_params = encode(
                ['address', 'address', 'uint256', 'bytes', 'bytes'],
                [smart_account_address, recipient_address, nonce, depin_owner_signature_bytes, smart_account_owner_signature_bytes]
            ).hex()
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{function_selector}{encoded_params}"
            }
            self._send_evm_tx(tx)
        except Exception as e:
            # TODO custom error
            raise