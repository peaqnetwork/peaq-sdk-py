from enum import Enum

class PayFunctionSignatures(str, Enum):
    TRANSFER_TO_ACCOUNT_ID = "transferToAccountId(bytes32,uint256)"
    ERC_721_SAFE_TRANSFER_FROM = "safeTransferFrom(address,address,uint256)"
    ERC_20_TRANSFER = "transfer(address,uint256)"
    
    
    # safeTransferFrom(address from, address to, uint256 tokenId)
    