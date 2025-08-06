from enum import Enum
from typing import Union, Optional
from decimal import Decimal
from pydantic import BaseModel, Field

class PayFunctionSignatures(str, Enum):
    TRANSFER_TO_ACCOUNT_ID = "transferToAccountId(bytes32,uint256)"
    ERC_721_SAFE_TRANSFER_FROM = "safeTransferFrom(address,address,uint256)"
    ERC_20_TRANSFER = "transfer(address,uint256)"
    
    
    # safeTransferFrom(address from, address to, uint256 tokenId)

# Options classes for transfer operations
class NativeTransferOptions(BaseModel):
    """Options for native token transfer"""
    to: str = Field(..., description="Recipient address (SS58 or EVM H160)")
    amount: Union[int, float, str, Decimal] = Field(..., description="Human-readable token amount (e.g., 1.5)")

class ERC20TransferOptions(BaseModel):
    """Options for ERC-20 token transfer"""
    erc_20_address: str = Field(..., description="ERC-20 contract address")
    recipient_address: str = Field(..., description="Recipient address")
    amount: Union[int, float, str, Decimal] = Field(..., description="Human-readable token amount")
    token_decimals: Optional[Union[int, float, str, Decimal]] = Field(None, description="Token decimals (defaults to 18)")

class ERC721TransferOptions(BaseModel):
    """Options for ERC-721 token transfer"""
    erc_721_address: str = Field(..., description="ERC-721 contract address")
    recipient_address: str = Field(..., description="Recipient address")
    token_id: int = Field(..., description="Token ID to transfer")
    