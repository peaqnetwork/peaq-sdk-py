"""objects used in the main sdk initializer"""
# python native imports
from peaq_sdk.types.base import (
    SubstrateSendResult,
    EvmSendResult,
    BuiltEvmTransactionResult,
    BuiltCallTransactionResult
)
from typing import List, Optional, Any, Callable, Union
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

# Type aliases for better TypeScript-like typing
StatusCallback = Optional[Callable[[Any], None]]
TxOptions = Optional[Any]  # Will be defined more specifically in base types


class VerificationMethodType(str, Enum):
    """Verification method types supported by the DID implementation."""
    ECDSA = "EcdsaSecp256k1RecoveryMethod2020"
    ED25519 = "Ed25519VerificationKey2020"
    SR25519 = "Sr25519VerificationKey2020"


class Verification(BaseModel):
    type: VerificationMethodType = Field(..., description="Type of verification method (ECDSA, Ed25519, Sr25519)")
    id: Optional[str] = Field(None, description="Unique identifier for this verification method (optional)")
    controller: Optional[str] = Field(None, description="Controller DID for this verification method (optional)")
    public_key_multibase: Optional[str] = Field(None, alias="publicKeyMultibase", description="Public key in multibase format (optional)")
    
    # model_config = ConfigDict(
    #     populate_by_name=True  # Enables aliases like `publicKeyMultibase` to be used with dict input
    # )

class Signature(BaseModel):
    type: VerificationMethodType = Field(..., description="Signature type (e.g., EcdsaSecp256k1RecoveryMethod2020)")
    issuer: str = Field(..., description="DID of the signature issuer")
    hash: str = Field(..., description="Hash value of the signature")
    
    # model_config = ConfigDict(
    #     populate_by_name=True
    # )

class Service(BaseModel):
    id: str = Field(..., description="Unique identifier for the service")
    type: str = Field(..., description="Service type")
    service_endpoint: Optional[str] = Field(None, alias="serviceEndpoint", description="Service endpoint URL (optional)")
    data: Optional[str] = Field(None, description="Additional service data (optional)")
    
    # model_config = ConfigDict(
    #     populate_by_name=True  # Enables aliases like `serviceEndpoint` to be used with dict input
    # )

class CustomDocumentFields(BaseModel):
    verifications: List[Verification] = Field(default_factory=list, description="List of verification methods")
    signature: Optional[Signature] = Field(None, description="Optional document signature")
    services: List[Service] = Field(default_factory=list, description="List of service endpoints")
    
    # model_config = ConfigDict(
    #     populate_by_name=True
    # )

class CreateDIDOptions(BaseModel):
    name: str = Field(..., description="Unique identifier for the DID document")
    controller: Optional[str] = Field(None, description="Controller DID (optional)")
    did_address: Optional[str] = Field(None, alias="didAddress", description="Target DID address (optional)")
    verification_methods: Optional[List[Verification]] = Field(
        None, alias="verificationMethods", description="List of verification methods to include (optional)"
    )
    services: Optional[List[Service]] = Field(None, description="List of service endpoints (optional)")
    signature: Optional[Signature] = Field(None, description="Optional signature from admin to validate issuance")

    # model_config = ConfigDict(
    #     populate_by_name=True  # Enables aliases like `didAddress` to be used with dict input
    # )
    
class DidFunctionSignatures(str, Enum):
    ADD_ATTRIBUTE = "addAttribute(address,bytes,bytes,uint32)"
    READ_ATTRIBUTE = "readAttribute(address,bytes)"
    UPDATE_ATTRIBUTE = "updateAttribute(address,bytes,bytes,uint32)"
    REMOVE_ATTRIBUTE = "removeAttribute(address,bytes)"

class DidCallFunction(str, Enum):
    ADD_ATTRIBUTE = 'add_attribute'
    READ_ATTRIBUTE = 'peaqdid_readAttribute'
    UPDATE_ATTRIBUTE = 'update_attribute'
    REMOVE_ATTRIBUTE = 'remove_attribute'
    


class DIDV2Document(BaseModel):
    """DID Document structure"""
    id: str = Field(..., description="DID identifier (e.g., did:peaq:0x...)")
    controller: str = Field(..., description="Controller DID")
    verification_method: List[dict] = Field(default_factory=list, alias="verificationMethod", description="List of verification methods")
    authentication: List[str] = Field(default_factory=list, description="List of authentication method references")
    service: List[dict] = Field(default_factory=list, description="List of service endpoints")
    signature: Optional[dict] = Field(None, description="Optional document signature")
    
    # model_config = ConfigDict(
    #     populate_by_name=True  # Enables aliases like `verificationMethod` to be used with dict input
    # )

class DIDDocument(BaseModel):
    """Complete DID Document structure with metadata"""
    name: str = Field(..., description="DID name/identifier")
    value: str = Field(..., description="Raw hex-encoded DID document value")
    validity: str = Field(..., description="Validity period of the DID")
    created: str = Field(..., description="Creation timestamp")
    document: DIDV2Document = Field(..., description="Parsed DID document structure")
    
    # model_config = ConfigDict(
    #     populate_by_name=True
    # )
    
class ReadDidResult(BaseModel):
    name: str = Field(..., description="DID name/identifier")
    value: str = Field(..., description="Raw hex-encoded DID document value")
    validity: str = Field(..., description="Validity period of the DID")
    created: str = Field(..., description="Creation timestamp")
    document: dict = Field(..., description="Parsed DID document as dictionary")

# DidWriteResult is now imported from base.py as a Union type alias
DidWriteResult = Union[SubstrateSendResult, EvmSendResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]

class GetDidError(Exception):
    """Raised when there is a failure to the function get item."""
    pass