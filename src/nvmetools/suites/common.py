# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import platform
import sys
import time

from nvmetools import TestSuite, fio, tests
from nvmetools.support.conversions import is_windows_admin

import psutil


def firmware(args):
    """Test Suite to verify firmware features.

    This suite runs Test Cases to verify firmware update, firmware activate, firmware download,
    and firmware security features.

    Args:
        args: dictionary of NVMe parameters passed from testnvme command
    """
    with TestSuite("Firmware", firmware.__doc__, **args) as suite:

        info = tests.suite_start_info(suite)

        tests.firmware_update(suite)
        tests.firmware_activate(suite)
        tests.firmware_download(suite)
        tests.firmware_security(suite)

        tests.suite_end_info(suite, info)


def functional(args):
    """Test Suite to verify functional features.

    This suite runs Test Cases to verify the admin commands, SMART attrbiutes, timestamp, and
    short self-test.

    Args:
        args: dictionary of NVMe parameters passed from testnvme command
    """
    with TestSuite("Functional", functional.__doc__, **args) as suite:

        info = tests.suite_start_info(suite)

        tests.admin_commands(suite)
        tests.background_smart(suite)
        tests.smart_data(suite)
        tests.timestamp(suite)

        tests.short_selftest(suite)

        tests.suite_end_info(suite, info)


def health(args):
    """Verifies drive health and wear with self-test diagnostic and SMART attributes.

    Check NVMe is a short Test Suite that verifies drive health and wear by running the drive
    diagnostic, reviewing SMART data and Self-Test history.

    Args:
        args: dictionary of NVMe parameters passed from testnvme command
    """
    if not is_windows_admin():
        print("This Test Suite must be run as Administrator.")
        sys.exit(1)

    with TestSuite("Check NVMe Health", health.__doc__, **args) as suite:
        info = tests.suite_start_info(suite)
        tests.short_diagnostic(suite)
        tests.suite_end_info(suite, info)


def performance(args):
    """Test suite to measure NVMe IO performance.

    Measures IO peformance for several conditions including short and long bursts of reads
    and writes.

    Args:
        args: dictionary of NVMe parameters passed from testnvme command
    """

    with TestSuite("Performance Test", performance.__doc__, **args) as suite:

        info = tests.suite_start_info(suite)

        tests.short_burst_performance(suite)
        tests.long_burst_performance(suite)
        tests.idle_latency(suite)
        tests.data_deduplication(suite)
        tests.read_buffer(suite)

        if fio.space_for_big_file(info, suite.volume):

            tests.big_file_writes(suite)

            tests.big_file_reads(suite)
            tests.data_compression(suite)
            tests.short_burst_performance_full(suite)
            tests.long_burst_performance_full(suite)

        tests.suite_end_info(suite, info)


def selftest(args):
    """Short and extended self-test.

    This suite runs Test Cases to verify the short and extended versions of the self-test.

    Args:
        args: dictionary of NVMe parameters passed from testnvme command

    """
    if not is_windows_admin():
        print("This Test Suite must be run as Administrator.")
        sys.exit(1)

    with TestSuite("Selftest", selftest.__doc__, **args) as suite:
        info = tests.suite_start_info(suite)

        tests.short_selftest(suite)

        if platform.system() == "Windows":
            time.sleep(600)
        tests.extended_selftest(suite)

        tests.suite_end_info(suite, info)


def stress(args):
    """Test suite to verify drive reliaility under IO stress.

    This suite runs Test Cases to stress the drive in several different ways

    Args:
        args: dictionary of NVMe parameters passed from testnvme command.
    """

    with TestSuite("Stress", stress.__doc__, **args) as suite:

        info = tests.suite_start_info(suite)

        tests.high_bandwidth_stress(suite)
        tests.high_iops_stress(suite)
        tests.burst_stress(suite)
        tests.temperature_cycle_stress(suite)

        tests.suite_end_info(suite, info)
