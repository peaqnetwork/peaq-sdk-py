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

from substrateinterface.base import SubstrateInterface
from eth_abi import encode

class Did(Base):
    def __init__(self, api, metadata) -> None:
        super().__init__()
        self._api = api
        self.__metadata: SDKMetadata = metadata
        
        
        
    def create(self, name: str, custom_document_fields: CustomDocumentFields, address: Optional[str] = None) -> Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
        """Creates a new DID for the previously initialized wallet / keyring"""
        if not isinstance(custom_document_fields, CustomDocumentFields):
            raise TypeError(
                f"custom_document_fields object must be CustomDocumentFields, "
                f"got {type(custom_document_fields).__name__!r}"
            )

        user_address = self._resolve_address(chain_type=self.__metadata.chain_type, pair=self.__metadata.pair, address=address)
        
        serialized_did = self._generate_did_document(user_address, custom_document_fields)
        
        if self.__metadata.chain_type is ChainType.EVM:                
            did_function_selector = self._api.keccak(text=DidFunctionSignatures.ADD_ATTRIBUTE.value)[:4].hex()
            name_encoded = name.encode("utf-8").hex()
            did_encoded = serialized_did.encode("utf-8").hex()
            encoded_params = encode(
                ['address', 'bytes', 'bytes', 'uint32'],
                [user_address, bytes.fromhex(name_encoded), bytes.fromhex(did_encoded), 0]
            ).hex()
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.DID.value,
                "data": f"0x{did_function_selector}{encoded_params}"
            }
            
            if self.__metadata.pair:
                receipt = self._send_evm_tx(tx, self.__metadata.pair)
                return WrittenTransactionResult(
                    message=f"Successfully added the DID under the name {name} for user {user_address}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed DID create transaction for {user_address} of the name {name}. You must sign and send it externally.",
                    tx=tx
                )
                
        else:
            call = self._api.compose_call(
                call_module=CallModule.PEAQ_DID.value,
                call_function=DidCallFunction.ADD_ATTRIBUTE.value,
                call_params={
                    'did_account': user_address,
                    'name': name,
                    'value': serialized_did,
                    'valid_for': None
                    }
            )
            
            if self.__metadata.pair:
                receipt = self._send_substrate_tx(call, self.__metadata.pair)
                return WrittenTransactionResult(
                    message=f"Successfully added the DID under the name {name} for user {user_address}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed DID create call for {user_address} of the name {name}. You must sign and send externally.",
                    call=call
                )
            
            
            
    def read(self, name: str, address: Optional[str] = None, wss_base_url: Optional[str] = None) -> ReadDidResult:
        """Reads DID at the given name for the keypair/wallet attached, or without using passing seed at create instance, and address can be used to read."""
        
        if self.__metadata.chain_type is ChainType.EVM:
            evm_address = (
                getattr(self.__metadata.pair, 'address', address)
                if self.__metadata.pair
                else address
            )
            if not evm_address:
                raise TypeError(f"Address is set to {evm_address}. Please either set seed at instance creation or pass an address.")
            if not wss_base_url:
                raise BaseUrlError(f"Must pass a wss base url when reading from EVM.")
            owner_address = evm_to_address(evm_address)
            api = SubstrateInterface(url=wss_base_url, ss58_format=42)
        else:
            owner_address = (
                getattr(self.__metadata.pair, 'ss58_address', address)
                if self.__metadata.pair
                else address
            )
            if not owner_address:
                raise TypeError(f"Address is set to {owner_address}. Please either set seed at instance creation or pass an address.")
            api = self._api
        
        # Query storage
        name_encoded = "0x" + name.encode("utf-8").hex()
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            DidCallFunction.READ_ATTRIBUTE.value, [owner_address, name_encoded, block_hash]
        )
        # Check result
        if resp['result'] is None:
            raise GetDidError(f"DID of name {name} was not found at address {owner_address}.")

        read_name = bytes.fromhex(resp['result']['name'][2:]).decode('utf-8')
        value = bytes.fromhex(resp['result']['value'][2:]).decode('utf-8')
        to_deserialize = bytes.fromhex(value)
        document = self._deserialize_did(to_deserialize)
        
        return ReadDidResult(
            name=read_name,
            value=value,
            validity=str(resp['result']['validity']),
            created=str(resp['result']['created']),
            document=document
        )



    def update(self, name: str, custom_document_fields: CustomDocumentFields, address: Optional[str] = None) -> Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
        """Overwrites the existing data in full"""
        if not isinstance(custom_document_fields, CustomDocumentFields):
            raise TypeError(
                f"custom_document_fields object must be CustomDocumentFields, "
                f"got {type(custom_document_fields).__name__!r}"
            )
            
        user_address = self._resolve_address(chain_type=self.__metadata.chain_type, pair=self.__metadata.pair, address=address)
        
        serialized_did = self._generate_did_document(user_address, custom_document_fields)
        
        if self.__metadata.chain_type is ChainType.EVM:
            serialized_did = self._generate_did_document(user_address, custom_document_fields)
            did_function_selector = self._api.keccak(text=DidFunctionSignatures.UPDATE_ATTRIBUTE.value)[:4].hex()
            name_encoded = name.encode("utf-8").hex()
            did_encoded = serialized_did.encode("utf-8").hex()
            
            encoded_params = encode(
                ['address', 'bytes', 'bytes', 'uint32'],
                [user_address, bytes.fromhex(name_encoded), bytes.fromhex(did_encoded), 0]
            ).hex()
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.DID.value,
                "data": f"0x{did_function_selector}{encoded_params}"
            }
            
            if self.__metadata.pair:
                receipt = self._send_evm_tx(tx, self.__metadata.pair)
                return WrittenTransactionResult(
                    message=f"Successfully updated the DID under the name {name} for user {user_address}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed DID update transaction for {user_address} of the name {name}. You must sign and send it externally.",
                    tx=tx
                )
                
        else:
            call = self._api.compose_call(
                call_module=CallModule.PEAQ_DID.value,
                call_function=DidCallFunction.UPDATE_ATTRIBUTE.value,
                call_params={
                    'did_account': user_address,
                    'name': name,
                    'value': serialized_did,
                    'valid_for': None
                    }
            )
            
            if self.__metadata.pair:
                receipt = self._send_substrate_tx(call, self.__metadata.pair)
                return WrittenTransactionResult(
                    message=f"Successfully updated the DID under the name {name} for user {user_address}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed DID update call for {user_address} of the name {name}. You must sign and send externally.",
                    call=call
                )


    
    def remove(self, name: str, address: Optional[str] = None) -> Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
        """Removes DID at the given name for the keypair/wallet attached"""
        
        user_address = self._resolve_address(chain_type=self.__metadata.chain_type, pair=self.__metadata.pair, address=address)
        
        if self.__metadata.chain_type is ChainType.EVM:
            did_function_selector = self._api.keccak(text=DidFunctionSignatures.REMOVE_ATTRIBUTE.value)[:4].hex()
            name_encoded = name.encode("utf-8").hex()
            encoded_params = encode(
                ['address', 'bytes'],
                [user_address, bytes.fromhex(name_encoded)]
            ).hex()
            
            tx: EvmTransaction = {
                "to": PrecompileAddresses.DID.value,
                "data": f"0x{did_function_selector}{encoded_params}"
            }
            
            if self.__metadata.pair:
                receipt = self._send_evm_tx(tx, self.__metadata.pair)
                return WrittenTransactionResult(
                    message=f"Successfully removed the DID under the name {name} for user {user_address}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed DID remove transaction for {user_address} of the name {name}. You must sign and send it externally.",
                    tx=tx
                )
                
        else:
            call = self._api.compose_call(
                call_module=CallModule.PEAQ_DID.value,
                call_function=DidCallFunction.REMOVE_ATTRIBUTE.value,
                call_params={
                    'did_account': user_address,
                    'name': name
                    }
            )
            
            if self.__metadata.pair:
                receipt = self._send_substrate_tx(call, self.__metadata.pair)
                return WrittenTransactionResult(
                    message=f"Successfully removed the DID under the name {name} for user {user_address}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed DID remove call for {user_address} of the name {name}. You must sign and send externally.",
                    call=call
                )
    
    
    def _generate_did_document(self, address: str, custom_document_fields: CustomDocumentFields) -> str:
        doc = peaq_proto.Document()
        doc.id = f"did:peaq:{address}"
        doc.controller = f"did:peaq:{address}"
        
        if custom_document_fields.verifications:
            for key_counter, verification in enumerate(custom_document_fields.verifications, start=1):
                id = f"did:peaq:{address}#keys-{key_counter}"
                verification_method = self._create_verification_method(
                    id,
                    address,
                    verification
                )
                doc.verification_methods.append(verification_method)
                doc.authentications.append(id)
            
        if custom_document_fields.signature:
            document_signature = self._add_signature(custom_document_fields.signature)
            doc.signature.CopyFrom(document_signature)

            
        if custom_document_fields.services:
            for service in custom_document_fields.services:
                document_service = self._add_service(service)
                doc.services.append(document_service)
        
        serialized_data = doc.SerializeToString()
        serialized_hex = serialized_data.hex()
        return serialized_hex
    
    def _create_verification_method(self, id: str, address: str, verification: Verification) -> peaq_proto.VerificationMethod:
        verification_method = peaq_proto.VerificationMethod()
        verification_method.id = id
        
        if self.__metadata.chain_type is ChainType.EVM:
            if verification.type != "EcdsaSecp256k1RecoveryMethod2020":
                raise ValueError(
                    f"EVM only supports EcdsaSecp256k1RecoveryMethod2020, got {verification.type}"
                )
            verification_method.type = verification.type
            verification_method.controller = f"did:peaq:{address}"
            verification_method.public_key_multibase = address
            return verification_method
        
        if verification.type not in ("Ed25519VerificationKey2020", "Sr25519VerificationKey2020", "EcdsaSecp256k1RecoveryMethod2020"):
            raise ValueError(
                "Substrate verification.type must be "
                "'Ed25519VerificationKey2020', 'Sr25519VerificationKey2020', or 'EcdsaSecp256k1RecoveryMethod2020'"
            )
        verification_method.type = verification.type
        verification_method.controller = f"did:peaq:{address}"
    
        if verification.public_key_multibase:
            verification_method.public_key_multibase = verification.public_key_multibase
        else:
            verification_method.public_key_multibase = address
        
        return verification_method
    
    def _add_signature(self, signature: Signature) -> peaq_proto.Signature:
        allowed = {
            "EcdsaSecp256k1RecoveryMethod2020",
            "Ed25519VerificationKey2020",
            "Sr25519VerificationKey2020",
        }
        if signature.type not in allowed:
            raise ValueError(
                'Signature.type must be one of '
                '"EcdsaSecp256k1RecoveryMethod2020", '
                '"Ed25519VerificationKey2020", or '
                '"Sr25519VerificationKey2020".'
            )
        if not signature.issuer:
            raise ValueError("Signature.issuer is required")
        if not signature.hash:
            raise ValueError("Signature.hash is required")

        proto_signature = peaq_proto.Signature()
        proto_signature.type = signature.type
        proto_signature.issuer = signature.issuer
        proto_signature.hash = signature.hash
        return proto_signature
    
    def _add_service(self, service: Service):
        if not service.id:
            raise ValueError("Service.id is required")
        if not service.type:
            raise ValueError("Service.type is required")
        if not (service.service_endpoint or service.data):
            raise ValueError(
                "Either serviceEndpoint or data must be provided for Service"
            )
        proto_service = peaq_proto.Services()
        proto_service.id = service.id
        proto_service.type = service.type

        if service.service_endpoint:
            proto_service.service_endpoint = service.service_endpoint
        if service.data:
            proto_service.data = service.data

        return proto_service
    
    def _deserialize_did(self, data):
        deserialized_doc = peaq_proto.Document()
        deserialized_doc.ParseFromString(data)  # ParseFromString modifies deserialized_doc in place
        return deserialized_doc