from typing import Optional, Union

from peaq_sdk.base import Base
from peaq_sdk.types.base import TxOptions, EvmSendResult, SubstrateSendResult
from peaq_sdk.utils.utils import parse_options
from peaq_sdk.types.common import (
    ChainType,
    SDKMetadata,
    CallModule,
    PrecompileAddresses,
    BaseUrlError
)
from peaq_sdk.types.did import (
    CreateDIDOptions,
    CustomDocumentFields, 
    DidFunctionSignatures,
    DidCallFunction,
    ReadDidResult,
    GetDidError,
    VerificationMethodType,
    StatusCallback,
    TxOptions,
    DidWriteResult
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
        tx_options: TxOptions = None
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
        did_document_hex = self._generate_did_document(id_address, {
            'controller': effective_controller,
            'verification_methods': verification_methods,
            'services': services,
            'signature': signature
        })
        
        if self.metadata.chain_type is ChainType.EVM:
            return await self._create_evm(name, effective_controller, did_document_hex, status_callback, tx_options)
        else:
            return self._create_substrate(name, effective_controller, did_document_hex, status_callback)
            
            
            
    def read(self, name: str, address: Optional[str] = None) -> ReadDidResult:
        """
        Reads (fetches) an on-chain DID identified by `name`. This method locates
        the DID document stored at `name` for the given user address.

        - EVM: Uses the EVM address (either from a local signer if present, or the
            passed `address` parameter). Because DID data is actually stored in the
            Substrate-based registry, an evm wallet must be converted to a substrate wallet to
            temporarily connect and query the Substrate chain.
        - Substrate: Queries the DID registry directly via the existing Substrate connection
            (`self.api`). The address defaults to the local keypair's SS58 address
            if none is explicitly provided.

        Args:
            name (str): The DID name or label under which the document is stored.
            address (Optional[str]): The address owning the DID. On EVM, this should
                be a H160 address; on Substrate, an SS58 address. If not provided,
                falls back to the local signer's address (if any).


        Returns:
            ReadDidResult:
                An object containing the DID name, on-chain value, validity, creation
                timestamp, and the deserialized DID document.

        Raises:
            TypeError:
                If no valid address can be determined (no local signer and no `address`).
            GetDidError:
                If the DID specified by `name` does not exist on-chain for `address`.
        """
        
        if self.metadata.chain_type is ChainType.EVM:
            evm_address = (
                getattr(self.metadata.pair, 'address', address)
                if self.metadata.pair
                else address
            )
            if not evm_address:
                raise TypeError(f"Address is set to {evm_address}. Please either set seed at instance creation or pass an address.")
            owner_address = evm_to_address(evm_address)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
            display_address = evm_address
        else:
            owner_address = (
                getattr(self.metadata.pair, 'ss58_address', address)
                if self.metadata.pair
                else address
            )
            if not owner_address:
                raise TypeError(f"Address is set to {owner_address}. Please either set seed at instance creation or pass an address.")
            api = self.api
            display_address = owner_address
        
        # Query storage
        name_encoded = "0x" + name.encode("utf-8").hex()
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            DidCallFunction.READ_ATTRIBUTE.value, [owner_address, name_encoded, block_hash]
        )
        # Check result
        if resp['result'] is None:
            raise GetDidError(f"DID of name {name} was not found at address {display_address}.")

        read_name = bytes.fromhex(resp['result']['name'][2:]).decode('utf-8')
        value = bytes.fromhex(resp['result']['value'][2:]).decode('utf-8')
        to_deserialize = bytes.fromhex(value)
        document = self._deserialize_did(to_deserialize)
        
        return ReadDidResult(
            name=read_name,
            value=value,
            validity=str(resp['result']['validity']),
            created=str(resp['result']['created']),
            document=MessageToDict(document)
        )


    def update(
        self, 
        name: str, 
        custom_document_fields: CustomDocumentFields, 
        address: Optional[str] = None,
        status_callback = None,
        tx_options = None
    ) -> DidWriteResult:
        """
        Updates an existing DID identified by `name`, overwriting the entire DID
        document with new `custom_document_fields`. Use caution, as all existing
        data is replaced with the newly provided fields.
        
        - EVM: Constructs a transaction to the `updateAttribute` DID precompile contract.
        - Substrate: Composes an `update_attribute` extrinsic to the peaqDid
            pallet.
        
        Args:
            name (str): The unique DID name or label to update.
            custom_document_fields (CustomDocumentFields): The new fields to
                embed in the DID document. These fully replace the prior document.
            address (Optional[str]): An optional address if no local keypair is present.
                On EVM, this should be an H160 address. On Substrate, a SS58 address.
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TxOptions for EVM transactions.

        Returns:
            DidWriteResult: A Union type that can be one of:
                - SubstrateSendResult: For signed Substrate transactions with txHash, unsubscribe, and finalize promise
                - EvmSendResult: For signed EVM transactions with txHash, unsubscribe, and receipt promise  
                - BuiltEvmTransactionResult: For unsigned EVM transactions with message and tx object
                - BuiltCallTransactionResult: For unsigned Substrate calls with message and extrinsic object

        Raises:
            TypeError: If `custom_document_fields` is not an instance of `CustomDocumentFields`.
        """
        if not isinstance(custom_document_fields, CustomDocumentFields):
            raise TypeError(
                f"custom_document_fields object must be CustomDocumentFields, "
                f"got {type(custom_document_fields).__name__!r}"
            )
            
        user_address = self._resolve_address(address=address)
        
        serialized_did = self._generate_did_document(user_address, custom_document_fields)
        
        if self.metadata.chain_type is ChainType.EVM:
            serialized_did = self._generate_did_document(user_address, custom_document_fields)
            did_function_selector = self.api.keccak(text=DidFunctionSignatures.UPDATE_ATTRIBUTE.value)[:4].hex()
            name_encoded = name.encode("utf-8").hex()
            did_encoded = serialized_did.encode("utf-8").hex()
            
            encoded_params = encode(
                ['address', 'bytes', 'bytes', 'uint32'],
                [user_address, bytes.fromhex(name_encoded), bytes.fromhex(did_encoded), 0]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.DID.value,
                "data": f"0x{did_function_selector}{encoded_params}"
            }
            
            if self.metadata.pair:
                opts = tx_options if tx_options else TxOptions()
                return self._send_evm_tx_structured(tx, on_status=status_callback, opts=opts)
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed DID update transaction for {user_address} of the name {name}. You must sign and send it externally.",
                    tx=tx
                )
                
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_DID.value,
                call_function=DidCallFunction.UPDATE_ATTRIBUTE.value,
                call_params={
                    'did_account': user_address,
                    'name': name,
                    'value': serialized_did,
                    'valid_for': None
                    }
            )
            
            if self.metadata.pair:
                return self._send_substrate_call_structured(call, on_status=status_callback)
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed DID update call for {user_address} of the name {name}. You must sign and send externally.",
                    call=call
                )


    
    def remove(
        self, 
        name: str, 
        address: Optional[str] = None,
        status_callback = None,
        tx_options = None
    ) -> DidWriteResult:
        """
        Removes an existing on-chain DID identified by `name`. Once removed,
        the DID data is no longer accessible via subsequent reads.
        
        - EVM: Constructs a transaction to the `removeAttribute` DID precompile contract.
        - Substrate: Composes an `remove_attribute` extrinsic to the peaqDid
            pallet.
        
        Args:
            name (str): The DID name or alias to remove from the chain.
            address (Optional[str]): An optional address if no local keypair is present.
                On EVM, this should be an H160 address. On Substrate, a SS58 address.
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TxOptions for EVM transactions.

        Returns:
            DidWriteResult: A Union type that can be one of:
                - SubstrateSendResult: For signed Substrate transactions with txHash, unsubscribe, and finalize promise
                - EvmSendResult: For signed EVM transactions with txHash, unsubscribe, and receipt promise  
                - BuiltEvmTransactionResult: For unsigned EVM transactions with message and tx object
                - BuiltCallTransactionResult: For unsigned Substrate calls with message and extrinsic object
        """
        
        user_address = self._resolve_address(address=address)
        
        if self.metadata.chain_type is ChainType.EVM:
            did_function_selector = self.api.keccak(text=DidFunctionSignatures.REMOVE_ATTRIBUTE.value)[:4].hex()
            name_encoded = name.encode("utf-8").hex()
            encoded_params = encode(
                ['address', 'bytes'],
                [user_address, bytes.fromhex(name_encoded)]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.DID.value,
                "data": f"0x{did_function_selector}{encoded_params}"
            }
            
            if self.metadata.pair:
                opts = tx_options if tx_options else TxOptions()
                return self._send_evm_tx_structured(tx, on_status=status_callback, opts=opts)
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed DID remove transaction for {user_address} of the name {name}. You must sign and send it externally.",
                    tx=tx
                )
                
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_DID.value,
                call_function=DidCallFunction.REMOVE_ATTRIBUTE.value,
                call_params={
                    'did_account': user_address,
                    'name': name
                    }
            )
            
            if self.metadata.pair:
                return self._send_substrate_call_structured(call, on_status=status_callback)
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed DID remove call for {user_address} of the name {name}. You must sign and send externally.",
                    call=call
                )
    
    async def _create_evm(
        self, 
        name: str, 
        address: str, 
        did_hex: str, 
        status_callback = None, 
        tx_options = None
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
        
        if self.metadata.pair:
            opts = tx_options if tx_options else TxOptions()
            return await self._send_evm_tx(tx, on_status=status_callback, opts=opts)
        else:
            return BuiltEvmTransactionResult(
                message=f"Constructed DID create transaction for {address} of the name {name}. You must sign and send it externally.",
                tx=tx
            )

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
        
        if self.metadata.pair:
            return self._send_substrate_call_structured(call, on_status=status_callback)
        else:
            return BuiltCallTransactionResult(
                message=f"Constructed DID create call for {address} of the name {name}. You must sign and send externally.",
                call=call
            )
    
    def _generate_did_document(self, id_address: str, extra: dict) -> str:
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
            method.type = vm.type
            method.controller = vm.controller or f"did:peaq:{extra['controller']}"
            
            # user can manually set the multibase if they would like
            if vm.public_key_multibase:
                method.public_key_multibase = vm.public_key_multibase
            elif self.metadata.chain_type == ChainType.EVM:
                # For EVM chains, use EIP-155 format: eip155:chain_id:address
                chain_id = self.get_chain_id()
                method.public_key_multibase = f"eip155:{chain_id}:{extra['controller']}"
            else:
                # For other chains, use the traditional multibase generation
                method.public_key_multibase = self._generate_multibase(extra['controller'], vm.type)
            
            # TODO add assertionMethod, keyAgreement, capabilityInvocation, capabilityDelegation in v3
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
            sig.type = signature.type
            sig.issuer = signature.issuer
            sig.hash = signature.hash
            doc.signature.CopyFrom(sig)
        
        serialized_data = doc.SerializeToString()
        serialized_hex = serialized_data.hex()
        return serialized_hex
    
    def get_chain_id(self) -> int:
        """
        Get the chain ID for EVM networks.
            
        Returns:
            int: The chain ID
        """
        if self.metadata.chain_type == ChainType.EVM:
            # For Web3, get chain ID from the provider
            return self.api.eth.chain_id
        raise ValueError("Chain ID is only available for EVM networks")

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