# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
from nvmetools import TestSuite, tests


def devinfo(args):
    """Read and verify start and end info for development."""
    with TestSuite("Info", devinfo.__doc__, **args) as suite:
        suite.stop_on_fail = False
        info = tests.suite_start_info(suite)
        tests.suite_end_info(suite, info)


def dev(args):
    """Short suite for test development."""
    with TestSuite("Development", dev.__doc__, **args) as suite:

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

        # Performance tests

        tests.short_burst_performance(suite)

        tests.aspm_latency(suite)
        tests.nonop_power_times(suite)

        tests.data_compression(suite)
        tests.data_deduplication(suite)

        tests.read_buffer(suite)

        tests.big_file_writes(suite)
        tests.big_file_reads(suite)

        tests.short_burst_performance_full(suite)

        # Stress tests

        tests.high_bandwidth_stress(suite)
        tests.high_iops_stress(suite)
        tests.burst_stress(suite)
        tests.temperature_cycle_stress(suite)

        tests.suite_end_info(suite, info)
