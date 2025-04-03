# author @ Jay Pan

# Use the already written substrate code:

# import time
# from dataclasses import dataclass
# from substrateinterface import SubstrateInterface, Keypair
# from scalecodec.types import GenericExtrinsic
# from scalecodec.base import RuntimeConfiguration
# from scalecodec.type_registry import load_type_registry_preset
# from scalecodec.utils.ss58 import ss58_encode
# import socket

# DEBUG = False


# def get_account_balance(substrate, addr, block_hash=None):
#     result = substrate.query(
#         'System', 'Account', [addr], block_hash=block_hash)
#     return int(result['data']['free'].value)


# def show_extrinsic(receipt, info_type):
#     if receipt.is_success:
#         print(f'🚀 {info_type}, Success: {receipt.get_extrinsic_identifier()}')
#     else:
#         print(f'💥 {info_type}, Extrinsic Failed: {receipt.error_message} {receipt.get_extrinsic_identifier()}')


# def _generate_call_description(call):
#     """Generates a description for an arbitrary extrinsic call"""
#     # print(type(call), call)
#     # assert type(call) == "scalecodec.types.GenericCall"
#     module = call.call_module.name
#     function = call.call_function.name
#     if module == 'Sudo':
#         # I don't like this solution, but unfortunately I was not able to access
#         # call.call_args in that way to extract the module and function of the payload.
#         desc = call.__str__().split('{')[3]
#         desc = desc.split("'")
#         submodule = desc[3]
#         subfunction = desc[7]
#         return f'{module}.{function}({submodule}.{subfunction})'
#     else:
#         return f'{module}.{function}'


# def _generate_batch_description(batch):
#     """Generates a description for an extrinsic batch"""
#     desc = [f'{_generate_call_description(b)}' for b in batch]
#     desc = ', '.join(desc)
#     return f'Batch[ {desc} ]'


# def into_keypair(keypair_or_uri) -> Keypair:
#     """Takes either a Keypair, or transforms a given uri into one"""
#     if isinstance(keypair_or_uri, str):
#         return Keypair.create_from_uri(keypair_or_uri)
#     elif isinstance(keypair_or_uri, Keypair):
#         return keypair_or_uri
#     else:
#         raise TypeError


# def into_substrate(substrate_or_url) -> SubstrateInterface:
#     """Takes a SubstrateInterface, or takes into one by given url"""
#     if isinstance(substrate_or_url, str):
#         return SubstrateInterface(substrate_or_url)
#     elif isinstance(substrate_or_url, SubstrateInterface):
#         return substrate_or_url
#     else:
#         raise TypeError


# @dataclass
# class ExtrinsicBatch:
#     """
#     ExtrinsicBatch class for simple creation of extrinsic-batch to be executed.

#     When initialising, pass either an existing SubstrateInterface/WS-URL and
#     optional Keypair/URI, or use the defaults. The ExtrinsicBatch is designed
#     to be used on one chain (relaychain/parachain), because the usage of one
#     SubstrateInterface. It is also designed for one user to execute the batch,
#     because the Utility pallet does not varying users unfortunately.

#     Example 1:    ex_stack = ExtrinsicStack(substrate, kp_src)
#     Example 2:    ex_stack = ExtrinsicStack(WS_URL, '//Bob')
#     Example 3:    ex_stack = ExtrinsicStack()
#     """
#     substrate: SubstrateInterface
#     keypair: Keypair
#     batch: list
#     submit_extrinsic: GenericExtrinsic

#     def __init__(self, substrate_or_url, keypair_or_uri):
#         self.substrate = into_substrate(substrate_or_url)
#         self.keypair = into_keypair(keypair_or_uri)
#         self.batch = []

#     def __enter__(self):
#         return self

#     def __exit__(self, exc_type, exc_val, exc_tb):
#         return self

#     def __str__(self):
#         return 'ExtrinsicBatch@{}, batch: {}'.format(self.substrate, self.batch)

#     def compose_call(self, module, extrinsic, params):
#         """Composes and appends an extrinsic call to this stack"""
#         self.batch.append(self._compose_call(
#             self.substrate, module, extrinsic, params))

#     def compose_sudo_call(self, module, extrinsic, params):
#         """Composes a sudo-user extrinsic call and adds it this stack"""
#         self.batch.append(self._compose_sudo_call(
#             self.substrate, module, extrinsic, params))

#     # TODO
#     def execute(self, wait_for_finalization=False, alt_keypair=None, tip=0) -> str:
#         """Executes the extrinsic-stack"""
#         if not self.batch:
#             return ''
#         if alt_keypair is None:
#             alt_keypair = self.keypair
#         return self._execute_extrinsic_batch(
#             self.substrate, alt_keypair, self.batch, wait_for_finalization, tip)

#     def get_payload(self):
#         if not self.batch:
#             return None

#         # Wrap payload into a utility batch cal
#         return self.substrate.compose_call(
#             call_module='Utility',
#             call_function='batch_all',
#             call_params={
#                 'calls': self.batch,
#             })

#     # TODO
#     def execute_n_clear(self, alt_keypair=None, wait_for_finalization=False, tip=0) -> str:
#         """Combination of execute() and clear()"""
#         if alt_keypair is None:
#             alt_keypair = self.keypair
#         receipt = self.execute(wait_for_finalization, alt_keypair, tip)
#         self.clear()
#         return receipt

#     def clear(self):
#         """Clears the current extrinsic-stack"""
#         self.batch = []

#     def clone(self, keypair_or_uri=None):
#         """Creates a duplicate, by using the same SubstrateInterface"""
#         if keypair_or_uri is None:
#             keypair_or_uri = self.keypair
#         return ExtrinsicBatch(self.substrate, keypair_or_uri)

#     def get_calls(self):
#         """returns a list of the alls of the extrinsics in this stack"""
#         return [x for x in self.batch]

#     def _compose_call(self, substrate, module, extrinsic, params):
#         """
#         Composes a substrate-extrinsic-call on any module
#         Example:
#           module = 'Rbac'
#           extrinsic = 'add_role'
#           params = {'role_id': entity_id, 'name': name }
#         """
#         return substrate.compose_call(
#             call_module=module,
#             call_function=extrinsic,
#             call_params=params
#         )

#     def _compose_sudo_call(self, substrate, module, extrinsic, params):
#         """
#         Composes a substrate-sudo-extrinsic-call on any module
#         Parameters same as in compose_call, see above
#         """
#         payload = self._compose_call(substrate, module, extrinsic, params)
#         return self._compose_call(substrate, 'Sudo', 'sudo', {'call': payload.value})

#     def _execute_extrinsic_batch(self, substrate, kp_src, batch,
#                                  wait_for_finalization=False,
#                                  tip=0) -> str:
#         """
#         Executes a extrinsic-stack/batch-call on substrate
#         Parameters:
#           substrate:  SubstrateInterface
#           kp_src:     Keypair
#           batch:      list[_compose_call(), _compose_call(), ...]
#         """
#         # Wrap payload into a utility batch cal
#         call = substrate.compose_call(
#             call_module='Utility',
#             call_function='batch_all',
#             call_params={
#                 'calls': batch,
#             })

#         nonce = substrate.get_account_nonce(kp_src.ss58_address)
#         extrinsic = substrate.create_signed_extrinsic(
#             call=call,
#             keypair=kp_src,
#             era={'period': 64},
#             nonce=nonce,
#             tip=tip
#         )
#         # Store the current extrinsic
#         self.submit_extrinsic = extrinsic

#         receipt = substrate.submit_extrinsic(
#             extrinsic, wait_for_inclusion=True,
#             wait_for_finalization=wait_for_finalization)
#         if len(batch) == 1:
#             description = _generate_call_description(batch[0])
#         else:
#             description = _generate_batch_description(batch)
#         if DEBUG:
#             show_extrinsic(receipt, description)

#         return receipt


# def get_block_height(substrate):
#     latest_block = substrate.get_block()
#     return latest_block['header']['number']


# def get_block_hash(substrate, block_num):
#     return substrate.get_block_hash(block_id=block_num)


# def get_chain(substrate):
#     return substrate.rpc_request(method='system_chain', params=[]).get('result')


# def wait_for_n_blocks(substrate, n=1, wait_time=700):
#     # Force reconnect the node
#     """Waits until the next block has been created"""
#     height = get_block_height(substrate)
#     wait_height = height + n
#     past = 0
#     retry = 0

#     start = time.time()
#     while past < n:
#         end = time.time()
#         if end - start > wait_time:
#             raise TimeoutError('Timeout for waiting blocks')
#         try:
#             substrate.connect_websocket()
#             # Force to get the latest block metadata to check whether the node can support or not
#             substrate.get_block_metadata()
#             next_height = get_block_height(substrate)
#         except (BrokenPipeError, socket.error) as e:
#             if retry > 3:
#                 raise e
#             print(f'Error: {e}, now waiting 30 seconds')
#             # It's preparing for the parachain restart
#             time.sleep(30)
#             retry += 1
#             continue

#         if height == next_height:
#             time.sleep(5)
#         elif next_height >= wait_height:
#             print(f'Current block: {height}, and now we can stop at {wait_height}')
#             break
#         else:
#             print(f'Current block: {height}, but waiting at {wait_height}')
#             height = next_height
#             past = past + 1


# def calculate_multi_sig(kps, threshold):
#     '''https://github.com/polkascan/py-scale-codec/blob/f063cfd47c836895886697e7d7112cbc4e7514b3/test/test_scale_types.py#L383'''  # noqa: E501

#     addrs = [kp.ss58_address for kp in kps]
#     RuntimeConfiguration().update_type_registry(load_type_registry_preset('legacy'))
#     multi_account_id = RuntimeConfiguration().get_decoder_class('MultiAccountId')

#     multi_sig_account = multi_account_id.create_from_account_list(addrs, threshold)
#     return ss58_encode(multi_sig_account.value.replace('0x', ''), 42)