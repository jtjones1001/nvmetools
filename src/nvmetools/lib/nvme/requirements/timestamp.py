# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""This module provides requirements for the self-test.  ID are 90-99."""

from nvmetools.support.framework import verification


def timestamp_absolute_accuracy(step, value, limit=1):

    float_value = float(value)
    verification(
        rqmt_id=90,
        step=step,
        title=f"Timestamp shall be within {limit} hour(s) of host timestamp",
        verified=(float_value < limit),
        value=f"{float_value:0.2f} hours",
    )


def timestamp_linearity(step, value, limit=0.99):

    verification(
        rqmt_id=91,
        step=step,
        title=f"Timestamp count is linear (Coeff > {limit})",
        verified=(value > limit),
        value=f"{value:0.2f}",
    )


def timestamp_did_not_stop(step, info):

    if info.parameters["Timestamp Stopped"] == "True":
        value = "Fail"
    else:
        value = "Pass"

    verification(
        rqmt_id=92,
        step=step,
        title="Timestamp shall run without stopping",
        verified=(value == "Pass"),
        value=value,
    )


def timestamp_relative_accuracy(step, value, limit=1):

    float_value = float(value)
    verification(
        rqmt_id=93,
        step=step,
        title=f"Timestamp change shall be within {limit}% of host time change",
        verified=(float_value < limit),
        value=f"{float_value:0.1f}%",
    )


def timestamp_supported(step, value):

    verification(
        rqmt_id=94,
        step=step,
        title="Timestamp feature is supported",
        verified=value,
        value=f"{value}",
    )
