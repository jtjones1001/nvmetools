# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""This module provides requirements for debugging."""

from nvmetools.support.framework import verification


def _force_pass(step):
    verification(
        rqmt_id=0,
        step=step,
        title="Force pass",
        verified=True,
        value="PASS",
    )


def _force_fail(step):
    verification(
        rqmt_id=1,
        step=step,
        title="Force fail",
        verified=False,
        value="FAIL",
    )
