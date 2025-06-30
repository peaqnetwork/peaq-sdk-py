import requests
import secrets

from typing import Optional, Union

from peaq_sdk.base import Base
from peaq_sdk.types.common import (
    SDKMetadata,
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
from web3.types import TxParams
from eth_abi import encode
from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import keccak, to_hex



# TODO:
# - Check default DID document fields
# - Error handling

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

    # ========================================================================
    # PUBLIC/CALLABLE FUNCTIONS
    # ========================================================================
        
    def create_machine_account(self, owner_eoa_address: str, nonce: Optional[int] = None, send_transaction: bool = False):
        """
        Creates a new smart account owned by the provided EOA address.

        Args:
            owner_eoa_address (str): The Externally Owned Account address that will own the smart account.
            nonce (Optional[int]): Optional nonce value. If not provided, a random 32-bit integer will be generated.
            send_transaction (bool): If True, sends the transaction automatically. If False, returns transaction data for frontend wallet submission.

        Returns:
            Union[str, dict]: The address of the newly created smart account if sent, or transaction data if send_transaction=False.
        """
        if nonce is None:
            nonce = secrets.randbits(32)
            
        admin_signature = self.admin_sign_deploy_machine_smart_account(owner_eoa_address, nonce)
        result = self.deploy_machine_smart_account(owner_eoa_address, nonce, admin_signature, send_transaction)
        return result
    
    def transfer_machine_station_balance(self, new_machine_station_address: str, nonce: Optional[int] = None, send_transaction: bool = False) -> str:
        """
        Transfers the balance from the current machine station to a new machine station address.
        This is typically used when upgrading or migrating to a new machine station contract.

        Args:
            new_machine_station_address (str): The address of the new machine station contract that will receive the balance.
            nonce (Optional[int]): Optional nonce value. If not provided, a random 32-bit integer will be generated.
            send_transaction (bool): If True, sends the transaction automatically. If False, returns transaction data for frontend wallet submission.

        Returns:
            Union[str, dict]: Success message with the new machine station address if sent, or transaction data if send_transaction=False.

        Note:
            This operation requires the machine station owner's signature and can only be executed by 
            the current machine station owner.
        """
        if nonce is None:
            nonce = secrets.randbits(32)
            
        admin_signature = self.admin_sign_transfer_machine_station_balance(new_machine_station_address, nonce)
        result = self.execute_transfer_machine_station_balance(new_machine_station_address, nonce, admin_signature, send_transaction)

        return result
    
    def storage_tx(
        self,
        email: str,
        item_type: str,
        item: str,
        tag: str,
        nonce: Optional[int] = None,
        refund_amount: Optional[int] = None,
        send_transaction: bool = False
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
            nonce (Optional[int]): Optional nonce value. If not provided, a random 32-bit integer will be generated.
            refund_amount (Optional[int]): Optional refund amount. If not provided, defaults to 0.
            send_transaction (bool): If True, sends the transaction automatically. If False, returns transaction data for frontend wallet submission.

        Returns:
            Union[str, dict]: "Success" if the transaction is completed successfully, or transaction data if send_transaction=False.
        """
        if nonce is None:
            nonce = secrets.randbits(32)
        if refund_amount is None:
            refund_amount = 0
            
        storage_data = self.generate_storage_tx(email, item_type, item, tag, nonce, refund_amount)
        
        result = self.execute_transaction(
            storage_data['target'],
            storage_data['calldata'],
            storage_data['nonce'],
            storage_data['refund_amount'],
            storage_data['admin_signature'],
            send_transaction
        )
        return result
    
    def did_tx(self, project, email, account_address, tag, custom_document_fields: Optional[str] = None, nonce: Optional[int] = None, refund_amount: Optional[int] = None, send_transaction: bool = False):
        """
        Generates and executes a Get Real specific DID transaction.

        Args:
            project (str): Project name for the DID.
            email (str): Email address for verification.
            account_address (str): The EOA address of the account.
            tag (str): Tag for linking the transaction.
            custom_document_fields (Optional[str]): Custom DID document fields.
            nonce (Optional[int]): Optional nonce value. If not provided, a random 32-bit integer will be generated.
            refund_amount (Optional[int]): Optional refund amount. If not provided, defaults to 0.
            send_transaction (bool): If True, sends the transaction automatically. If False, returns transaction data for frontend wallet submission.

        Returns:
            Union[str, dict]: Transaction result if sent, or transaction data if send_transaction=False.
        """
        if nonce is None:
            nonce = secrets.randbits(32)
        if refund_amount is None:
            refund_amount = 0
            
        did_data = self.generate_did_tx(project, email, account_address, tag, custom_document_fields, nonce, refund_amount)
        
        result = self.execute_transaction(
            did_data['target'],
            did_data['calldata'],
            did_data['nonce'],
            did_data['refund_amount'],
            did_data['admin_signature'],
            send_transaction
        )
        return result
    
    def machine_account_storage_tx(self, machine_account_address, email, item_type, item, tag, machine_account_signature: Optional[str] = None, nonce: Optional[int] = None, refund_amount: Optional[int] = None, send_transaction: bool = False):
        """
        Executes a storage transaction through a smart account.
        
        If machine_account_signature is not provided, this method will return a signable message
        object that should be sent to the frontend for the machine account owner to sign.
        
        Args:
            machine_account_address (str): Address of the smart account
            email (str): Email address for verification
            item_type (str): Type/key of the item to store
            item (str): The data to store
            tag (str): Tag for linking the transaction
            machine_account_signature (Optional[str]): Pre-signed signature from machine account owner
            nonce (Optional[int]): Optional nonce value. If not provided, a random 32-bit integer will be generated.
            refund_amount (Optional[int]): Optional refund amount. If not provided, defaults to 0.
            send_transaction (bool): If True, sends the transaction automatically. If False, returns transaction data for frontend wallet submission.
            
        Returns:
            Union[WrittenTransactionResult, dict]: Transaction result if signature provided and sent, 
                                                 signable message object for frontend signing, or 
                                                 transaction data if send_transaction=False
        """
        if nonce is None:
            nonce = secrets.randbits(32)
        if refund_amount is None:
            refund_amount = 0
            
        # If no signature provided, generate and return signable message for frontend
        if machine_account_signature is None:
            return self._generate_machine_account_storage_signable_message(
                machine_account_address, email, item_type, item, tag, nonce, refund_amount
            )
        
        # If signature provided, generate transaction data and execute
        machine_account_storage_data = self.generate_machine_account_storage_tx(
            machine_account_address, email, item_type, item, tag, machine_account_signature, nonce, refund_amount
        )
        
        # Execute the transaction
        result = self.execute_machine_transaction(
            machine_account_storage_data['machine_account_address'],
            machine_account_storage_data['target'],
            machine_account_storage_data['calldata'],
            machine_account_storage_data['nonce'],
            machine_account_storage_data['refund_amount'],
            machine_account_storage_data['admin_signature'],
            machine_account_storage_data['machine_account_signature'],
            send_transaction
        )
        return result
        
    def machine_account_did_tx(self, account_address, machine_account_address, project, email, tag, custom_document_fields: Optional[str] = None, machine_account_signature: Optional[str] = None, nonce: Optional[int] = None, refund_amount: Optional[int] = None, send_transaction: bool = False):
        """
        Executes a DID transaction through a smart account.
        
        If machine_account_signature is not provided, this method will return a signable message
        object that should be sent to the frontend for the machine account owner to sign.
        
        Args:
            account_address (str): The EOA address of the account owner
            machine_account_address (str): Address of the smart account
            project (str): Project name for the DID
            email (str): Email address for verification
            tag (str): Tag for linking the transaction
            custom_document_fields (Optional[str]): Custom DID document fields
            machine_account_signature (Optional[str]): Pre-signed signature from machine account owner
            nonce (Optional[int]): Optional nonce value. If not provided, a random 32-bit integer will be generated.
            refund_amount (Optional[int]): Optional refund amount. If not provided, defaults to 0.
            send_transaction (bool): If True, sends the transaction automatically. If False, returns transaction data for frontend wallet submission.
            
        Returns:
            Union[WrittenTransactionResult, dict]: Transaction result if signature provided and sent, 
                                                 signable message object for frontend signing, or 
                                                 transaction data if send_transaction=False
        """
        if nonce is None:
            nonce = secrets.randbits(32)
        if refund_amount is None:
            refund_amount = 0
            
        # If no signature provided, generate and return signable message for frontend
        if machine_account_signature is None:
            return self._generate_machine_account_did_signable_message(
                account_address, machine_account_address, project, email, tag, custom_document_fields, nonce, refund_amount
            )
        
        # If signature provided, generate transaction data and execute
        machine_account_did_data = self.generate_machine_account_did_tx(
            account_address, machine_account_address, project, email, tag, custom_document_fields, machine_account_signature, nonce, refund_amount
        )
        
        # Execute the transaction
        result = self.execute_machine_transaction(
            machine_account_did_data['machine_account_address'],
            machine_account_did_data['target'],
            machine_account_did_data['calldata'],
            machine_account_did_data['nonce'],
            machine_account_did_data['refund_amount'],
            machine_account_did_data['admin_signature'],
            machine_account_did_data['machine_account_owner_signature'],
            send_transaction
        )
        return result
    
    def machine_account_batch_txs(self, data_payloads, nonce: Optional[int] = None, refund_amount: Optional[int] = None, send_transaction: bool = False):
        """
        Executes a batch of machine account transactions.
        
        Args:
            data_payloads (list): List of transaction payloads.
            nonce (Optional[int]): Optional nonce value. If not provided, a random 32-bit integer will be generated.
            refund_amount (Optional[int]): Optional refund amount. If not provided, defaults to 0.
            send_transaction (bool): If True, sends the transaction automatically. If False, returns transaction data for frontend wallet submission.
            
        Returns:
            Union[WrittenTransactionResult, dict]: Transaction result if sent, or transaction data if send_transaction=False.
        """
        if nonce is None:
            nonce = secrets.randbits(32)
        if refund_amount is None:
            refund_amount = 0
            
        # Unpack data payload
        machine_account_addresses = [tx["machine_account_address"] for tx in data_payloads]
        targets = [tx["target"] for tx in data_payloads]
        calldata_list = [tx["calldata"] for tx in data_payloads]
        machine_nonces = [tx["nonce"] for tx in data_payloads]
        machine_account_owner_signatures = [tx["machine_account_owner_signature"] for tx in data_payloads]

        depin_owner_signature = self.admin_sign_machine_batch_transactions(machine_account_addresses, targets, calldata_list, nonce, refund_amount, machine_nonces)
        
        result = self.execute_machine_batch_transactions(    
            machine_account_addresses,
            targets,
            calldata_list,
            nonce,
            refund_amount,
            machine_nonces,
            depin_owner_signature,
            machine_account_owner_signatures,
            send_transaction
        )
        
        return result

    def machine_account_transfer_balance(self, machine_account_address, recipient_address, nonce: Optional[int] = None):
        """
        Transfers balance from a machine account to a recipient address.
        
        Args:
            machine_account_address (str): Address of the machine account.
            recipient_address (str): Address to receive the balance.
            nonce (Optional[int]): Optional nonce value. If not provided, a random 32-bit integer will be generated.
            
        Returns:
            Transaction result.
        """
        if nonce is None:
            nonce = secrets.randbits(32)
        
        machine_account_owner_signature = self.machine_sign_transfer_machine_balance(machine_account_address, recipient_address, nonce)
        depin_owner_signature = self.admin_sign_transfer_machine_balance(machine_account_address, recipient_address, nonce)
        
        result = self.execute_transfer_machine_balance(
            machine_account_address,
            recipient_address,
            nonce,
            depin_owner_signature,
            machine_account_owner_signature
        )
        
        return result

    # ========================================================================
    # HELPER/PRIVATE FUNCTIONS
    # ========================================================================

    def _generate_machine_account_storage_signable_message(self, machine_account_address, email, item_type, item, tag, nonce, refund_amount):
        """
        Generates a signable message for smart account storage transaction.
        
        Returns:
            dict: Complete response with signable message and transaction data for frontend
        """
        response = self.store_data_key(email, item_type, tag)
        # TODO check validity
        
        storage_calldata = self.sdk.storage.add_item(item_type, item)
        
        # Generate signable message for machine account owner
        signable_message = self.machine_sign_machine_transaction(
            machine_account_address, 
            PrecompileAddresses.STORAGE.value, 
            storage_calldata.tx['data'], 
            nonce
        )
        
        # Generate admin signature (can be done now since we have the private key)
        admin_signature = self.admin_sign_machine_transaction(
            machine_account_address, 
            PrecompileAddresses.STORAGE.value, 
            storage_calldata.tx['data'], 
            nonce,
            refund_amount
        )
        
        return {
            "message": "Machine account signature required. Please sign this message with the machine account owner's private key.",
            "signable_message": signable_message,
            "transaction_data": {
                "machine_account_address": machine_account_address,
                "target": PrecompileAddresses.STORAGE.value,
                "calldata": storage_calldata.tx['data'],
                "nonce": nonce,
                "admin_signature": admin_signature,
                "email": email,
                "item_type": item_type,
                "item": item,
                "tag": tag,
                "refund_amount": refund_amount
            }
        }
        
    def generate_machine_account_storage_tx(self, machine_account_address, email, item_type, item, tag, signature: str, nonce, refund_amount):
        """
        Generates smart account storage transaction data with provided signature.
        This method assumes a valid signature is provided.
        
        Args:
            machine_account_address (str): Address of the smart account
            email (str): Email address for verification  
            item_type (str): Type/key of the item to store
            item (str): The data to store
            tag (str): Tag for linking the transaction
            signature (str): Machine account owner's signature
            nonce (int): Transaction nonce
            refund_amount (int): Transaction refund amount
            
        Returns:
            dict: Transaction data ready for execution
        """
        response = self.store_data_key(email, item_type, tag)
        # TODO check validity
        
        storage_calldata = self.sdk.storage.add_item(item_type, item)
        admin_signature = self.admin_sign_machine_transaction(
            machine_account_address, 
            PrecompileAddresses.STORAGE.value, 
            storage_calldata.tx['data'], 
            nonce,
            refund_amount
        )
        
        return {
            "machine_account_address": machine_account_address,
            "target": PrecompileAddresses.STORAGE.value,
            "calldata": storage_calldata.tx['data'],
            "nonce": nonce,
            "refund_amount": refund_amount,
            "admin_signature": admin_signature,
            "machine_account_signature": signature
        }

    def _generate_machine_account_did_signable_message(self, account_address, machine_account_address, project, email, tag, custom_document_fields: Optional[str] = None, nonce: int = None, refund_amount: int = None):
        """
        Generates a signable message for smart account DID transaction.
        
        Returns:
            dict: Complete response with signable message and transaction data for frontend
        """
        # TODO who is generating this signature? Create machine address or the eoa?
        # MAY NEED TO CHANGE TO machine_account_address
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
                          Service(id='#machine_account_address', type='address', data=machine_account_address),
                          Service(id='#machine_account_eoa_address', type='address', data=account_address)]
            )
        
        did_calldata = self.sdk.did.create(name=project, custom_document_fields=custom_fields, address=machine_account_address)
        
        # Generate signable message for machine account owner
        signable_message = self.machine_sign_machine_transaction(
            machine_account_address, 
            PrecompileAddresses.DID.value, 
            did_calldata.tx['data'], 
            nonce
        )
        
        # Generate depin owner signature (can be done now since we have the private key)
        admin_signature = self.admin_sign_machine_transaction(
            machine_account_address, 
            PrecompileAddresses.DID.value, 
            did_calldata.tx['data'], 
            nonce,
            refund_amount
        )
        
        return {
            "message": "Machine account signature required. Please sign this message with the machine account owner's private key.",
            "signable_message": signable_message,
            "transaction_data": {
                "machine_account_address": machine_account_address,
                "target": PrecompileAddresses.DID.value,
                "calldata": did_calldata.tx['data'],
                "nonce": nonce,
                "admin_signature": admin_signature,
                "account_address": account_address,
                "project": project,
                "email": email,
                "tag": tag,
                "custom_document_fields": custom_document_fields,
                "refund_amount": refund_amount
            }
        }

    def generate_machine_account_did_tx(self, account_address, machine_account_address, project, email, tag, custom_document_fields: Optional[str] = None, signature: str = None, nonce: int = None, refund_amount: int = None):
        """
        Generates smart account DID transaction data with provided signature.
        This method assumes a valid signature is provided.
        
        Args:
            account_address (str): The EOA address of the account owner
            machine_account_address (str): Address of the smart account
            project (str): Project name for the DID
            email (str): Email address for verification
            tag (str): Tag for linking the transaction
            custom_document_fields (Optional[str]): Custom DID document fields
            signature (str): Machine account owner's signature
            nonce (int): Transaction nonce
            refund_amount (int): Transaction refund amount
            
        Returns:
            dict: Transaction data ready for execution
        """
        # TODO who is generating this signature? Create machine address or the eoa?
        # MAY NEED TO CHANGE TO machine_account_address
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
                          Service(id='#machine_account_address', type='address', data=machine_account_address),
                          Service(id='#machine_account_eoa_address', type='address', data=account_address)]
            )
        
        did_calldata = self.sdk.did.create(name=project, custom_document_fields=custom_fields, address=machine_account_address)
        admin_signature = self.admin_sign_machine_transaction(
            machine_account_address, 
            PrecompileAddresses.DID.value, 
            did_calldata.tx['data'], 
            nonce,
            refund_amount
        )
        
        return {
            "machine_account_address": machine_account_address,
            "target": PrecompileAddresses.DID.value,
            "calldata": did_calldata.tx['data'],
            "nonce": nonce,
            "admin_signature": admin_signature,
            "machine_account_owner_signature": signature,
            "refund_amount": refund_amount
        }

    def generate_storage_tx(self, email, item_type, item, tag, nonce, refund_amount):
        """
        Generates storage transaction data for direct execution.
        
        Args:
            email (str): Email address for verification
            item_type (str): Type/key of the item to store
            item (str): The data to store
            tag (str): Tag for linking the transaction
            nonce (int): Transaction nonce
            refund_amount (int): Transaction refund amount
            
        Returns:
            dict: Transaction data ready for execution
        """
        response = self.store_data_key(email, item_type, tag)
        # TODO make sure you get a valid response back
        
        storage_calldata = self.sdk.storage.add_item(item_type, item)
        admin_signature = self.admin_sign_transaction(PrecompileAddresses.STORAGE.value, storage_calldata.tx['data'], nonce, refund_amount)
    
        return {
            "target": PrecompileAddresses.STORAGE.value,
            "calldata": storage_calldata.tx['data'],
            "nonce": nonce,
            "refund_amount": refund_amount,
            "admin_signature": admin_signature
        }
    
    def generate_did_tx(self, project, email, account_address, tag, custom_document_fields: Optional[str] = None, nonce: int = None, refund_amount: int = None):
        """
        Generates DID transaction data for direct execution.
        
        Args:
            project (str): Project name for the DID
            email (str): Email address for verification
            account_address (str): The EOA address of the account
            tag (str): Tag for linking the transaction
            custom_document_fields (Optional[str]): Custom DID document fields
            nonce (int): Transaction nonce
            refund_amount (int): Transaction refund amount
            
        Returns:
            dict: Transaction data ready for execution
        """
        account_email_signature = self.generate_email_signature(email, account_address, tag)
        
        if custom_document_fields:
            custom_fields = custom_document_fields
            # TODO must be able to add signature to the service
        else:
            # TODO default fields
            custom_fields = CustomDocumentFields(
                verifications=[Verification(type="EcdsaSecp256k1RecoveryMethod2020")],
                # signature=[Signature], TODO do we want a signature here?
                services=[Service(id='#emailSignature', type='emailSignature', data=account_email_signature),
                          Service(id='#depin_project_address', type='address', data=self.machine_station_account.address),
                          Service(id='#eoa_address', type='address', data=account_address)]
            )

        # only case for depin to create its own?
        did_calldata = self.sdk.did.create(name=project, custom_document_fields=custom_fields, address=account_address)
        admin_signature = self.admin_sign_transaction(PrecompileAddresses.DID.value, did_calldata.tx['data'], nonce, refund_amount)

        return {
            "target": PrecompileAddresses.DID.value,
            "calldata": did_calldata.tx['data'],
            "nonce": nonce,
            "refund_amount": refund_amount,
            "admin_signature": admin_signature
        }

    # ========================================================================
    # SERVICE INTERACTION FUNCTIONS
    # ========================================================================

    def store_data_key(self, email, item_type, tag):
        """
        Stores data key in the Get Real service for verification.
        
        Args:
            email (str): Email address for verification
            item_type (str): Type/key of the item to store
            tag (str): Tag for linking the transaction
            
        Returns:
            dict: Service response
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
        
    def generate_email_signature(self, email, machine_account_address, tag):
        """
        Generates email signature through the Get Real service.
        
        Args:
            email (str): Email address for verification
            machine_account_address (str): DID address for the signature
            tag (str): Tag for linking the transaction
            
        Returns:
            str: Email signature
        """
        try:
            data = {
                "email": email,
                "did_address": machine_account_address,
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