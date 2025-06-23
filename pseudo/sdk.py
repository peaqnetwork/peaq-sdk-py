class PeaqSdk:
    def send_tx(
        self,
        call_or_tx: Union[GenericCall, dict],
        *,
        chain: ChainType,               # SUBSTRATE or EVM
        mode: Literal["fast","balanced","safe"] = "balanced",
        fee_multiplier: float = 1.0,    # overrides mode if given
        wait_for_finality: bool = False,
        confirmations: int = 1,         # for EVM
        max_retries: int = 5
    ) -> TxReceipt:
        """
        Unified entry point for all txs.
        """
        cfg = self._select_mode(mode, fee_multiplier, wait_for_finality, confirmations)
        if chain == ChainType.SUBSTRATE:
            native = self._substrate_handler.send(
                call=call_or_tx,
                tip_multiplier=cfg.tip_mult,
                wait_for_finalization=cfg.wait_for_finality,
                max_attempts=max_retries
            )
        else:
            native = self._evm_handler.send(
                tx=call_or_tx,
                gas_price_multiplier=cfg.tip_mult,
                wait_for_finality=cfg.wait_for_finality,
                confirmations=cfg.confirmations,
                max_attempts=max_retries
            )
        return self._format_unified_receipt(native)
