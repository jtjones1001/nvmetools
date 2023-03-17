# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""This module provides requirements for the self-test.  ID  are 70-89."""

from nvmetools.support.framework import verification


def selftest_pass(step, selftest):
    verification(
        rqmt_id=70,
        step=step,
        title="Self-test result shall be 0 indicating no errors",
        verified=(int(selftest.data["return code"]) == 0),
        value=selftest.data["return code"],
    )


def selftest_runtime(step, selftest):
    if "logfile" not in selftest.data:
        value = "N/A"
        verified = False
    else:
        value = f"{selftest.data['runtime']:0.2f} min"
        verified = selftest.data["runtime"] <= selftest.data["runtime limit"]

    verification(
        rqmt_id=71,
        step=step,
        title=f"Self-test run time shall be less than or equal to {selftest.data['runtime limit']} minutes",
        verified=verified,
        value=value,
    )


def selftest_monotonicity(step, selftest):
    if "logfile" not in selftest.data:
        value = "N/A"
        verified = False
    else:
        value = selftest.data["monotonic"]
        verified = selftest.data["monotonic"] == "Monotonic"

    verification(
        rqmt_id=72,
        step=step,
        title="Self-test progress is monotonic",
        verified=verified,
        value=value,
    )


def selftest_linearity(step, selftest, limit=0.9):
    if "logfile" not in selftest.data:
        value = "N/A"
        verified = False
    else:
        value = f"{selftest.data['linear']:0.2f}"
        verified = selftest.data["linear"] > limit

    verification(
        rqmt_id=73,
        step=step,
        title=f"Self-test progress is roughly linear (Coeff greater than {limit})",
        verified=verified,
        value=value,
    )


def selftest_poweron_hours(step, selftest):
    if "logfile" not in selftest.data:
        value = "N/A"
        verified = False
    else:
        verified = (selftest.data["result_poh"] == selftest.data["last_poh"]) or (
            selftest.data["result_poh"] == selftest.data["second_last_poh"]
        )

        if verified:
            value = "Match"
        else:
            value = "Mismatch"

    verification(
        rqmt_id=74,
        step=step,
        title="Self-test Power-On Hours match hours reported in log page 2",
        verified=verified,
        value=value,
    )
