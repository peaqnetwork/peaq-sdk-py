import os
import json
import logging
import requests
from pathlib import Path
import secrets

from typing import Optional, Union

from peaq_sdk.base import Base
from peaq_sdk.types.common import (
    ChainType,
    SDKMetadata,
    SeedError,
    CallModule,
    EvmTransaction,
    PrecompileAddresses,
    WrittenTransactionResult,
    BuiltEvmTransactionResult,
    BuiltCallTransactionResult,
    BaseUrlError
)
from peaq_sdk.types.did import (
    CustomDocumentFields, 
    Verification,
    Signature,
    Service,
    DidFunctionSignatures,
    DidCallFunction,
    ReadDidResult,
    GetDidError
)
from peaq_sdk.utils import peaq_proto
from peaq_sdk.utils.utils import evm_to_address

from peaq_sdk.storage import Storage


from substrateinterface.base import SubstrateInterface
from web3 import Web3
from eth_abi import encode
from google.protobuf.json_format import MessageToDict

from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import keccak, to_hex
from eth_abi import encode

from web3 import Web3

from eth_account.messages import encode_defunct

class GetReal(Base):
    """
    Provides methods to interact with peaq's Get Real code. Allows projects to easily onboard.
    
    # Handles and signatures in the backend so DePINs don't need to

    TODO Typecast parameters
    """
    def __init__(self, sdk, machine_station_address, depin_owner_private_key, machine_owner_private_key, service_url, api_key, project_api_key, api, metadata) -> None:
        """
        Initializes Get Real instance.

        Args:
            api (Web3 | SubstrateInterface): The blockchain API connection.
                which may be a Web3 (EVM) or SubstrateInterface (Substrate).
            metadata (SDKMetadata): Shared metadata, including chain type,
                and optional signer.
                
    TODO add description
        """
        super().__init__(api, metadata)
        self.sdk = sdk
        
        self.chain_id = self._api.eth.chain_id
        self.peaq_service_url = service_url
        self.service_api_key = api_key
        self.project_api_key = project_api_key
        self.gas_station_address = machine_station_address
        # self.gas_station_owner_private = depin_private_key
        # self.machine_owner_private = machine_owner_private_key

        # Create a wallet to sign DePIN as owner transactions
        self.depin_owner_account = Account.from_key(depin_owner_private_key)
        
        # TODO How can a user initialize this at a better time
        self.machine_account = Account.from_key(machine_owner_private_key)
        
        
    def create_smart_account(self, machine_address):
        # use secrets to generate a 128-bit integer as the nonce
        nonce = secrets.randbits(128)
        
        deploy_signature = self.depin_owner_sign_typed_data_deploy_machine_smart_account(machine_address, nonce)
        machine_smart_account_address = self.deploy_machine_smart_account(machine_address, nonce, deploy_signature)
        
        return machine_smart_account_address
    
    def transfer_machine_station_balance(self, new_machine_station_address):
        nonce = secrets.randbits(128)
        owner_function_signature = self.depin_owner_sign_typed_data_transfer_machine_station_balance(new_machine_station_address, nonce)
        self.execute_transfer_machine_station_balance(new_machine_station_address, nonce, owner_function_signature)

        return f"Successfully Transferred balance to the new Machine Station Factory at address {new_machine_station_address}"
    
    def generate_storage_tx(self, email, itemType, item, tag):
        nonce = secrets.randbits(128)
        # response = self.store_data_key(email, itemType, tag)
        # print(response)
        
        storage_calldata = self.sdk.storage.add_item(itemType, item)
        owner_signature = self.owner_sign_typed_data_execute_transaction("0x0000000000000000000000000000000000000801", storage_calldata.tx['data'], nonce)
        
        self.execute_transaction(
            "0x0000000000000000000000000000000000000801",
            storage_calldata.tx['data'],
            nonce,
            owner_signature,
        )
        return "Success"
    
    def generate_did_tx(self):
        
        self
        pass
        
    def depin_owner_sign_typed_data_deploy_machine_smart_account(self, machine_address, nonce):
        """
        Example placeholder method for generating an EIP-712 typed-data signature
        for deploying a machine smart account.
        """
        try:
            domain = {
                "name": "MachineStationFactory",
                "version": "1",
                "chainId": self.chain_id,
                "verifyingContract": self.gas_station_address
            }
            types = {
                "DeployMachineSmartAccount": [
                    {"name": "machineOwner", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                ],
            }
            message = {
                "machineOwner": machine_address,
                "nonce": nonce
            }
            
            signable_message = encode_typed_data(domain, types, message)
            signature = self.depin_owner_account.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            raise
        
    def depin_owner_sign_typed_data_transfer_machine_station_balance(self, new_machine_station_address, nonce):
        try: 
            domain = {
                "name": "MachineStationFactory",
                "version": "1",
                "chainId": self.chain_id,
                "verifyingContract": self.gas_station_address
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
            signature = self.depin_owner_account.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            raise
        
    def owner_sign_typed_data_execute_transaction(self, target, calldata, nonce):
        try:
            domain = {
                "name": "MachineStationFactory",
                "version": "1",
                "chainId": self.chain_id,
                "verifyingContract": self.gas_station_address
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
            signature = self.depin_owner_account.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            raise
        
    # execute transactions
    def deploy_machine_smart_account(self, machine_address, nonce, signature):
        try:
            selector = self.api.keccak(text="deployMachineSmartAccount(address,uint256,bytes)")[:4].hex()
            signature_bytes = bytes.fromhex(signature[2:])
            encoded_params = encode(
                ['address', 'uint256', 'bytes'],
                [machine_address, nonce, signature_bytes]
            ).hex()
            
            tx: EvmTransaction = {
                "to": self.gas_station_address,
                "data": f"0x{selector}{encoded_params}"
            }
            receipt = self._send_evm_tx(tx)
            machine_smart_address = keccak(text="MachineSmartAccountDeployed(address)").hex()
            
            for log in receipt["logs"]:
                if log["topics"][0].hex() == machine_smart_address and len(log["topics"]) > 1:
                    machine_smart_account_address = Web3.to_checksum_address(log["topics"][1].hex()[24:])
                    return machine_smart_account_address

            raise ValueError("MachineSmartAccountDeployed event not found in logs")
        except Exception as e:
            raise
        
    def execute_transfer_machine_station_balance(self, new_machine_station_address, nonce, signature):
        try:
            selector = self.api.keccak(text="transferMachineStationBalance(address,uint256,bytes)")[:4].hex()
            signature_bytes = bytes.fromhex(signature[2:])
            encoded_params = encode(
                ['address', 'uint256', 'bytes'],
                [new_machine_station_address, nonce, signature_bytes]
            ).hex()
            
            tx: EvmTransaction = {
                "to": self.gas_station_address,
                "data": f"0x{selector}{encoded_params}"
            }
            self._send_evm_tx(tx)
        except Exception as e:
            raise
        
    def execute_transaction(self, target, calldata, nonce, signature):
        try:
            selector = self.api.keccak(text="executeTransaction(address,bytes,uint256,bytes)")[:4].hex()
            calldata_bytes = bytes.fromhex(calldata[2:])
            signature_bytes = bytes.fromhex(signature[2:])
            encoded_params = encode(
                ['address', 'bytes', 'uint256', 'bytes'],
                [target, calldata_bytes, nonce, signature_bytes]
            ).hex()
            tx: EvmTransaction = {
                "to": self.gas_station_address,
                "data": f"0x{selector}{encoded_params}"
            }
            self._send_evm_tx(tx)
        except Exception as e:
            raise
        
        
    
    # Next 2 functions are used in the get real service
    def store_data_key(self, email, item_type, tag):
        try:
            data = {
                "email": email,
                "item_type": item_type,
                "tag": tag
            }

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "APIKEY": self.service_api_key,
                "P-APIKEY": self.project_api_key
            }

            response = requests.post(f"{self.peaq_service_url}/v1/data/store", json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise    
        
        
    # helper functions
    def _load_abi(self, filename: str) -> list:
        """
        Loads an ABI JSON file located in ../abi relative to this script.
        Returns the parsed JSON as a Python object (list/dict).
        """
        current_dir = os.path.dirname(os.path.realpath(__file__))
        abi_dir = os.path.join(current_dir, "abi")
        abi_path = os.path.join(abi_dir, filename)
        with open(abi_path, "r", encoding="utf-8") as f:
            return json.load(f)