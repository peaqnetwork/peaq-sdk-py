from peaq_sdk.base import Base
from peaq_sdk.types.common import ChainType, SDKMetadata, SeedError, CallModule
from peaq_sdk.types.did import (
    CustomDocumentFields, 
    CreateDidResult,
    Verification,
    Signature,
    Service,
    DidFunctionSignatures,
    DidCallFunction
)
from peaq_sdk.utils import peaq_proto


class Did(Base):
    def __init__(self, api, metadata) -> None:
        super().__init__()
        self._api = api
        self.__metadata: SDKMetadata = metadata
    def create(self, name: str, custom_document_fields: CustomDocumentFields) -> CreateDidResult:
        if not isinstance(custom_document_fields, CustomDocumentFields):
            raise TypeError(
                f"custom_document_fields object must be CustomDocumentFields, "
                f"got {type(custom_document_fields).__name__!r}"
            )
        if not self.__metadata.pair:
            raise SeedError(
                "No seed/private key set for the operation 'create'. "
                "Unable to perform the write transaction."
            )
        if self.__metadata.chain_type is ChainType.EVM:
            account = self.__metadata.pair
            self._generate_did_document(account.address, custom_document_fields)
        else:
            keypair = self.__metadata.pair
            value = self._generate_did_document(keypair.ss58_address, custom_document_fields)
            call = self._api.compose_call(
                call_module=CallModule.PEAQ_DID.value,
                call_function=DidCallFunction.ADD_ATTRIBUTE.value,
                call_params={
                    'did_account': keypair.ss58_address,
                    'name': name,
                    'value': value,
                    'valid_for': None
                    }
            )
            receipt = self._send_substrate_tx(call, keypair)
            return CreateDidResult(
                message=f"Successfully added the DID under the name {name} for user {keypair.ss58_address}",
                receipt=receipt
            )
        pass
    def read():
        pass
    def update():
        pass
    def remove():
        pass
    
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
        # deserialized_did = self._deserialize_did(serialized_data)
        # print(deserialized_did)
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