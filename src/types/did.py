"""objects used in the main sdk initializer"""
# python native imports
from dataclasses import dataclass, field
from typing import List, Optional

from src.types.common import TransactionResult

@dataclass
class Verification:
    type: str
    controller: Optional[str] = None
    publicKeyMultibase: Optional[str] = None

@dataclass
class Signature:
    type: str
    issuer: str
    hash: str

@dataclass
class Service:
    id: str
    type: str
    serviceEndpoint: Optional[str] = None
    data: Optional[str] = None

@dataclass
class CustomDocumentFields:
    verifications: List[Verification] = field(default_factory=list)
    signature: Optional[Signature] = None
    services: List[Service] = field(default_factory=list)
    
@dataclass
class CreateDidResult:
    message: str
    receipt: TransactionResult