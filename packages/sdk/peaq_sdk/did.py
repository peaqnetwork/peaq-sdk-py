from typing import Optional, Union

from peaq_sdk.base import Base
from peaq_sdk.types.base import TxOptions, EvmSendResult, SubstrateSendResult, TxOptions, StatusCallback
from peaq_sdk.utils.utils import parse_options
from peaq_sdk.types.common import (
    ChainType,
    SDKMetadata,
    CallModule,
    PrecompileAddresses,
)
from peaq_sdk.types.did import (
    CreateDIDOptions,
    ReadDIDOptions,
    UpdateDIDOptions,
    RemoveDIDOptions,
    DidFunctionSignatures,
    DidCallFunction,
    ReadDidResult,
    VerificationMethodType,
    DidWriteResult,
    DIDV2Document,
    DIDDocument
)
from peaq_sdk.types.base import (
    BuiltEvmTransactionResult,
    BuiltCallTransactionResult
)
from peaq_sdk.utils import peaq_proto
from peaq_sdk.utils.utils import evm_to_address
from peaq_sdk.utils.crypto import (
    generate_evm_public_key_multibase,
    generate_ed25519_public_key_multibase,
    generate_sr25519_public_key_multibase
)

from substrateinterface.base import SubstrateInterface
from substrateinterface.utils.ss58 import ss58_decode
from web3 import Web3
from web3.types import TxParams
from eth_abi import encode
from google.protobuf.json_format import MessageToDict

class Did(Base):
    """
    Provides methods to interact with the peaq on-chain DID precompile (EVM)
    or pallet (Substrate). Supports add, get, update, and remove operations.
    """
    def __init__(self, api: Web3 | SubstrateInterface, metadata: SDKMetadata) -> None:
        """
        Initializes DID with a connected API instance and shared SDK metadata.

        Args:
            api (Web3 | SubstrateInterface): The blockchain API connection.
                which may be a Web3 (EVM) or SubstrateInterface (Substrate).
            metadata (SDKMetadata): Shared metadata, including chain type,
                and optional signer.
        """
        super().__init__(api, metadata)
        
    async def create(
        self, 
        options: CreateDIDOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> DidWriteResult:
        """
        Creates a new Decentralized Identifier (DID) on-chain with the specified options.

        - EVM: Constructs a transaction to the `addAttribute` DID precompile contract.
        - Substrate: Composes an `add_attribute` extrinsic to the peaqDid pallet.

        Args:
            options (CreateDIDOptions): DID creation options containing name, controller, 
                didAddress, verificationMethods, services, and signature.
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TxOptions for EVM transactions.

        Returns:
            DidWriteResult: A Union type that can be one of:
                - SubstrateSendResult: For signed Substrate transactions with txHash, unsubscribe, and finalize promise
                - EvmSendResult: For signed EVM transactions with txHash, unsubscribe, and receipt promise  
                - BuiltEvmTransactionResult: For unsigned EVM transactions with message and tx object
                - BuiltCallTransactionResult: For unsigned Substrate calls with message and extrinsic object

        Raises:
            TypeError: If no valid address can be determined.
        """
        ops = parse_options(CreateDIDOptions, options, caller="did.create()")
        
        # Extract options after type checking for proper parameters sent
        name = ops.name
        controller = ops.controller
        did_address = ops.did_address
        verification_methods = ops.verification_methods or []
        services = ops.services or []
        signature = ops.signature

        # Get the connected wallet/keypair address
        connected_address = getattr(self.metadata.pair, 'address', None) if self.metadata.pair else None
        if not connected_address and not controller:
            raise TypeError('No wallet/keypair connected. Please either provide a controller or connect a wallet/keypair.')

        # Use provided controller or default to connected address
        effective_controller = controller or connected_address
        
        # Use provided didAddress for ID generation, otherwise use effectiveController
        id_address = did_address or effective_controller

        # Build DID Document (protobuf) -> hex string
        did_document_hex = await self._generate_did_document(id_address, {
            'controller': effective_controller,
            'verification_methods': verification_methods,
            'services': services,
            'signature': signature
        })
        
        if self.metadata.chain_type is ChainType.EVM:
            return await self._create_evm(name, effective_controller, did_document_hex, status_callback, tx_options)
        else:
            return self._create_substrate(name, effective_controller, did_document_hex, status_callback)
            
            
            
    async def read(self, options: ReadDIDOptions) -> Optional[ReadDidResult]:
        """
        Reads (fetches) an on-chain DID identified by options.name. This method locates
        the DID document stored at `name` for the given user address.

        - EVM: Uses the EVM address (either from a local signer if present, or the
            passed `address` parameter). Because DID data is actually stored in the
            Substrate-based registry, an evm wallet must be converted to a substrate wallet to
            temporarily connect and query the Substrate chain.
        - Substrate: Queries the DID registry directly via the existing Substrate connection
            (`self.api`). The address defaults to the local keypair's SS58 address
            if none is explicitly provided.

        Args:
            options (ReadDIDOptions): Options containing name and optional address.

        Returns:
            Optional[ReadDidResult]:
                An object containing the DID name, on-chain value, validity, creation
                timestamp, and the deserialized DID document. Returns None if not found.

        Raises:
            TypeError:
                If no valid address can be determined (no local signer and no `address`).
        """
        ops = parse_options(ReadDIDOptions, options, caller="did.read()")
        name = ops.name
        address = ops.address
        
        # Switch statement to determine chain type
        if self.metadata.chain_type == ChainType.EVM:
            evm_address = address or getattr(self.metadata.pair, 'address', None) if self.metadata.pair else None
            if not evm_address:
                raise TypeError('Address is required. Please either set seed at instance creation or pass an address.')
            
            # Convert EVM address to Substrate address format
            owner_address = evm_to_address(evm_address)
            
            # Create temporary Substrate API connection
            temp_api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
            
            try:
                result = await self._read_from_substrate(name, owner_address, temp_api)
                if result and result.get('document'):
                    doc = result['document']
                    return ReadDidResult(
                        name=doc.name,
                        value=doc.value,
                        validity=doc.validity,
                        created=doc.created,
                        document=doc.document
                    )
                return None
            finally:
                # Clean up temporary connection if needed
                # temp_api doesn't have disconnect in Python SubstrateInterface
                pass
        
        # For Substrate chains, use direct API access
        api = self.api
        owner_address = address or getattr(self.metadata.pair, 'ss58_address', None) if self.metadata.pair else None
        if not owner_address:
            raise TypeError('Signer/address required')
        
        result = await self._read_from_substrate(name, owner_address, api)
        if result and result.get('document'):
            doc = result['document']
            return ReadDidResult(
                name=doc.name,
                value=doc.value,
                validity=doc.validity,
                created=doc.created,
                document=doc.document
            )
        return None


    async def update(
        self,
        options: UpdateDIDOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> DidWriteResult:
        """
        Updates an existing DID identified by options.name, completely overwriting 
        the entire DID document with new verification methods and services.
        
        - EVM: Constructs a transaction to the `updateAttribute` DID precompile contract.
        - Substrate: Composes an `update_attribute` extrinsic to the peaqDid pallet.
        
        Args:
            options (UpdateDIDOptions): Update options containing name, controller, 
                didAddress, verificationMethods, services, and signature.
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TxOptions for EVM transactions.

        Returns:
            DidWriteResult: A Union type that can be one of:
                - SubstrateSendResult: For signed Substrate transactions with txHash, unsubscribe, and finalize promise
                - EvmSendResult: For signed EVM transactions with txHash, unsubscribe, and receipt promise  
                - BuiltEvmTransactionResult: For unsigned EVM transactions with message and tx object
                - BuiltCallTransactionResult: For unsigned Substrate calls with message and extrinsic object

        Raises:
            TypeError: If no valid address can be determined.
        """
        ops = parse_options(UpdateDIDOptions, options, caller="did.update()")
        
        # Extract options after type checking
        name = ops.name
        controller = ops.controller
        did_address = ops.did_address
        verification_methods = ops.verification_methods or []
        services = ops.services or []
        signature = ops.signature

        # Get the connected wallet/keypair address
        connected_address = getattr(self.metadata.pair, 'address', None) if self.metadata.pair else None
        if not connected_address and not controller:
            raise TypeError('No wallet/keypair connected. Please either provide a controller or connect a wallet/keypair.')

        # Use provided controller or default to connected address
        effective_controller = controller or connected_address
        
        # Use provided didAddress for ID generation, otherwise use effectiveController
        id_address = did_address or effective_controller

        # Build DID Document (protobuf) -> hex string
        did_document_hex = self._generate_did_document(id_address, {
            'controller': effective_controller,
            'verification_methods': verification_methods,
            'services': services,
            'signature': signature
        })

        if self.metadata.chain_type == ChainType.EVM:
            return await self._update_evm(name, effective_controller, did_document_hex, status_callback, tx_options)
        else:
            return self._update_substrate(name, effective_controller, did_document_hex, status_callback)


    async def remove(
        self,
        options: RemoveDIDOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> DidWriteResult:
        """
        Removes an existing on-chain DID identified by options.name. Once removed,
        the DID data is no longer accessible via subsequent reads.
        
        - EVM: Constructs a transaction to the `removeAttribute` DID precompile contract.
        - Substrate: Composes an `remove_attribute` extrinsic to the peaqDid pallet.
        
        Args:
            options (RemoveDIDOptions): Remove options containing name and optional address.
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TxOptions for EVM transactions.

        Returns:
            DidWriteResult: A Union type that can be one of:
                - SubstrateSendResult: For signed Substrate transactions with txHash, unsubscribe, and finalize promise
                - EvmSendResult: For signed EVM transactions with txHash, unsubscribe, and receipt promise  
                - BuiltEvmTransactionResult: For unsigned EVM transactions with message and tx object
                - BuiltCallTransactionResult: For unsigned Substrate calls with message and extrinsic object
        """
        ops = parse_options(RemoveDIDOptions, options, caller="did.remove()")
        name = ops.name
        address = ops.address

        if self.metadata.chain_type == ChainType.EVM:
            return await self._remove_evm(name, getattr(self.metadata.pair, 'address', None) or address, status_callback, tx_options)
        else:
            return self._remove_substrate(name, getattr(self.metadata.pair, 'address', None) or address, status_callback)
    
    async def _create_evm(
        self, 
        name: str, 
        address: str, 
        did_hex: str, 
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> Union[EvmSendResult, BuiltEvmTransactionResult]:
        """
        Creates a DID on EVM by constructing a transaction to the addAttribute precompile.
        
        Args:
            name (str): The DID name
            address (str): The address/controller
            did_hex (str): The hex-encoded DID document
            status_callback: Optional callback for transaction status
            tx_options: Optional transaction options
            
        Returns:
            Union[EvmSendResult, BuiltEvmTransactionResult]: 
                - EvmSendResult: For signed transactions with tx_hash, unsubscribe, and receipt promise
                - BuiltEvmTransactionResult: For unsigned transactions with message and tx object
        """
        did_function_selector = self.api.keccak(text=DidFunctionSignatures.ADD_ATTRIBUTE.value)[:4].hex()
        name_encoded = name.encode("utf-8").hex()
        did_encoded = did_hex.encode("utf-8").hex()
        encoded_params = encode(
            ['address', 'bytes', 'bytes', 'uint32'],
            [address, bytes.fromhex(name_encoded), bytes.fromhex(did_encoded), 0]
        ).hex()
        
        tx: TxParams = {
            "to": PrecompileAddresses.DID.value,
            "data": f"0x{did_function_selector}{encoded_params}"
        }
        
        return await self._handle_evm_tx(tx, f"create DID {name} for {address}", status_callback, tx_options)

    def _create_substrate(
        self, 
        name: str, 
        address: str, 
        did_hex: str, 
        status_callback = None
    ) -> Union[SubstrateSendResult, BuiltCallTransactionResult]:
        """
        Creates a DID on Substrate by composing an add_attribute extrinsic.
        
        Args:
            name (str): The DID name
            address (str): The address/controller  
            did_hex (str): The hex-encoded DID document
            status_callback: Optional callback for transaction status
            
        Returns:
            Union[SubstrateSendResult, BuiltCallTransactionResult]:
                - SubstrateSendResult: For signed transactions with tx_hash, unsubscribe, and finalize promise
                - BuiltCallTransactionResult: For unsigned transactions with message and call object
        """
        call = self.api.compose_call(
            call_module=CallModule.PEAQ_DID.value,
            call_function=DidCallFunction.ADD_ATTRIBUTE.value,
            call_params={
                'did_account': address,
                'name': name,
                'value': did_hex,
                'valid_for': None
                }
        )
        
        return self._handle_substrate_tx(call, f"add DID {name}", status_callback)

    async def _read_from_substrate(self, name: str, owner_address: str, api) -> Optional[dict]:
        """
        Reads a DID from Substrate storage using the provided API.
        
        Args:
            name (str): The DID name
            owner_address (str): The owner's address
            api: The Substrate API instance
            
        Returns:
            Optional[dict]: Dictionary containing document info and proto_document, or None if not found
        """
        # Query storage
        name_encoded = "0x" + name.encode("utf-8").hex()
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            DidCallFunction.READ_ATTRIBUTE.value, [owner_address, name_encoded, block_hash]
        )
        
        # Check result
        if resp['result'] is None:
            return None

        read_name = bytes.fromhex(resp['result']['name'][2:]).decode('utf-8')
        value = bytes.fromhex(resp['result']['value'][2:]).decode('utf-8')
        to_deserialize = bytes.fromhex(value)
        proto_document = self._deserialize_did(to_deserialize)
        
        # Convert protobuf document to structured format using helper
        proto_dict = self._proto_to_v2(proto_document)
        
        # Create the DIDDocument structure
        did_document = DIDDocument(
            name=read_name,
            value=value,
            validity=str(resp['result']['validity']),
            created=str(resp['result']['created']),
            document=DIDV2Document(**proto_dict)
        )
        
        return {
            'name': read_name,
            'raw_value': value,
            'validity': str(resp['result']['validity']),
            'created': str(resp['result']['created']),
            'document': did_document,
            'proto_document': proto_document
        }

    async def _update_evm(
        self, 
        name: str, 
        address: str, 
        did_hex: str, 
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> Union[EvmSendResult, BuiltEvmTransactionResult]:
        """
        Updates a DID on EVM by constructing a transaction to the updateAttribute precompile.
        
        Args:
            name (str): The DID name
            address (str): The address/controller
            did_hex (str): The hex-encoded DID document
            status_callback: Optional callback for transaction status
            tx_options: Optional transaction options

        Returns:
            Union[EvmSendResult, BuiltEvmTransactionResult]: 
                - EvmSendResult: For signed transactions with tx_hash, unsubscribe, and receipt promise
                - BuiltEvmTransactionResult: For unsigned transactions with message and tx object
        """
        did_function_selector = self.api.keccak(text=DidFunctionSignatures.UPDATE_ATTRIBUTE.value)[:4].hex()
        name_encoded = name.encode("utf-8").hex()
        did_encoded = did_hex.encode("utf-8").hex()
        encoded_params = encode(
            ['address', 'bytes', 'bytes', 'uint32'],
        [address, bytes.fromhex(name_encoded), bytes.fromhex(did_encoded), 0]
        ).hex()
            
        tx: TxParams = {
            "to": PrecompileAddresses.DID.value,
            "data": f"0x{did_function_selector}{encoded_params}"
        }
        
        return await self._handle_evm_tx(tx, f"update DID {name}", status_callback, tx_options)
                
    def _update_substrate(
        self, 
        name: str, 
        address: str, 
        did_hex: str, 
        status_callback = None
    ) -> Union[SubstrateSendResult, BuiltCallTransactionResult]:
        """
        Updates a DID on Substrate by composing an update_attribute extrinsic.
        
        Args:
            name (str): The DID name
            address (str): The address/controller  
            did_hex (str): The hex-encoded DID document
            status_callback: Optional callback for transaction status
            
        Returns:
            Union[SubstrateSendResult, BuiltCallTransactionResult]:
                - SubstrateSendResult: For signed transactions with tx_hash, unsubscribe, and finalize promise
                - BuiltCallTransactionResult: For unsigned transactions with message and call object
        """
        call = self.api.compose_call(
            call_module=CallModule.PEAQ_DID.value,
            call_function=DidCallFunction.UPDATE_ATTRIBUTE.value,
            call_params={
            'did_account': address,
                'name': name,
            'value': did_hex,
                'valid_for': None
                }
        )
            
        return self._handle_substrate_tx(call, f"update DID {name}", status_callback)

    async def _remove_evm(
        self, 
        name: str, 
        address: str, 
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> Union[EvmSendResult, BuiltEvmTransactionResult]:
        """
        Removes a DID on EVM by constructing a transaction to the removeAttribute precompile.
        
        Args:
            name (str): The DID name
            address (str): The address/controller
            status_callback: Optional callback for transaction status
            tx_options: Optional transaction options

        Returns:
            Union[EvmSendResult, BuiltEvmTransactionResult]: 
                - EvmSendResult: For signed transactions with tx_hash, unsubscribe, and receipt promise
                - BuiltEvmTransactionResult: For unsigned transactions with message and tx object
        """
        did_function_selector = self.api.keccak(text=DidFunctionSignatures.REMOVE_ATTRIBUTE.value)[:4].hex()
        name_encoded = name.encode("utf-8").hex()
        encoded_params = encode(
            ['address', 'bytes'],
        [address, bytes.fromhex(name_encoded)]
        ).hex()
            
        tx: TxParams = {
            "to": PrecompileAddresses.DID.value,
            "data": f"0x{did_function_selector}{encoded_params}"
        }
            
        return await self._handle_evm_tx(tx, f"remove DID {name}", status_callback, tx_options)
                
    def _remove_substrate(
        self, 
        name: str, 
        address: str, 
        status_callback = None
    ) -> Union[SubstrateSendResult, BuiltCallTransactionResult]:
        """
        Removes a DID on Substrate by composing a remove_attribute extrinsic.
        
        Args:
            name (str): The DID name
            address (str): The address/controller  
            status_callback: Optional callback for transaction status
            
        Returns:
            Union[SubstrateSendResult, BuiltCallTransactionResult]:
                - SubstrateSendResult: For signed transactions with tx_hash, unsubscribe, and finalize promise
                - BuiltCallTransactionResult: For unsigned transactions with message and call object
        """
        call = self.api.compose_call(
            call_module=CallModule.PEAQ_DID.value,
            call_function=DidCallFunction.REMOVE_ATTRIBUTE.value,
            call_params={
            'did_account': address,
                'name': name
                }
        )
        
        return self._handle_substrate_tx(call, f"remove DID {name}", status_callback)

    # ---------------  Generalized handlers ----------------
    async def _handle_evm_tx(
        self, 
        tx: TxParams, 
        action: str, 
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> Union[EvmSendResult, BuiltEvmTransactionResult]:
        """
        Generalized handler for EVM transactions, similar to TypeScript _handleEvmTx.
        
        Args:
            tx (TxParams): The transaction parameters
            action (str): Description of the action being performed
            status_callback: Optional callback for transaction status
            tx_options: Optional transaction options
            
        Returns:
            Union[EvmSendResult, BuiltEvmTransactionResult]: 
                - EvmSendResult: For signed transactions with tx_hash, unsubscribe, and receipt promise
                - BuiltEvmTransactionResult: For unsigned transactions with message and tx object
        """
        if not self.metadata.pair:
            return BuiltEvmTransactionResult(
                message=f"Constructed {action} tx (unsigned).",
                tx=tx
            )
        try:
            # The _send_evm_tx method already handles EVM status updates properly
            return await self._send_evm_tx(tx, on_status=status_callback, opts=tx_options)
        except Exception as err:
            # Throw error instead of returning signable extrinsic
            raise Exception(f"Failed to {action}: {str(err)}")

    def _handle_substrate_tx(
        self, 
        call, 
        action: str, 
        status_callback = None
    ) -> Union[SubstrateSendResult, BuiltCallTransactionResult]:
        """
        Generalized handler for Substrate transactions, similar to TypeScript _handleSubstrateTx.
        
        Args:
            call: The Substrate call object
            action (str): Description of the action being performed
            status_callback: Optional callback for transaction status
            
        Returns:
            Union[SubstrateSendResult, BuiltCallTransactionResult]:
                - SubstrateSendResult: For signed transactions with tx_hash, unsubscribe, and finalize promise
                - BuiltCallTransactionResult: For unsigned transactions with message and call object
        """
        if not self.metadata.pair:
            return BuiltCallTransactionResult(
                message=f"Constructed {action} call (unsigned).",
                call=call
            )
        try:
            # Now both methods accept the unified TransactionStatusCallback type
            return self._send_substrate_call_structured(call, on_status=status_callback)
        except Exception as err:
            # Throw error instead of returning signable extrinsic
            raise Exception(f"Failed to {action}: {str(err)}")
    
    async def _generate_did_document(self, id_address: str, extra: dict) -> str:
        """
        Constructs and serializes a DID document in Protobuf format based on the
        provided `id_address` and extra fields. The result is returned as
        a hex-encoded string.

        This document includes:
        - `id` field set to `"did:peaq:{id_address}"`.
        - `controller` field set to `"did:peaq:{controller}"`.
        - Verification methods (and authentications) if present in `extra['verification_methods']`.
        - A signature if `extra['signature']` is set.
        - One or more services if `extra['services']` is provided.

        Args:
            id_address (str): The address used for the DID ID.
            extra (dict): Dictionary containing:
                - controller (str): The controller address
                - verification_methods (List[Verification]): Verification methods
                - services (List[Service]): Services 
                - signature (Optional[Signature]): Document signature

        Returns:
            str: A hex-encoded Protobuf serialization of the DID document.

        Raises:
            ValueError: If a verification type or signature type is invalid for the
                current chain type (checked inside helper methods).
        """
        # Create new Doc and set id & controller
        doc = peaq_proto.Document()
        doc.id = f"did:peaq:{id_address}"
        doc.controller = f"did:peaq:{extra['controller']}"
        
        # Add verification methods
        verification_methods = extra.get('verification_methods', [])
        for idx, vm in enumerate(verification_methods):
            method = peaq_proto.VerificationMethod()
            method.id = vm.id or f"did:peaq:{id_address}#keys-{idx + 1}"
            method.type = vm.type.value
            method.controller = vm.controller or f"did:peaq:{extra['controller']}"
            
            # user can manually set the multibase if they would like
            if vm.public_key_multibase:
                method.public_key_multibase = vm.public_key_multibase
            elif self.metadata.chain_type == ChainType.EVM:
                # For EVM chains, use EIP-155 format: eip155:chain_id:address
                chain_id = await self.get_chain_id()  
                method.public_key_multibase = f"eip155:{chain_id}:{extra['controller']}"
            else:
                # For other chains, use the traditional multibase generation
                method.public_key_multibase = self._generate_multibase(extra['controller'], vm.type)
            
            doc.verification_methods.append(method)
            doc.authentications.append(method.id)
        
        # Add services
        services = extra.get('services', [])
        for srv in services:
            s = peaq_proto.Services()
            s.id = srv.id
            s.type = srv.type
            
            # At least one of serviceEndpoint or data should be provided
            if srv.service_endpoint:
                s.service_endpoint = srv.service_endpoint
            if srv.data:
                s.data = srv.data
            
            # Validate that at least one field is set
            if not srv.service_endpoint and not srv.data:
                raise ValueError(f"Service {srv.id} must have either serviceEndpoint or data")
            
            doc.services.append(s)
        
        # Add signature if provided
        signature = extra.get('signature')
        if signature:
            sig = peaq_proto.Signature()
            sig.type = signature.type.value
            sig.issuer = signature.issuer
            sig.hash = signature.hash
            doc.signature.CopyFrom(sig)
        
        serialized_data = doc.SerializeToString()
        serialized_hex = serialized_data.hex()
        return serialized_hex
    
    async def get_chain_id(self) -> int:
        """
        Get the chain ID for EVM networks.
        Uses the cached chain ID from the base class.
            
        Returns:
            int: The chain ID
        """
        return await super().get_chain_id()

    def _generate_multibase(self, address: str, verification_type: str) -> str:
        """
        Generates the appropriate publicKeyMultibase based on verification type and chain.
        Similar to the TypeScript implementation.
        
        Args:
            address (str): The address (EVM or SS58)
            verification_type (str): The verification method type
            
        Returns:
            str: Generated publicKeyMultibase
            
        Raises:
            ValueError: If verification type is unsupported or required signer is missing
        """
        if verification_type == VerificationMethodType.ECDSA:
            if self.metadata.chain_type != ChainType.EVM:
                raise ValueError('EcdsaSecp256k1RecoveryMethod2020 is only supported on EVM chains')
            
            # Note: EVM case should be handled in _generate_did_document using EIP-155 format
            # This fallback attempts to generate from signing key if available
            if self.metadata.pair and hasattr(self.metadata.pair, '_key_obj'):
                return generate_evm_public_key_multibase(self.metadata.pair)
            # If no signing key, return empty string (caller should handle EIP-155 format)
            return ''
            
        elif verification_type == VerificationMethodType.ED25519:
            if self.metadata.chain_type != ChainType.SUBSTRATE:
                raise ValueError('Ed25519VerificationKey2020 is only supported on Substrate chains')
            return generate_ed25519_public_key_multibase(address)
            
        elif verification_type == VerificationMethodType.SR25519:
            if self.metadata.chain_type != ChainType.SUBSTRATE:
                raise ValueError('Sr25519VerificationKey2020 is only supported on Substrate chains')
            return generate_sr25519_public_key_multibase(address)
        else:
            raise ValueError(f"Unsupported DID verification method type: {verification_type}")
    
    def _deserialize_did(self, data):
        """
        Parses a Protobuf-serialized DID document from the given raw `data` bytes.

        Args:
            data (bytes): The raw Protobuf-encoded DID document.

        Returns:
            peaq_proto.Document: The deserialized DID document.
        """
        deserialized_doc = peaq_proto.Document()
        deserialized_doc.ParseFromString(data)
        return deserialized_doc
    
    def _proto_to_v2(self, doc) -> dict:
        """
        Converts a protobuf DID document to a structured dictionary format.
        Similar to the TypeScript _protoToV2 method.
        
        Args:
            doc: The protobuf DID document
            
        Returns:
            dict: Structured dictionary representation of the DID document
        """
        return {
            'id': doc.id,
            'controller': doc.controller,
            'verificationMethod': [
                {
                    'id': m.id,
                    'type': m.type,
                    'controller': m.controller,
                    'publicKeyMultibase': m.public_key_multibase
                } for m in (doc.verification_methods or [])
            ],
            'authentication': list(doc.authentications),
            'service': [
                {
                    'id': s.id,
                    'type': s.type,
                    'serviceEndpoint': s.service_endpoint if hasattr(s, 'service_endpoint') else None,
                    'data': s.data if hasattr(s, 'data') else None
                } for s in (doc.services or [])
            ],
            'signature': {
                'type': doc.signature.type,
                'issuer': doc.signature.issuer,
                'hash': doc.signature.hash
            } if doc.HasField('signature') else None
        }