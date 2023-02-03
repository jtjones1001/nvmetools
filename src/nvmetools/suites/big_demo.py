# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Demonstration Test Suite with all NVMe Test Cases.

Test suite with all possible test cases that creates a big report for demonstration.
"""
import platform
import time

from nvmetools import TestSuite, tests
from nvmetools.support.conversions import is_windows_admin

if not is_windows_admin():
    raise Exception("This Test Suite must be run as Administrator.")


with TestSuite("Big Demo", __doc__) as suite:

    info = tests.suite_start_info(suite)
    tests.admin_commands(suite)

    # SMART

    tests.background_smart(suite)
    tests.smart_data(suite)

    # Features

    tests.timestamp(suite)

    # Firmware

    tests.firmware_update(suite)
    tests.firmware_activate(suite)
    tests.firmware_download(suite)
    tests.firmware_security(suite)

    # Selftests

    tests.short_selftest(suite)
    if platform.system() == "Windows":
        time.sleep(600)
    tests.extended_selftest(suite)

    # Performance tests

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

    # Stress tests

    tests.high_bandwidth_stress(suite)
    tests.high_iops_stress(suite)
    tests.burst_stress(suite)
    tests.temperature_cycle_stress(suite)

    tests.suite_end_info(suite, info)