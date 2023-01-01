# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""This module provides requirements for the testing of NVMe information.  ID are 10-49."""

from nvmetools.support.conversions import as_float, as_int
from nvmetools.support.framework import verification


def admin_commands_pass(step, info):
    commands_status = "Pass"
    commands = info.summary["command times"]
    for command in commands:
        if command["return code"] != 0:
            commands_status = "Fail"

    verification(
        rqmt_id=10,
        step=step,
        title="Admin commands shall pass",
        verified=(commands_status == "Pass"),
        value=commands_status,
    )


def no_critical_warnings(step, info):
    if info.parameters["Critical Warnings"] == "No":
        value = 0
    else:
        value = 1

    verification(
        rqmt_id=11,
        step=step,
        title="Critical warnings shall be 0",
        verified=(value == 0),
        value=value,
    )


def no_prior_selftest_failures(step, info):

    value = as_int(info.parameters["Number Of Failed Self-Tests"])
    verification(
        rqmt_id=12,
        step=step,
        title="Prior self-test failures shall be 0",
        verified=(value == 0),
        value=value,
    )


def no_media_errors(step, info):

    value = as_int(info.parameters["Media and Data Integrity Errors"])
    verification(
        rqmt_id=13,
        step=step,
        title="Media and integrity errors shall be 0",
        verified=(value == 0),
        value=value,
    )


def no_critical_time(step, info):

    value = as_int(info.parameters["Critical Composite Temperature Time"])
    verification(
        rqmt_id=14,
        step=step,
        title="Time operating at or above the critical temperature shall be 0",
        verified=(value == 0),
        value=f"{value} min",
    )


def usage_within_limit(step, info, limit=90):

    value = as_int(info.parameters["Percentage Used"])
    verification(
        rqmt_id=15,
        step=step,
        title=f"Percentage Used shall be less than {limit}%",
        verified=(value < as_int(limit)),
        value=f"{value}%",
    )


def data_written_within_limit(step, info, limit=90):

    if "Data Used" in info.parameters:
        value = as_float(info.parameters["Data Used"])
        float_limit = as_float(limit)
        verification(
            rqmt_id=16,
            step=step,
            title=f"Data Used shall be less than {limit}% of TBW",
            verified=(value < float_limit),
            value=f"{value:0.1f}%",
        )


def power_on_hours_within_limit(step, info, limit=90):

    if info.parameters["Warranty Used"] != "NA":
        value = as_float(info.parameters["Warranty Used"])
        float_limit = as_float(limit)
        verification(
            rqmt_id=17,
            step=step,
            title=f"Power On Hours Used shall be less than {limit}% of Warranty Hours",
            verified=(value < float_limit),
            value=f"{value:0.1f}%",
        )


def throttle_time_within_limit(step, info, limit):

    if "Percent Throttled" in info.parameters:
        value = as_float(info.parameters["Percent Throttled"])
        float_limit = as_float(limit)

        verification(
            rqmt_id=18,
            step=step,
            title=f"Percent throttled shall be less than {limit}%",
            verified=(value < float_limit),
            value=f"{value:0.1f}%",
        )


def admin_command_reliability(step, samples):

    MINIMUM_COMMAND_SAMPLES = 10000

    verification(
        rqmt_id=19,
        step=step,
        title=f"Greater than {MINIMUM_COMMAND_SAMPLES:,} admin command shall complete without error",
        verified=(samples.total_command_fails == 0) and (samples.total_commands > MINIMUM_COMMAND_SAMPLES),
        value=f"{samples.total_command_fails} / {samples.total_commands:,}",
    )


def no_static_parameter_changes(step, info):

    value = info.summary["read details"]["static mismatches"]

    verification(
        rqmt_id=20,
        step=step,
        title="Static parameters, such as Model Number, shall not change",
        verified=(value == 0),
        value=value,
    )


def no_counter_parameter_decrements(step, info):

    value = info.summary["read details"]["counter mismatches"]

    verification(
        rqmt_id=21,
        step=step,
        title="SMART counters, such as Data Written, shall not decrement",
        verified=(value == 0),
        value=value,
    )


def admin_command_avg_latency(step, info, limit):

    verification(
        rqmt_id=22,
        step=step,
        title=f"Admin Command average latency shall be less than {limit} mS",
        verified=(info.avg_latency < limit),
        value=f"{info.avg_latency:0.1f} mS",
    )


def admin_command_max_latency(step, info, limit):

    verification(
        rqmt_id=23,
        step=step,
        title=f"Admin Command maximum latency shall be less than {limit} mS",
        verified=(info.max_latency < limit),
        value=f"{info.max_latency:0.1f} mS",
    )


def accurate_power_on_change(step, info):

    host_change = as_float(info.compare["deltas"]["host time seconds"]["delta"]) / 3600
    value = abs(as_int(info.compare["deltas"]["Power On Hours"]["delta"]) - host_change)

    verification(
        rqmt_id=24,
        step=step,
        title="Power On Hour change shall be within 1 hour of host time change",
        verified=(value <= 1.0),
        value=f"{value:0.2f} hrs",
    )


def smart_latency_increase(step, value, limit, sample):

    verification(
        rqmt_id=25,
        step=step,
        title=(
            f"Average latency of slowest {sample:,} IO shall not increase more than "
            + f"{limit}% with concurrent SMART reads"
        ),
        value=f"{value:0.3f}%",
        verified=(float(value) < limit),
    )


def no_errorcount_change(step, info):

    if str(type(info)) == "<class 'nvmetools.support.info.Info'>":
        media_error_increase = 0
        for counter in info.counters:
            if counter["title"] == "Media and Data Integrity Errors":
                media_error_increase = counter["delta"]

    else:
        media_error_increase = as_int(info._first_sample.parameters["Media and Data Integrity Errors"]) - as_int(
            info._last_sample.parameters["Media and Data Integrity Errors"]
        )
    verification(
        rqmt_id=26,
        step=step,
        title="Error count shall not increase",
        verified=(media_error_increase == 0),
        value=media_error_increase,
    )


def smart_read_data(step, value, limit):

    verification(
        rqmt_id=27,
        step=step,
        title=f"SMART attribute Data Read shall be within {limit:,.0f} " + "bytes of data read",
        verified=(value < limit),
        value=f"{value:,}",
    )


def smart_write_data(step, value, limit):

    verification(
        rqmt_id=28,
        step=step,
        title=f"SMART attribute Data Written shall be within {limit:,.0f} " + "bytes of data written",
        verified=(value < limit),
        value=f"{value:,}",
    )


def idle_temperature_delta(step, value):

    value = abs(value)

    verification(
        rqmt_id=29,
        step=step,
        title="Long burst end temperature shall be within 5C of start temperature",
        verified=(value < 5),
        value=f"{value:}C",
    )


def review_wear_values(step):

    verification(
        rqmt_id=30,
        step=step,
        title="Percentage * Used values shall be consistent",
        verified=False,
        value="REVIEW",
    )
