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


class VerificationMethodType(str, Enum):
    """Verification method types supported by the DID implementation."""
    ECDSA = "EcdsaSecp256k1RecoveryMethod2020"
    ED25519 = "Ed25519VerificationKey2020"
    SR25519 = "Sr25519VerificationKey2020"


class Verification(BaseModel):
    type: VerificationMethodType = Field(..., description="Type of verification method (ECDSA, Ed25519, Sr25519)")
    id: Optional[str] = Field(None, description="Unique identifier for this verification method (optional)")
    controller: Optional[str] = Field(None, description="Controller DID for this verification method (optional)")
    public_key_multibase: Optional[str] = Field(None, description="Public key in multibase format (optional)")


class Signature(BaseModel):
    type: VerificationMethodType = Field(..., description="Signature type (e.g., EcdsaSecp256k1RecoveryMethod2020)")
    issuer: str = Field(..., description="DID of the signature issuer")
    hash: str = Field(..., description="Hash value of the signature")


class Service(BaseModel):
    id: str = Field(..., description="Unique identifier for the service")
    type: str = Field(..., description="Service type")
    service_endpoint: Optional[str] = Field(None, description="Service endpoint URL (optional)")
    data: Optional[str] = Field(None, description="Additional service data (optional)")


class CustomDocumentFields(BaseModel):
    verifications: List[Verification] = Field(default_factory=list, description="List of verification methods")
    signature: Optional[Signature] = Field(None, description="Optional document signature")
    services: List[Service] = Field(default_factory=list, description="List of service endpoints")


class CreateDIDOptions(BaseModel):
    name: str = Field(..., description="Unique identifier for the DID document")
    controller: Optional[str] = Field(None, description="Controller DID (optional)")
    did_address: Optional[str] = Field(None, description="Target DID address (optional)")
    verification_methods: Optional[List[Verification]] = Field(
        None, description="List of verification methods to include (optional)"
    )
    services: Optional[List[Service]] = Field(None, description="List of service endpoints (optional)")
    signature: Optional[Signature] = Field(None, description="Optional signature from admin to validate issuance")


class ReadDIDOptions(BaseModel):
    """Options for reading a DID document"""
    name: str = Field(..., description="DID name/identifier to read")
    address: Optional[str] = Field(None, description="Address owning the DID (optional, defaults to connected wallet)")

class UpdateDIDOptions(BaseModel):
    """Options for updating a DID document"""
    name: str = Field(..., description="Unique identifier for the DID document to update")
    controller: Optional[str] = Field(None, description="Controller DID (optional)")
    did_address: Optional[str] = Field(None, description="Target DID address (optional)")
    verification_methods: Optional[List[Verification]] = Field(
        None, description="List of verification methods to include (optional)"
    )
    services: Optional[List[Service]] = Field(None, description="List of service endpoints (optional)")
    signature: Optional[Signature] = Field(None, description="Optional signature from admin to validate issuance")

class RemoveDIDOptions(BaseModel):
    """Options for removing a DID document"""
    name: str = Field(..., description="DID name/identifier to remove")
    address: Optional[str] = Field(None, description="Address owning the DID (optional, defaults to connected wallet)")
    
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
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: str = Field(..., description="DID identifier (e.g., did:peaq:0x...)")
    controller: str = Field(..., description="Controller DID")
    verificationMethod: List[dict] = Field(default_factory=list, description="List of verification methods")
    authentication: List[str] = Field(default_factory=list, description="List of authentication method references")
    service: List[dict] = Field(default_factory=list, description="List of service endpoints")
    signature: Optional[dict] = Field(None, description="Optional document signature")
    
    def __str__(self):
        """String representation for printing"""
        return self.model_dump_json(indent=2)
    

class DIDDocument(BaseModel):
    """Complete DID Document structure with metadata"""
    name: str = Field(..., description="DID name/identifier")
    value: str = Field(..., description="Raw hex-encoded DID document value")
    validity: str = Field(..., description="Validity period of the DID")
    created: str = Field(..., description="Creation timestamp")
    document: DIDV2Document = Field(..., description="Parsed DID document structure")

    
class ReadDidResult(BaseModel):
    name: str = Field(..., description="DID name/identifier")
    value: str = Field(..., description="Raw hex-encoded DID document value")
    validity: str = Field(..., description="Validity period of the DID")
    created: str = Field(..., description="Creation timestamp")
    document: DIDV2Document = Field(..., description="Parsed DID document as dictionary")
    
    def __str__(self):
        """String representation for printing"""
        return self.model_dump_json(indent=2)

# DidWriteResult is now imported from base.py as a Union type alias
DidWriteResult = Union[SubstrateSendResult, EvmSendResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]

class GetDidError(Exception):
    """Raised when there is a failure to the function get item."""
    pass