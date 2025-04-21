from enum import Enum


class RbacFunctionSignatures(str, Enum):
    ADD_ROLE = "addRole(bytes32,bytes)",
    
class RbacCallFunction(str, Enum):
    ADD_ROLE = 'add_role'