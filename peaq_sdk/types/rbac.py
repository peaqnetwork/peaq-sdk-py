from enum import Enum
from dataclasses import dataclass


class RbacFunctionSignatures(str, Enum):
    ADD_ROLE = "addRole(bytes32,bytes)",
    
class RbacCallFunction(str, Enum):
    ADD_ROLE = 'add_role'
    GET_ROLE = 'peaqrbac_fetchRole'
    
@dataclass
class FetchResponseData:
    id: str
    name: str
    enabled: bool
    
class GetRbacError(Exception):
    """Raised when there is a failure to one of the RBAC get item functions."""