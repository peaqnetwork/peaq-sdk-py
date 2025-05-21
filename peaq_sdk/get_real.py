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
from peaq_sdk.types.get_real import (
    MachineStationFactoryFunctionSignatures
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

# TODO important question:
# Who should sign for execute_transaction vs execute_machine_transaction, should it be owner and machine/user respectively?
#
# - Error analysis

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
        self.machine_station_address = machine_station_address
        # self.gas_station_owner_private = depin_private_key
        # self.machine_owner_private = machine_owner_private_key

        # Create a wallet to sign DePIN as owner transactions
        self.depin_owner_account = Account.from_key(depin_owner_private_key)
        
        # TODO How can a user initialize this at a better time
        self.machine_account = Account.from_key(machine_owner_private_key)
        
        
    def create_smart_account(self, wallet_address):
        """
        # use secrets to generate a 128-bit integer as the nonce
        TODO
        """
        nonce = secrets.randbits(128)
        depin_signature = self.depin_owner_sign_typed_data_deploy_machine_smart_account(wallet_address, nonce)
        smart_account_address = self.deploy_machine_smart_account(wallet_address, nonce, depin_signature)
        return smart_account_address
    
    def transfer_machine_station_balance(self, new_machine_station_address):
        """
        TODO
        """
        nonce = secrets.randbits(128)
        depin_signature = self.depin_owner_sign_typed_data_transfer_machine_station_balance(new_machine_station_address, nonce)
        self.execute_transfer_machine_station_balance(new_machine_station_address, nonce, depin_signature)

        return f"Successfully Transferred balance to the new Machine Station Factory at address {new_machine_station_address}"
    
    # TODO change to 'execute_storage_tx' or something like that 
    def generate_storage_tx(self, email, item_type, item, tag):
        """
        TODO
        """
        nonce = secrets.randbits(128)
        response = self.store_data_key(email, item_type, tag)
        # TODO make sure you get a valid response back
        
        storage_calldata = self.sdk.storage.add_item(item_type, item)
        depin_signature = self.depin_owner_sign_typed_data_execute_transaction(PrecompileAddresses.STORAGE.value, storage_calldata.tx['data'], nonce)
        
        self.execute_transaction(
            PrecompileAddresses.STORAGE.value,
            storage_calldata.tx['data'],
            nonce,
            depin_signature,
        )
        return "Success"
    
    # allow for projects to use custom fields
    def generate_did_tx(self, project, email, account_address, tag, custom_document_fields: Optional[str] = None):
        """
        TODO
        """
        nonce = secrets.randbits(128)
        account_email_signature = self.generate_email_signature(email, account_address, tag)
        
        if custom_document_fields:
            custom_fields = custom_document_fields
            # TODO must be able to add signature to the service
        else:
            # default fields
            custom_fields = CustomDocumentFields(
                verifications=[Verification(type="EcdsaSecp256k1RecoveryMethod2020")],
                # signature=[Signature], TODO do we want a signature here?
                services=[Service(id='#emailSignature', type='emailSignature', data=account_email_signature),
                          Service(id='#depin_project_address', type='address', data=self.depin_owner_account.address),
                          Service(id='#eoa_address', type='address', data=account_address)]
            )

        # only case for depin to create its own?
        did_calldata = self.sdk.did.create(name=project, custom_document_fields=custom_fields, address=account_address)
        depin_signature = self.depin_owner_sign_typed_data_execute_transaction(PrecompileAddresses.DID.value, did_calldata.tx['data'], nonce)

        self.execute_transaction(
            PrecompileAddresses.DID.value,
            did_calldata.tx['data'],
            nonce,
            depin_signature,
        )
        return "Success"
    
    def generate_smart_account_storage_tx(self, smart_account_address, email, item_type, item, tag):
        """
        - if they don't have access to private key, return the eip-712signable message back for them to sign on the frontend
        TODO
        """
        nonce = secrets.randbits(128)
        response = self.store_data_key(email, item_type, tag)
        # TODO check validity
        
        storage_calldata = self.sdk.storage.add_item(item_type, item)
        smart_account_owner_signature = self.machine_owner_sign_typed_data_execute_machine_transaction(smart_account_address, PrecompileAddresses.STORAGE.value, storage_calldata.tx['data'], nonce)
        depin_owner_signature = self.depin_owner_sign_typed_data_execute_machine_transaction(smart_account_address, PrecompileAddresses.STORAGE.value, storage_calldata.tx['data'], nonce)
        
        self.execute_machine_transaction(
            smart_account_address,
            PrecompileAddresses.STORAGE.value,
            storage_calldata.tx['data'],
            nonce,
            depin_owner_signature,
            smart_account_owner_signature,
        )
        return "Success"
        
    def generate_smart_account_create_did_tx(self, account_address, smart_account_address, project, email, tag, custom_document_fields: Optional[str] = None):
        """
        - if they don't have access to private key, return the eip-712 signable message back for them to sign on the frontend
        TODO
        """
        nonce = secrets.randbits(128)
        # TODO who is generating this signature? Create machine address or the eoa?
        # MAY NEED TO CHANGE TO smart_account_address
        account_email_signature = self.generate_email_signature(email, account_address, tag)
        
        if custom_document_fields:
            custom_fields = custom_document_fields
            # TODO must be able to add signature to the service
        else:
            # default fields
            
            # TODO Need to have proper verification:
            # - eoa address (machine address) does a EcdsaSecp256k1RecoveryMethod2020
            # - depin address (depin owner address) does a EcdsaSecp256k1RecoveryMethod2020
            
            custom_fields = CustomDocumentFields(
                verifications=[Verification(type="EcdsaSecp256k1RecoveryMethod2020")],
                # signature=[Signature], TODO do we want a signature here?
                services=[Service(id='#emailSignature', type='emailSignature', data=account_email_signature),
                          Service(id='#depin_project_address', type='address', data=self.depin_owner_account.address),
                          Service(id='#smart_account_address', type='address', data=smart_account_address),
                          Service(id='#smart_account_eoa_address', type='address', data=account_address)]
            )
        
        did_calldata = self.sdk.did.create(name=project, custom_document_fields=custom_fields, address=smart_account_address)
        
        # may need to request user/machine signature from the frontend
        smart_account_owner_signature = self.machine_owner_sign_typed_data_execute_machine_transaction(smart_account_address, PrecompileAddresses.DID.value, did_calldata.tx['data'], nonce)
        depin_owner_signature = self.depin_owner_sign_typed_data_execute_machine_transaction(smart_account_address, PrecompileAddresses.DID.value, did_calldata.tx['data'], nonce)
        
        
        self.execute_machine_transaction(
            smart_account_address,
            PrecompileAddresses.DID.value,
            did_calldata.tx['data'],
            nonce,
            depin_owner_signature,
            smart_account_owner_signature,
        )
        return "Success"
    
    def execute_machine_batch_txs():
        """
        TODO
        """
        pass
    
    def execute_machine_transfer_balance():
        """
        TODO
        """
        pass
        
    def depin_owner_sign_typed_data_deploy_machine_smart_account(self, wallet_address, nonce):
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
                "machineOwner": wallet_address,
                "nonce": nonce
            }
            
            signable_message = encode_typed_data(domain, types, message)
            depin_signature = self.depin_owner_account.sign_message(signable_message).signature.hex()
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
            depin_signature = self.depin_owner_account.sign_message(signable_message).signature.hex()
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
            depin_signature = self.depin_owner_account.sign_message(signable_message).signature.hex()
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
            signature = self.depin_owner_account.sign_message(signable_message).signature.hex()
            return "0x" + signature
        except Exception as e:
            # TODO custom error
            raise
        
    # execute transactions
    def deploy_machine_smart_account(self, wallet_address, nonce, depin_signature):
        """
        TODO
        """
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.DEPLOY_MACHINE_SMART_ACCOUNT.value)[:4].hex()
            signature_bytes = bytes.fromhex(depin_signature[2:])
            encoded_params = encode(
                ['address', 'uint256', 'bytes'],
                [wallet_address, nonce, signature_bytes]
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
        
    def execute_transfer_machine_station_balance(self, new_machine_station_address, nonce, depin_signature):
        """
        TODO
        """
        try:
            selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.TRANSFER_MACHINE_STATION_BALANCE.value)[:4].hex()
            signature_bytes = bytes.fromhex(depin_signature[2:])
            encoded_params = encode(
                ['address', 'uint256', 'bytes'],
                [new_machine_station_address, nonce, signature_bytes]
            ).hex()
            
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{selector}{encoded_params}"
            }
            self._send_evm_tx(tx)
        except Exception as e:
            raise
        
    def execute_transaction(self, target, calldata, nonce, depin_signature):
        """
        TODO
        """
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_TRANSACTION.value)[:4].hex()
            calldata_bytes = bytes.fromhex(calldata[2:])
            signature_bytes = bytes.fromhex(depin_signature[2:])
            encoded_params = encode(
                ['address', 'bytes', 'uint256', 'bytes'],
                [target, calldata_bytes, nonce, signature_bytes]
            ).hex()
            tx: EvmTransaction = {
                "to": self.machine_station_address,
                "data": f"0x{function_selector}{encoded_params}"
            }
            self._send_evm_tx(tx)
        except Exception as e:
            # TODO custom error
            raise
    
    def execute_machine_transaction(self, smart_account_address, target, calldata, nonce, depin_owner_signature, smart_account_owner_signature):
        try:
            function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_MACHINE_TRANSACTION.value)[:4].hex()
            calldata_bytes = bytes.fromhex(calldata[2:])
            depin_owner_signature_bytes = bytes.fromhex(depin_owner_signature[2:])
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
        except Exception as e:
            # TODO custom error
            raise
        
    
    # Next 2 functions are used in the get real service
    def store_data_key(self, email, item_type, tag):
        """
        TODO
        """
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
            # TODO custom error
            raise
        
    def generate_email_signature(self, email, smart_account_address, tag):
        try:
            data = {
                "email": email,
                "did_address": smart_account_address,
                "tag": tag
            }

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "APIKEY": self.service_api_key,
                "P-APIKEY": self.project_api_key
            }
            response = requests.post(f"{self.peaq_service_url}/v1/sign", json=data, headers=headers)
            response.raise_for_status()
            account_email_signature = response.json()["data"]["signature"]
            return account_email_signature
        except Exception as e:
            # TODO custom error
            raise