# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""This module provides requirements for the fio application. ID are 100-109."""

from nvmetools.support.framework import verification
from nvmetools.support.log import log


def no_io_errors(step, fio):
    if type(fio) == int:
        value = fio
    else:
        value = fio.io_errors

    verification(
        rqmt_id=100,
        step=step,
        title="No errors shall occur running IO",
        verified=(value == 0),
        value=value,
    )


def no_data_corruption(step, fio):
    if type(fio) == int:
        value = fio
    else:
        value = fio.corruption_errors

    verification(
        rqmt_id=101,
        step=step,
        title="No data corruption shall occur running IO",
        verified=(value == 0),
        value=value,
    )
