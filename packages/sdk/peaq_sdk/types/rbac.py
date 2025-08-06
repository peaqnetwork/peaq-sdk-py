from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


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
    
class FetchResponseData(BaseModel):
    """Response data for RBAC fetch operations (roles, groups, permissions)"""
    id: str = Field(..., description="Unique identifier for the entity")
    name: str = Field(..., description="Human-readable name of the entity")
    enabled: bool = Field(..., description="Whether the entity is currently enabled")

class FetchResponseRole2Permission(BaseModel):
    """Response data for role-to-permission relationship queries"""
    permission: str = Field(..., description="Permission identifier")
    role: str = Field(..., description="Role identifier")

class FetchResponseRole2Group(BaseModel):
    """Response data for role-to-group relationship queries"""
    role: str = Field(..., description="Role identifier")
    group: str = Field(..., description="Group identifier")

class FetchResponseRole2User(BaseModel):
    """Response data for role-to-user relationship queries"""
    role: str = Field(..., description="Role identifier")
    user: str = Field(..., description="User identifier")

class ResponseFetchUserGroups(BaseModel):
    """Response data for user-to-group relationship queries"""
    user: str = Field(..., description="User identifier")
    group: str = Field(..., description="Group identifier")
    
# Options classes for RBAC operations
class CreateRoleOptions(BaseModel):
    """Options for creating a role"""
    role_name: str = Field(..., description="Name of the role to create")
    role_id: Optional[str] = Field(None, description="Optional role ID (32 chars max)")

class CreateGroupOptions(BaseModel):
    """Options for creating a group"""
    group_name: str = Field(..., description="Name of the group to create")
    group_id: Optional[str] = Field(None, description="Optional group ID (32 chars max)")

class CreatePermissionOptions(BaseModel):
    """Options for creating a permission"""
    permission_name: str = Field(..., description="Name of the permission to create")
    permission_id: Optional[str] = Field(None, description="Optional permission ID (32 chars max)")

class AssignPermissionToRoleOptions(BaseModel):
    """Options for assigning a permission to a role"""
    permission_id: str = Field(..., description="Permission ID (32 chars)")
    role_id: str = Field(..., description="Role ID (32 chars)")

class AssignRoleToGroupOptions(BaseModel):
    """Options for assigning a role to a group"""
    role_id: str = Field(..., description="Role ID (32 chars)")
    group_id: str = Field(..., description="Group ID (32 chars)")

class AssignRoleToUserOptions(BaseModel):
    """Options for assigning a role to a user"""
    role_id: str = Field(..., description="Role ID (32 chars)")
    user_id: str = Field(..., description="User ID (32 chars)")

class AssignUserToGroupOptions(BaseModel):
    """Options for assigning a user to a group"""
    user_id: str = Field(..., description="User ID (32 chars)")
    group_id: str = Field(..., description="Group ID (32 chars)")

class DisableRoleOptions(BaseModel):
    """Options for disabling a role"""
    role_id: str = Field(..., description="Role ID (32 chars)")

class DisableGroupOptions(BaseModel):
    """Options for disabling a group"""
    group_id: str = Field(..., description="Group ID (32 chars)")

class DisablePermissionOptions(BaseModel):
    """Options for disabling a permission"""
    permission_id: str = Field(..., description="Permission ID (32 chars)")

class UpdateRoleOptions(BaseModel):
    """Options for updating a role"""
    role_id: str = Field(..., description="Role ID (32 chars)")
    role_name: str = Field(..., description="New name for the role")

class UpdateGroupOptions(BaseModel):
    """Options for updating a group"""
    group_id: str = Field(..., description="Group ID (32 chars)")
    group_name: str = Field(..., description="New name for the group")

class UpdatePermissionOptions(BaseModel):
    """Options for updating a permission"""
    permission_id: str = Field(..., description="Permission ID (32 chars)")
    permission_name: str = Field(..., description="New name for the permission")

class UnassignPermissionToRoleOptions(BaseModel):
    """Options for unassigning a permission from a role"""
    permission_id: str = Field(..., description="Permission ID (32 chars)")
    role_id: str = Field(..., description="Role ID (32 chars)")

class UnassignRoleToGroupOptions(BaseModel):
    """Options for unassigning a role from a group"""
    role_id: str = Field(..., description="Role ID (32 chars)")
    group_id: str = Field(..., description="Group ID (32 chars)")

class UnassignRoleToUserOptions(BaseModel):
    """Options for unassigning a role from a user"""
    role_id: str = Field(..., description="Role ID (32 chars)")
    user_id: str = Field(..., description="User ID (32 chars)")

class UnassignUserToGroupOptions(BaseModel):
    """Options for unassigning a user from a group"""
    user_id: str = Field(..., description="User ID (32 chars)")
    group_id: str = Field(..., description="Group ID (32 chars)")

# Fetch options classes
class FetchRoleOptions(BaseModel):
    """Options for fetching a role"""
    owner: str = Field(..., description="Owner address")
    role_id: str = Field(..., description="Role ID (32 chars)")

class FetchGroupOptions(BaseModel):
    """Options for fetching a group"""
    owner: str = Field(..., description="Owner address")
    group_id: str = Field(..., description="Group ID (32 chars)")

class FetchPermissionOptions(BaseModel):
    """Options for fetching a permission"""
    owner: str = Field(..., description="Owner address")
    permission_id: str = Field(..., description="Permission ID (32 chars)")

class FetchRolesOptions(BaseModel):
    """Options for fetching all roles"""
    owner: str = Field(..., description="Owner address")

class FetchGroupsOptions(BaseModel):
    """Options for fetching all groups"""
    owner: str = Field(..., description="Owner address")

class FetchPermissionsOptions(BaseModel):
    """Options for fetching all permissions"""
    owner: str = Field(..., description="Owner address")

class FetchUserRolesOptions(BaseModel):
    """Options for fetching user roles"""
    owner: str = Field(..., description="Owner address")
    user_id: str = Field(..., description="User ID (32 chars)")

class FetchGroupRolesOptions(BaseModel):
    """Options for fetching group roles"""
    owner: str = Field(..., description="Owner address")
    group_id: str = Field(..., description="Group ID (32 chars)")

class FetchUserGroupsOptions(BaseModel):
    """Options for fetching user groups"""
    owner: str = Field(..., description="Owner address")
    user_id: str = Field(..., description="User ID (32 chars)")

class FetchRolePermissionsOptions(BaseModel):
    """Options for fetching role permissions"""
    owner: str = Field(..., description="Owner address")
    role_id: str = Field(..., description="Role ID (32 chars)")

class FetchUserPermissionsOptions(BaseModel):
    """Options for fetching user permissions"""
    owner: str = Field(..., description="Owner address")
    user_id: str = Field(..., description="User ID (32 chars)")

class FetchGroupPermissionsOptions(BaseModel):
    """Options for fetching group permissions"""
    owner: str = Field(..., description="Owner address")
    group_id: str = Field(..., description="Group ID (32 chars)")

class GetRbacError(Exception):
    """Raised when there is a failure to one of the RBAC get item functions."""