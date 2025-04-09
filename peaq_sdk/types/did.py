"""objects used in the main sdk initializer"""
# python native imports

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

@dataclass
class Verification:
    type: str
    controller: Optional[str] = None
    public_key_multibase: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.type, str):
            raise TypeError(f"Verification.type must be str, got {type(self.type).__name__}")
    # add more checks here if needed
    
    # when should the user be able to set controller/publicKeyMultibase themselves?

@dataclass
class Signature:
    type: str
    issuer: str
    hash: str

    def __post_init__(self):
        if not all(isinstance(attr, str) for attr in (self.type, self.issuer, self.hash)):
            raise TypeError("Signature fields type, issuer, hash must all be str")

@dataclass
class Service:
    id: str
    type: str
    service_endpoint: Optional[str] = None
    data: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.id, str) or not isinstance(self.type, str):
            raise TypeError("Service.id and Service.type must be str")
        if self.service_endpoint is not None and not isinstance(self.service_endpoint, str):
            raise TypeError("Service.serviceEndpoint must be str or None")
        if self.data is not None and not isinstance(self.data, str):
            raise TypeError("Service.data must be str or None")

@dataclass
class CustomDocumentFields:
    verifications: List[Verification] = field(default_factory=list)
    signature: Optional[Signature] = None
    services: List[Service] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.verifications, list):
            raise TypeError("verifications must be a Verification[]]")
        for v in self.verifications:
            if not isinstance(v, Verification):
                raise TypeError(f"Expected Verification, got {type(v).__name__}")
        if self.signature is not None and not isinstance(self.signature, Signature):
            raise TypeError(f"Expected Signature or None, got {type(self.signature).__name__}")
        if not isinstance(self.services, list):
            raise TypeError("services must be a Service[]")
        for s in self.services:
            if not isinstance(s, Service):
                raise TypeError(f"Expected Service, got {type(s).__name__}")

# Used for Storage EVM precompiles
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
    
@dataclass
class ReadDidResult:
    name: str
    value: str
    validity: str
    created: str
    document: dict
    
class GetDidError(Exception):
    """Raised when there is a failure to the function get item."""
    pass