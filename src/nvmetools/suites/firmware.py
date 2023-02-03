# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Test Suite to verify firmware features.

This suite runs Test Cases to verify firmware update, firmware activate, firmware download,
and firmware security features.
"""
from nvmetools import TestSuite, tests

with TestSuite("Firmware", __doc__) as suite:

    info = tests.suite_start_info(suite)

    tests.firmware_update(suite)
    tests.firmware_activate(suite)
    tests.firmware_download(suite)
    tests.firmware_security(suite)

    tests.suite_end_info(suite, info)
