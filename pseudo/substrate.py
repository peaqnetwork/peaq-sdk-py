def send(call, tip_multiplier, wait_for_finalization, max_attempts):
    base_fee = api.get_payment_info(call).partialFee
    tip = int(base_fee * tip_multiplier)
    attempt = 0
    while attempt < max_attempts:
        extrinsic = api.create_signed_extrinsic(call, tip=tip)
        try:
            receipt = api.submit_extrinsic(
                extrinsic,
                wait_for_inclusion=True,
                wait_for_finalization=wait_for_finalization
            )
            return receipt
        except PriorityTooLow:
            tip = int(tip * 1.25)
            attempt += 1
            sleep(0.5)
        except WebSocketClosed:
            reconnect_api()
            attempt += 1
            sleep(0.5)
    raise ExtrinsicExecutionError("…")
