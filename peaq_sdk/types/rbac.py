from enum import Enum
from dataclasses import dataclass
from typing import List


class RbacFunctionSignatures(str, Enum):
    ADD_ROLE = "addRole(bytes32,bytes)"
    ADD_GROUP = "addGroup(bytes32,bytes)"
    ADD_PERMISSION = "addPermission(bytes32,bytes)"
    ASSIGN_PERMISSION_TO_ROLE = "assignPermissionToRole(bytes32,bytes32)"
    UNASSIGN_PERMISSION_TO_ROLE = "unassignPermissionToRole(bytes32,bytes32)"
    ASSIGN_ROLE_TO_GROUP = "assignRoleToGroup(bytes32,bytes32)"
    UNASSIGN_ROLE_TO_GROUP = "unassignRoleToGroup(bytes32,bytes32)"
    ASSIGN_ROLE_TO_USER = "assignRoleToUser(bytes32,bytes32)"
    UNASSIGN_ROLE_TO_USER = "unassignRoleToUser(bytes32,bytes32)"
    ASSIGN_USER_TO_GROUP = "assignUserToGroup(bytes32,bytes32)"
    UNASSIGN_USER_TO_GROUP = "unassignUserToGroup(bytes32,bytes32)"
    DISABLE_GROUP = "disableGroup(bytes32)"
    DISABLE_PERMISSION = "disablePermission(bytes32)"
    DISABLE_ROLE = "disableRole(bytes32)"
    UPDATE_GROUP = "updateGroup(bytes32,bytes)"
    UPDATE_PERMISSION = "updatePermission(bytes32,bytes)"
    UPDATE_ROLE = "updateRole(bytes32,bytes)"
    
class RbacCallFunction(str, Enum):
    ADD_ROLE = 'add_role'
    ADD_GROUP = 'add_group'
    ADD_PERMISSION = 'add_permission'
    ASSIGN_PERMISSION_TO_ROLE = 'assign_permission_to_role'
    UNASSIGN_PERMISSION_TO_ROLE = 'unassign_permission_to_role'
    ASSIGN_ROLE_TO_GROUP = 'assign_role_to_group'
    UNASSIGN_ROLE_TO_GROUP = 'unassign_role_to_group'
    ASSIGN_ROLE_TO_USER = 'assign_role_to_user'
    UNASSIGN_ROLE_TO_USER = 'unassign_role_to_user'
    ASSIGN_USER_TO_GROUP = 'assign_user_to_group'
    UNASSIGN_USER_TO_GROUP = 'unassign_user_to_group'
    DISABLE_GROUP = 'disable_group'
    DISABLE_PERMISSION = 'disable_permission'
    DISABLE_ROLE = 'disable_role'
    UPDATE_GROUP = 'update_group'
    UPDATE_PERMISSION = 'update_permission'
    UPDATE_ROLE = 'update_role'
    GET_ROLE = 'peaqrbac_fetchRole'
    GET_GROUP = 'peaqrbac_fetchGroup'
    GET_PERMISSION = 'peaqrbac_fetchPermission'
    GET_ROLES = 'peaqrbac_fetchRoles'
    GET_GROUPS = 'peaqrbac_fetchGroups'
    GET_PERMISSIONS = 'peaqrbac_fetchPermissions'
    GET_USER_GROUPS = 'peaqrbac_fetchUserGroups'
    GET_USER_ROLES = 'peaqrbac_fetchUserRoles'
    GET_USER_PERMISSIONS = 'peaqrbac_fetchUserPermissions'
    GET_ROLE_PERMISSIONS = 'peaqrbac_fetchRolePermissions'
    GET_GROUP_ROLES = 'peaqrbac_fetchGroupRoles'
    GET_GROUP_PERMISSIONS = 'peaqrbac_fetchGroupPermissions'
    
@dataclass
class FetchResponseData:
    id: str
    name: str
    enabled: bool

@dataclass
class FetchResponseRole2Permission:
    permission: str
    role: str

@dataclass
class FetchResponseRole2Group:
    role: str
    group: str

@dataclass
class FetchResponseRole2User:
    role: str
    user: str

@dataclass
class ResponseFetchUserGroups:
    user: str
    group: str
    
class GetRbacError(Exception):
    """Raised when there is a failure to one of the RBAC get item functions."""