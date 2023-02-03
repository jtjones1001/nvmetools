# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Test suite to verify drive reliaility under IO stress.

This suite runs Test Cases to stress the drive in several different ways
"""
from nvmetools import TestSuite, tests

with TestSuite("Stress", __doc__) as suite:

    info = tests.suite_start_info(suite)

    tests.high_bandwidth_stress(suite)
    tests.high_iops_stress(suite)
    tests.burst_stress(suite)
    tests.temperature_cycle_stress(suite)

    tests.suite_end_info(suite, info)
