# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Demonstration Test Suite with a few NVMe Test Cases.

Test suite with a few Test Cases that run very quickly for short demonstrations.
"""
from nvmetools import TestSuite, tests

with TestSuite("Short Demo", __doc__) as suite:

    info = tests.suite_start_info(suite)

    tests.firmware_update(suite)
    tests.firmware_activate(suite)
    tests.firmware_download(suite)
    tests.firmware_security(suite)

    tests.suite_end_info(suite, info)
