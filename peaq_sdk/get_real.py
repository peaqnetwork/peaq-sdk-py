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
from peaq_sdk.types.machine_station import (
    MachineStationFactoryFunctionSignatures
)

from peaq_sdk.machine_station import MachineStation

from substrateinterface.base import SubstrateInterface
from web3 import Web3
from eth_abi import encode
from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import keccak, to_hex



# TODO important question:
# Who should sign for execute_transaction vs execute_machine_transaction, should it be owner and machine/user respectively?
#
# - Error analysis

class GetReal(MachineStation):
    """
    Provides methods to interact with peaq's Get Real code. Allows projects to easily onboard.
    Inherits from MachineStation to have access to all machine station functionality.
    
    # Handles and signatures in the backend so DePINs don't need to

    TODO Typecast parameters
    """
    def __init__(
        self, 
        sdk, 
        machine_station_address: str, 
        machine_station_owner_private_key: str, 
        machine_account_owner_private_key: str, 
        service_url: str,
        api_key: str,
        project_api_key: str,
        api: Web3 | SubstrateInterface, 
        metadata: SDKMetadata
    ) -> None:
        """
        Initializes Get Real instance.

        Args:
            sdk (Main): The main SDK instance.
            machine_station_address (str): Address of the deployed machine station contract.
            machine_station_owner_private_key (str): Private key of the machine station owner.
            machine_account_owner_private_key (str): Private key of the machine account owner.
            service_url (str): URL for the peaq service.
            api_key (str): API key for authentication.
            project_api_key (str): Project-specific API key.
            api (Web3 | SubstrateInterface): The blockchain API connection.
            metadata (SDKMetadata): Shared metadata for the SDK.
        """
        # Initialize MachineStation (which initializes Base)
        super().__init__(
            sdk=sdk,
            machine_station_address=machine_station_address,
            machine_station_owner_private_key=machine_station_owner_private_key,
            machine_account_owner_private_key=machine_account_owner_private_key,
            api=api,
            metadata=metadata
        )
        
        self.sdk = sdk
        self.chain_id = self._api.eth.chain_id
        self.peaq_service_url = service_url
        self.service_api_key = api_key
        self.project_api_key = project_api_key
        self.machine_station_address = machine_station_address

        # Create a wallet to sign DePIN as owner transactions
        self.machine_station_account = Account.from_key(machine_station_owner_private_key)
        
        # TODO How can a user initialize this at a better time
        self.machine_account = Account.from_key(machine_account_owner_private_key)
        
        
    def create_smart_account(self, owner_eoa_address: str, nonce: Optional[int] = None):
        """
        Creates a new smart account owned by the provided EOA address.

        Args:
            owner_eoa_address (str): The Externally Owned Account address that will own the smart account.
            nonce (Optional[int]): Optional nonce value. If not provided, a random 128-bit integer will be generated.

        Returns:
            str: The address of the newly created smart account.
        """
        if nonce is None:
            nonce = secrets.randbits(128)
            
        depin_signature = self.depin_owner_sign_typed_data_deploy_machine_smart_account(owner_eoa_address, nonce)
        result = self.deploy_machine_smart_account(owner_eoa_address, nonce, depin_signature)
        return result
    
    def transfer_machine_station_balance(self, new_machine_station_address: str, nonce: Optional[int] = None) -> str:
        """
        Transfers the balance from the current machine station to a new machine station address.
        This is typically used when upgrading or migrating to a new machine station contract.

        Args:
            new_machine_station_address (str): The address of the new machine station contract that will receive the balance.
            nonce (Optional[int]): Optional nonce value. If not provided, a random 128-bit integer will be generated.

        Returns:
            str: Success message with the new machine station address.

        Note:
            This operation requires the machine station owner's signature and can only be executed by 
            the current machine station owner.
        """
        if nonce is None:
            nonce = secrets.randbits(128)
            
        depin_signature = self.depin_owner_sign_typed_data_transfer_machine_station_balance(new_machine_station_address, nonce)
        result = self.execute_transfer_machine_station_balance(new_machine_station_address, nonce, depin_signature)

        return result
    
    def storage_tx(
        self,
        email: str,
        item_type: str,
        item: str,
        tag: str
    ) -> str:
        """
        Generates and executes a Get Real specific storage transaction. This transaction stores data on-chain
        with email verification, allowing for authenticated data storage.

        The transaction flow:
        1. Stores the data key with email verification
        2. Creates and executes the storage transaction on-chain
        3. Links the stored data with the verified email through the tag

        Args:
            email (str): The email address associated with the EOA account for verification.
            item_type (str): The key/identifier for the data being stored.
            item (str): The actual data/value to be stored on-chain.
            tag (str): An identifier used to link and verify this transaction on-chain.

        Returns:
            str: "Success" if the transaction is completed successfully.
        """
            
        storage_data = self.generate_storage_tx(email, item_type, item, tag)
        
        result = self.execute_transaction(
            storage_data['target'],
            storage_data['calldata'],
            storage_data['nonce'],
            storage_data['depin_signature'],
        )
        return result
    
    # allow for projects to use custom fields
    def did_tx(self, project, email, account_address, tag, custom_document_fields: Optional[str] = None):
        """
        TODO
        """
        did_data = self.generate_did_tx(project, email, account_address, tag, custom_document_fields)
        
        result = self.execute_transaction(
            did_data['target'],
            did_data['calldata'],
            did_data['nonce'],
            did_data['depin_signature'],
        )
        return result
    
    def smart_account_storage_tx(self, smart_account_address, email, item_type, item, tag):
        """
        - if they don't have access to private key, return the eip-712signable message back for them to sign on the frontend
        TODO
        """
        smart_account_storage_data = self.generate_smart_account_storage_tx(smart_account_address, email, item_type, item, tag)

        result = self.execute_machine_transaction(
            smart_account_storage_data['smart_account_address'],
            smart_account_storage_data['target'],
            smart_account_storage_data['calldata'],
            smart_account_storage_data['nonce'],
            smart_account_storage_data['depin_owner_signature'],
            smart_account_storage_data['smart_account_owner_signature']
        )
        return result
        
    def smart_account_did_tx(self, account_address, smart_account_address, project, email, tag, custom_document_fields: Optional[str] = None):
        """
        - if they don't have access to private key, return the eip-712 signable message back for them to sign on the frontend
        TODO
        """
        smart_account_did_tx = self.generate_smart_account_did_tx(account_address, smart_account_address, project, email, tag, custom_document_fields)
        
        result = self.execute_machine_transaction(
            smart_account_did_tx['smart_account_address'],
            smart_account_did_tx['target'],
            smart_account_did_tx['calldata'],
            smart_account_did_tx['nonce'],
            smart_account_did_tx['depin_owner_signature'],
            smart_account_did_tx['smart_account_owner_signature']
        )
        return result
    
    def smart_account_batch_txs(self, data_payloads):
        """
        TODO
        """
        # Unpack data payload
        smart_account_addresses = [tx["smart_account_address"] for tx in data_payloads]
        targets = [tx["target"] for tx in data_payloads]
        calldata_list = [tx["calldata"] for tx in data_payloads]
        machine_nonces = [tx["nonce"] for tx in data_payloads]
        smart_account_owner_signatures = [tx["smart_account_owner_signature"] for tx in data_payloads]

        # Generate a single batch‐nonce for the entire batch
        nonce = secrets.randbits(128)
        
        depin_owner_signature = self.depin_owner_sign_typed_data_execute_machine_batch_transactions(smart_account_addresses, targets, calldata_list, nonce, machine_nonces)
        
        
        result = self.execute_machine_batch_transactions(    
            smart_account_addresses,
            targets,
            calldata_list,
            nonce,
            machine_nonces,
            depin_owner_signature,
            smart_account_owner_signatures
        )
        
        return result

    
    def smart_account_transfer_balance(self, smart_account_address, recipient_address):
        """
        TODO
        """
        nonce = secrets.randbits(128)
        
        smart_account_owner_signature = self.machine_sign_typed_data_transfer_machine_balance(smart_account_address, recipient_address, nonce)
        depin_owner_signature = self.owner_sign_typed_data_transfer_machine_balance(smart_account_address, recipient_address, nonce)
        
        
        result = self.execute_machine_transfer_balance(
            smart_account_address,
            recipient_address,
            nonce,
            depin_owner_signature,
            smart_account_owner_signature
        )
        
        return result

        
    # Build the Machine Station Factory transactions that are Get-Real Specific 
    # 
    # If user is not in get-real they should just use the tx builder in the sdk and then sign the calldata by calling the proper function
    def generate_storage_tx(self, email, item_type, item, tag):
        nonce = secrets.randbits(128)
        response = self.store_data_key(email, item_type, tag)
        # TODO make sure you get a valid response back
        
        storage_calldata = self.sdk.storage.add_item(item_type, item)
        depin_signature = self.depin_owner_sign_typed_data_execute_transaction(PrecompileAddresses.STORAGE.value, storage_calldata.tx['data'], nonce)
    
        return {
            "target": PrecompileAddresses.STORAGE.value,
            "calldata": storage_calldata.tx['data'],
            "nonce": nonce,
            "depin_signature": depin_signature
            }
    
    def generate_did_tx(self, project, email, account_address, tag, custom_document_fields: Optional[str] = None):
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
                          Service(id='#depin_project_address', type='address', data=self.machine_station_account.address),
                          Service(id='#eoa_address', type='address', data=account_address)]
            )

        # only case for depin to create its own?
        did_calldata = self.sdk.did.create(name=project, custom_document_fields=custom_fields, address=account_address)
        depin_signature = self.depin_owner_sign_typed_data_execute_transaction(PrecompileAddresses.DID.value, did_calldata.tx['data'], nonce)

        return {
            "target": PrecompileAddresses.DID.value,
            "calldata": did_calldata.tx['data'],
            "nonce": nonce,
            "depin_signature": depin_signature
            }
        
    # TODO be able to send a signable message back to the frontend for signature request
    def generate_smart_account_storage_tx(self, smart_account_address, email, item_type, item, tag, signature: Optional[str] = None):
        nonce = secrets.randbits(128)
        response = self.store_data_key(email, item_type, tag)
        # TODO check validity
        
        storage_calldata = self.sdk.storage.add_item(item_type, item)
        
        # generate a message to sign if not provided
        if not signature:
            smart_account_owner_signature = self.machine_owner_sign_typed_data_execute_machine_transaction(smart_account_address, PrecompileAddresses.STORAGE.value, storage_calldata.tx['data'], nonce)
        depin_owner_signature = self.depin_owner_sign_typed_data_execute_machine_transaction(smart_account_address, PrecompileAddresses.STORAGE.value, storage_calldata.tx['data'], nonce)
        
        return {
            "smart_account_address": smart_account_address,
            "target": PrecompileAddresses.STORAGE.value,
            "calldata": storage_calldata.tx['data'],
            "nonce": nonce,
            "depin_owner_signature": depin_owner_signature,
            "smart_account_owner_signature": smart_account_owner_signature
        }
        
    def generate_smart_account_did_tx(self, account_address, smart_account_address, project, email, tag, custom_document_fields: Optional[str] = None):
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
                          Service(id='#depin_project_address', type='address', data=self.machine_station_account.address),
                          Service(id='#smart_account_address', type='address', data=smart_account_address),
                          Service(id='#smart_account_eoa_address', type='address', data=account_address)]
            )
        
        did_calldata = self.sdk.did.create(name=project, custom_document_fields=custom_fields, address=smart_account_address)
        
        # may need to request user/machine signature from the frontend
        smart_account_owner_signature = self.machine_owner_sign_typed_data_execute_machine_transaction(smart_account_address, PrecompileAddresses.DID.value, did_calldata.tx['data'], nonce)
        depin_owner_signature = self.depin_owner_sign_typed_data_execute_machine_transaction(smart_account_address, PrecompileAddresses.DID.value, did_calldata.tx['data'], nonce)
        
        return {
            "smart_account_address": smart_account_address,
            "target": PrecompileAddresses.DID.value,
            "calldata": did_calldata.tx['data'],
            "nonce": nonce,
            "depin_owner_signature": depin_owner_signature,
            "smart_account_owner_signature": smart_account_owner_signature
        }        

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


    # # The following code generates the tx to be sent on chain
    # def generate_storage_tx(self, email, item_type, item, tag):
    #     nonce = secrets.randbits(128)
    #     response = self.store_data_key(email, item_type, tag)
    #     # TODO make sure you get a valid response back
        
    #     storage_calldata = self.sdk.storage.add_item(item_type, item)
    #     depin_signature = self.depin_owner_sign_typed_data_execute_transaction(PrecompileAddresses.STORAGE.value, storage_calldata.tx['data'], nonce)
    
    #     return {
    #         "target": PrecompileAddresses.STORAGE.value,
    #         "calldata": storage_calldata.tx['data'],
    #         "nonce": nonce,
    #         "depin_signature": depin_signature
    #         }
    
    # def generate_did_tx(self, project, email, account_address, tag, custom_document_fields: Optional[str] = None):
    #     nonce = secrets.randbits(128)
    #     account_email_signature = self.generate_email_signature(email, account_address, tag)
        
    #     if custom_document_fields:
    #         custom_fields = custom_document_fields
    #         # TODO must be able to add signature to the service
    #     else:
    #         # default fields
    #         custom_fields = CustomDocumentFields(
    #             verifications=[Verification(type="EcdsaSecp256k1RecoveryMethod2020")],
    #             # signature=[Signature], TODO do we want a signature here?
    #             services=[Service(id='#emailSignature', type='emailSignature', data=account_email_signature),
    #                       Service(id='#depin_project_address', type='address', data=self.machine_station_account.address),
    #                       Service(id='#eoa_address', type='address', data=account_address)]
    #         )

    #     # only case for depin to create its own?
    #     did_calldata = self.sdk.did.create(name=project, custom_document_fields=custom_fields, address=account_address)
    #     depin_signature = self.depin_owner_sign_typed_data_execute_transaction(PrecompileAddresses.DID.value, did_calldata.tx['data'], nonce)

    #     return {
    #         "target": PrecompileAddresses.DID.value,
    #         "calldata": did_calldata.tx['data'],
    #         "nonce": nonce,
    #         "depin_signature": depin_signature
    #         }
        
    # def generate_smart_account_storage_tx(self, smart_account_address, email, item_type, item, tag):
    #     nonce = secrets.randbits(128)
    #     response = self.store_data_key(email, item_type, tag)
    #     # TODO check validity
        
    #     storage_calldata = self.sdk.storage.add_item(item_type, item)
    #     smart_account_owner_signature = self.machine_owner_sign_typed_data_execute_machine_transaction(smart_account_address, PrecompileAddresses.STORAGE.value, storage_calldata.tx['data'], nonce)
    #     depin_owner_signature = self.depin_owner_sign_typed_data_execute_machine_transaction(smart_account_address, PrecompileAddresses.STORAGE.value, storage_calldata.tx['data'], nonce)
        
    #     return {
    #         "smart_account_address": smart_account_address,
    #         "target": PrecompileAddresses.STORAGE.value,
    #         "calldata": storage_calldata.tx['data'],
    #         "nonce": nonce,
    #         "depin_owner_signature": depin_owner_signature,
    #         "smart_account_owner_signature": smart_account_owner_signature
    #     }
        
    # def generate_smart_account_did_tx(self, account_address, smart_account_address, project, email, tag, custom_document_fields: Optional[str] = None):
    #     nonce = secrets.randbits(128)
    #     # TODO who is generating this signature? Create machine address or the eoa?
    #     # MAY NEED TO CHANGE TO smart_account_address
    #     account_email_signature = self.generate_email_signature(email, account_address, tag)
        
    #     if custom_document_fields:
    #         custom_fields = custom_document_fields
    #         # TODO must be able to add signature to the service
    #     else:
    #         # default fields
            
    #         # TODO Need to have proper verification:
    #         # - eoa address (machine address) does a EcdsaSecp256k1RecoveryMethod2020
    #         # - depin address (depin owner address) does a EcdsaSecp256k1RecoveryMethod2020
            
    #         custom_fields = CustomDocumentFields(
    #             verifications=[Verification(type="EcdsaSecp256k1RecoveryMethod2020")],
    #             # signature=[Signature], TODO do we want a signature here?
    #             services=[Service(id='#emailSignature', type='emailSignature', data=account_email_signature),
    #                       Service(id='#depin_project_address', type='address', data=self.machine_station_account.address),
    #                       Service(id='#smart_account_address', type='address', data=smart_account_address),
    #                       Service(id='#smart_account_eoa_address', type='address', data=account_address)]
    #         )
        
    #     did_calldata = self.sdk.did.create(name=project, custom_document_fields=custom_fields, address=smart_account_address)
        
    #     # may need to request user/machine signature from the frontend
    #     smart_account_owner_signature = self.machine_owner_sign_typed_data_execute_machine_transaction(smart_account_address, PrecompileAddresses.DID.value, did_calldata.tx['data'], nonce)
    #     depin_owner_signature = self.depin_owner_sign_typed_data_execute_machine_transaction(smart_account_address, PrecompileAddresses.DID.value, did_calldata.tx['data'], nonce)
        
    #     return {
    #         "smart_account_address": smart_account_address,
    #         "target": PrecompileAddresses.DID.value,
    #         "calldata": did_calldata.tx['data'],
    #         "nonce": nonce,
    #         "depin_owner_signature": depin_owner_signature,
    #         "smart_account_owner_signature": smart_account_owner_signature
    #     }

    # # signatures
    # def depin_owner_sign_typed_data_deploy_machine_smart_account(self, wallet_address, nonce):
    #     """
    #     TODO
    #     """
    #     try:
    #         domain = {
    #             "name": "MachineStationFactory",
    #             "version": "1",
    #             "chainId": self.chain_id,
    #             "verifyingContract": self.machine_station_address
    #         }
    #         types = {
    #             "DeployMachineSmartAccount": [
    #                 {"name": "machineOwner", "type": "address"},
    #                 {"name": "nonce", "type": "uint256"},
    #             ],
    #         }
    #         message = {
    #             "machineOwner": wallet_address,
    #             "nonce": nonce
    #         }
            
    #         signable_message = encode_typed_data(domain, types, message)
    #         depin_signature = self.machine_station_account.sign_message(signable_message).signature.hex()
    #         return "0x" + depin_signature
    #     except Exception as e:
    #         # TODO custom error
    #         raise
        
    # def depin_owner_sign_typed_data_transfer_machine_station_balance(self, new_machine_station_address, nonce):
    #     """
    #     TODO
    #     """
    #     try: 
    #         domain = {
    #             "name": "MachineStationFactory",
    #             "version": "1",
    #             "chainId": self.chain_id,
    #             "verifyingContract": self.machine_station_address
    #         }
    #         types = {
    #             "TransferMachineStationBalance": [
    #                 {"name": "newMachineStationAddress", "type": "address"},
    #                 {"name": "nonce", "type": "uint256"},
    #             ],
    #         }
    #         message = {
    #             "newMachineStationAddress": new_machine_station_address,
    #             "nonce": nonce
    #         }
            
    #         signable_message = encode_typed_data(domain, types, message)
    #         depin_signature = self.machine_station_account.sign_message(signable_message).signature.hex()
    #         return "0x" + depin_signature
    #     except Exception as e:
    #         # TODO custom error
    #         raise
        
    # def depin_owner_sign_typed_data_execute_transaction(self, target, calldata, nonce):
    #     """
    #     TODO
    #     """
    #     try:
    #         domain = {
    #             "name": "MachineStationFactory",
    #             "version": "1",
    #             "chainId": self.chain_id,
    #             "verifyingContract": self.machine_station_address
    #         }
    #         types = {
    #             "ExecuteTransaction": [
    #                 {"name": "target", "type": "address"},
    #                 {"name": "data", "type": "bytes"},
    #                 {"name": "nonce", "type": "uint256"},
    #             ],
    #         }
    #         message = {
    #             "target": target,
    #             "data": calldata,
    #             "nonce": nonce
    #         }
            
    #         signable_message = encode_typed_data(domain, types, message)
    #         depin_signature = self.machine_station_account.sign_message(signable_message).signature.hex()
    #         return "0x" + depin_signature
    #     except Exception as e:
    #         # TODO custom error
    #         raise
        
    # def machine_owner_sign_typed_data_execute_machine_transaction(self, smart_account_address, target, calldata, nonce):
    #     try:
    #         domain = {
    #             "name": "MachineSmartAccount",
    #             "version": "1",
    #             "chainId": self.chain_id,
    #             "verifyingContract": smart_account_address
    #         }
    #         types = {
    #             "Execute": [
    #                 {"name": "target", "type": "address"},
    #                 {"name": "data", "type": "bytes"},
    #                 {"name": "nonce", "type": "uint256"},
    #             ],
    #         }
    #         message = {
    #             "target": target,
    #             "data": calldata,
    #             "nonce": nonce
    #         }
            
    #         signable_message = encode_typed_data(domain, types, message)
    #         # TODO have return the signature message back to the user if they don't have access to their private key
    #         signature = self.machine_account.sign_message(signable_message).signature.hex()
    #         return "0x" + signature
    #     except Exception as e:
    #         # TODO custom error
    #         raise
        
    # def depin_owner_sign_typed_data_execute_machine_transaction(self, smart_account_address, target, calldata, nonce):
    #     try:
    #         domain = {
    #             "name": "MachineStationFactory",
    #             "version": "1",
    #             "chainId": self.chain_id,
    #             "verifyingContract": self.machine_station_address
    #         }
    #         types = {
    #             "ExecuteMachineTransaction": [
    #                 {"name": "machineAddress", "type": "address"},
    #                 {"name": "target", "type": "address"},
    #                 {"name": "data", "type": "bytes"},
    #                 {"name": "nonce", "type": "uint256"},
    #             ],
    #         }
    #         message = {
    #             "machineAddress": smart_account_address,
    #             "target": target,
    #             "data": calldata,
    #             "nonce": nonce
    #         }
            
    #         signable_message = encode_typed_data(domain, types, message)
    #         signature = self.machine_station_account.sign_message(signable_message).signature.hex()
    #         return "0x" + signature
    #     except Exception as e:
    #         # TODO custom error
    #         raise
        
    # def depin_owner_sign_typed_data_execute_machine_batch_transactions(self, smart_account_addresses, targets, calldata_list, nonce, machine_nonces):
    #     try:
    #         domain = {
    #             "name": "MachineStationFactory",
    #             "version": "1",
    #             "chainId": self.chain_id,
    #             "verifyingContract": self.machine_station_address
    #         }
    #         types = {
    #             "ExecuteMachineBatchTransactions": [
    #                 {"name": "machineAddresses", "type": "address[]"},
    #                 {"name": "targets", "type": "address[]"},
    #                 {"name": "data", "type": "bytes[]"},
    #                 {"name": "nonce", "type": "uint256"},
    #                 {"name": "machineNonces", "type": "uint256[]"},
    #             ],
    #         }
    #         message = {
    #             "machineAddresses": smart_account_addresses,
    #             "targets": targets,
    #             "data": calldata_list,
    #             "nonce": nonce,
    #             "machineNonces": machine_nonces
    #         }
            
    #         signable_message = encode_typed_data(domain, types, message)
    #         signature = self.machine_station_account.sign_message(signable_message).signature.hex()
    #         return "0x" + signature
    #     except Exception as e:
    #         # TODO custom error
    #         raise
        
    # def machine_sign_typed_data_transfer_machine_balance(self, smart_account_address, recipient_address, nonce):
    #     try:
    #         domain = {
    #             "name": "MachineSmartAccount",
    #             "version": "1",
    #             "chainId": self.chain_id,
    #             "verifyingContract": smart_account_address
    #         }
    #         types = {
    #             "TransferMachineBalance": [
    #                 {"name": "recipientAddress", "type": "address"},
    #                 {"name": "nonce", "type": "uint256"},
    #             ],
    #         }
    #         message = {
    #             "recipientAddress": recipient_address,
    #             "nonce": nonce
    #         }
            
    #         signable_message = encode_typed_data(domain, types, message)
    #         signature = self.machine_account.sign_message(signable_message).signature.hex()
    #         return "0x" + signature
    #     except Exception as e:
    #         # TODO custom error
    #         raise
        
    # def owner_sign_typed_data_transfer_machine_balance(self, smart_account_address, recipient_address, nonce):
    #     try: 
    #         domain = {
    #             "name": "MachineStationFactory",
    #             "version": "1",
    #             "chainId": self.chain_id,
    #             "verifyingContract": self.machine_station_address
    #         }
    #         types = {
    #             "ExecuteMachineTransferBalance": [
    #                 {"name": "machineAddress", "type": "address"},
    #                 {"name": "recipientAddress", "type": "address"},
    #                 {"name": "nonce", "type": "uint256"},
    #             ],
    #         }
    #         message = {
    #             "machineAddress": smart_account_address,
    #             "recipientAddress": recipient_address,
    #             "nonce": nonce
    #         }
    #         signable_message = encode_typed_data(domain, types, message)
    #         signature = self.machine_station_account.sign_message(signable_message).signature.hex()
    #         return "0x" + signature
    #     except Exception as e:
    #         # TODO custom error
    #         raise    
        
    
    # # execute transactions
    # def deploy_machine_smart_account(self, wallet_address, nonce, depin_signature):
    #     """
    #     TODO
    #     """
    #     try:
    #         function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.DEPLOY_MACHINE_SMART_ACCOUNT.value)[:4].hex()
    #         signature_bytes = bytes.fromhex(depin_signature[2:])
    #         encoded_params = encode(
    #             ['address', 'uint256', 'bytes'],
    #             [wallet_address, nonce, signature_bytes]
    #         ).hex()
            
    #         tx: EvmTransaction = {
    #             "to": self.machine_station_address,
    #             "data": f"0x{function_selector}{encoded_params}"
    #         }
    #         receipt = self._send_evm_tx(tx)
    #         smart_account_address = keccak(text="MachineSmartAccountDeployed(address)").hex()
            
    #         for log in receipt["logs"]:
    #             if log["topics"][0].hex() == smart_account_address and len(log["topics"]) > 1:
    #                 smart_account_address = Web3.to_checksum_address(log["topics"][1].hex()[24:])
    #                 return smart_account_address

    #         raise ValueError("MachineSmartAccountDeployed event not found in logs")
    #     except Exception as e:
    #         # TODO custom error
    #         raise
        
    # def execute_transfer_machine_station_balance(self, new_machine_station_address, nonce, depin_signature):
    #     """
    #     TODO
    #     """
    #     try:
    #         selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.TRANSFER_MACHINE_STATION_BALANCE.value)[:4].hex()
    #         signature_bytes = bytes.fromhex(depin_signature[2:])
    #         encoded_params = encode(
    #             ['address', 'uint256', 'bytes'],
    #             [new_machine_station_address, nonce, signature_bytes]
    #         ).hex()
            
    #         tx: EvmTransaction = {
    #             "to": self.machine_station_address,
    #             "data": f"0x{selector}{encoded_params}"
    #         }
    #         self._send_evm_tx(tx)
    #     except Exception as e:
    #         raise
        
    # def execute_transaction(self, target, calldata, nonce, depin_signature):
    #     """
    #     TODO
    #     """
    #     try:
    #         function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_TRANSACTION.value)[:4].hex()
    #         calldata_bytes = bytes.fromhex(calldata[2:])
    #         signature_bytes = bytes.fromhex(depin_signature[2:])
    #         encoded_params = encode(
    #             ['address', 'bytes', 'uint256', 'bytes'],
    #             [target, calldata_bytes, nonce, signature_bytes]
    #         ).hex()
    #         tx: EvmTransaction = {
    #             "to": self.machine_station_address,
    #             "data": f"0x{function_selector}{encoded_params}"
    #         }
    #         self._send_evm_tx(tx)
    #     except Exception as e:
    #         # TODO custom error
    #         raise
    
    # def execute_machine_transaction(self, smart_account_address, target, calldata, nonce, depin_owner_signature, smart_account_owner_signature):
    #     try:
    #         function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_MACHINE_TRANSACTION.value)[:4].hex()
    #         calldata_bytes = bytes.fromhex(calldata[2:])
    #         depin_owner_signature_bytes = bytes.fromhex(depin_owner_signature[2:])
    #         smart_account_owner_signature_bytes = bytes.fromhex(smart_account_owner_signature[2:])
            
    #         encoded_params = encode(
    #             ['address', 'address', 'bytes', 'uint256', 'bytes', 'bytes'],
    #             [smart_account_address, target, calldata_bytes, nonce, depin_owner_signature_bytes, smart_account_owner_signature_bytes]
    #         ).hex()
    #         tx: EvmTransaction = {
    #             "to": self.machine_station_address,
    #             "data": f"0x{function_selector}{encoded_params}"
    #         }
    #         self._send_evm_tx(tx)
    #     except Exception as e:
    #         # TODO custom error
    #         raise
        
    # def execute_machine_batch_transaction(self, smart_account_addresses, targets, calldata_list, nonce, machine_nonces, depin_owner_signature, smart_account_owner_signatures):
    #     try:
    #         function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_MACHINE_BATCH_TRANSACTIONS.value)[:4].hex()
            
    #         calldata_list_bytes = [
    #             bytes.fromhex(d[2:])
    #             for d in calldata_list
    #         ]
    #         depin_owner_signature_bytes = bytes.fromhex(depin_owner_signature[2:])
    #         smart_account_owner_signatures_bytes = [
    #             bytes.fromhex(s[2:])
    #             for s in smart_account_owner_signatures
    #         ]
            
    #         encoded_params = encode(
    #             ['address[]', 'address[]', 'bytes[]', 'uint256', 'uint256[]', 'bytes', 'bytes[]'],
    #             [smart_account_addresses, targets, calldata_list_bytes, nonce, machine_nonces, depin_owner_signature_bytes, smart_account_owner_signatures_bytes]
    #         ).hex()
    #         tx: EvmTransaction = {
    #             "to": self.machine_station_address,
    #             "data": f"0x{function_selector}{encoded_params}"
    #         }
    #         self._send_evm_tx(tx)
    #     except Exception as e:
    #         # TODO custom error
    #         raise
        
    # def execute_machine_transfer_balance(self, smart_account_address, recipient_address, nonce, depin_owner_signature, smart_account_owner_signature):
    #     try:
            
    #         function_selector = self.api.keccak(text=MachineStationFactoryFunctionSignatures.EXECUTE_MACHINE_TRANSFER_BALANCE.value)[:4].hex()
    #         depin_owner_signature_bytes = bytes.fromhex(depin_owner_signature[2:])
    #         smart_account_owner_signature_bytes = bytes.fromhex(smart_account_owner_signature[2:])
            
    #         encoded_params = encode(
    #             ['address', 'address', 'uint256', 'bytes', 'bytes'],
    #             [smart_account_address, recipient_address, nonce, depin_owner_signature_bytes, smart_account_owner_signature_bytes]
    #         ).hex()
    #         tx: EvmTransaction = {
    #             "to": self.machine_station_address,
    #             "data": f"0x{function_selector}{encoded_params}"
    #         }
    #         self._send_evm_tx(tx)
    #     except Exception as e:
    #         # TODO custom error
    #         raise
        
