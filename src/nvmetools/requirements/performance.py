# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""This module provides requirements for the testing of NVMe information.  ID are 50-69."""

from nvmetools.support.framework import verification


def power_exit_latency(step):

    verification(
        rqmt_id=50,
        step=step,
        title="IO read latency within power state exit latencies",
        verified=False,
        value="REVIEW",
    )


def power_entry_timeout(step):

    verification(
        rqmt_id=51,
        step=step,
        title="Power state entry timeout shall meet drive setting",
        verified=False,
        value="REVIEW",
    )


def random_read_4k_qd1_bandwidth(step, data, burst_type="Short"):

    limit = data["limits"]["Random Read, QD1, 4KiB"]
    value = data["random read"]["results"]["1"]["4096"]["bw"]

    verification(
        rqmt_id=52,
        step=step,
        title=f"{burst_type} burst, random reads, 4KiB, QD1 bandwidth shall be greater than {limit} GB/s",
        verified=value > limit,
        value=f"{value:0,.3f} GB/s",
    )


def random_write_4k_qd1_bandwidth(step, data, burst_type="Short"):

    limit = data["limits"]["Random Write, QD1, 4KiB"]
    value = data["random write"]["results"]["1"]["4096"]["bw"]

    verification(
        rqmt_id=53,
        step=step,
        title=f"{burst_type} burst, random writes, 4KiB, QD1 bandwidth shall be greater than {limit} GB/s",
        verified=value > limit,
        value=f"{value:0,.3f} GB/s",
    )


def sequential_read_128k_qd32_bandwidth(step, data, burst_type="Short"):

    limit = data["limits"]["Sequential Read, QD32, 128KiB"]
    value = data["sequential read"]["results"]["32"]["131072"]["bw"]

    verification(
        rqmt_id=54,
        step=step,
        title=f"{burst_type} burst, sequential reads, 128KiB, QD32 bandwidth shall be greater than {limit} GB/s",
        verified=value > limit,
        value=f"{value:0,.3f} GB/s",
    )


def sequential_write_128k_qd32_bandwidth(step, data, burst_type="Short"):

    limit = data["limits"]["Sequential Write, QD32, 128KiB"]
    value = data["sequential write"]["results"]["32"]["131072"]["bw"]

    verification(
        rqmt_id=55,
        step=step,
        title=f"{burst_type} burst, sequential writes, 128KiB, QD32 bandwidth shall be greater than {limit} GB/s",
        verified=value > limit,
        value=f"{value:0,.3f} GB/s",
    )


def bandwidth_vs_qd_bs(step):

    verification(
        rqmt_id=56,
        step=step,
        title="IO bandwidth behaved as expected with increasing queue depth and block size",
        verified=False,
        value="REVIEW",
    )
