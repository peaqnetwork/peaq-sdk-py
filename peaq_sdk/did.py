from peaq_sdk.base import Base
from peaq_sdk.types.common import ChainType, SDKMetadata, SeedError
from peaq_sdk.types.did import CustomDocumentFields, CreateDidResult, Verification
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
            self._generate_did_document(keypair.ss58_address, custom_document_fields)
        
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
        
        # vfields = custom_document_fields.verifications or []
        if custom_document_fields.verifications:
            print(custom_document_fields.verifications)
            for key_counter, verification in enumerate(custom_document_fields.verifications, start=1):
                vm, vm_id = self._create_verification_method(
                    key_counter,
                    address,
                    verification
                )
                doc.verification_methods.append(vm)
                doc.authentications.append(vm_id)
            print("Has verifications")
            
        # if customDocumentFields.signature:
        #     print("Has signature")
        # if customDocumentFields.services:
        #     print("Has services")
        
        serialized_data = doc.SerializeToString()
        serialized_hex = serialized_data.hex()
        deserialized_did = self._deserialize_did(serialized_data)
        print(deserialized_did)
    
    def _create_verification_method(self, key_counter: int, address: str, verification: Verification):
        verification_method = peaq_proto.VerificationMethod()
        id = f"did:peaq:{address}#keys-{key_counter}"
        verification_method.id = id
        
        print(verification)
        if self.__metadata.chain_type is ChainType.EVM:
            if verification.type != "EcdsaSecp256k1RecoveryMethod2020":
                raise ValueError(
                    f"EVM only supports EcdsaSecp256k1RecoveryMethod2020, got {verification.type}"
                )
            verification_method.type = verification.type
            verification_method.controller = f"did:peaq:{address}"
            verification_method.public_key_multibase = address
            return verification_method, id
        
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
        
        return verification_method, id
    
    
    def _deserialize_did(self, data):
        deserialized_doc = peaq_proto.Document()
        deserialized_doc.ParseFromString(data)  # ParseFromString modifies deserialized_doc in place
        return deserialized_doc