# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Test Suite to verify functional features.

This suite runs Test Cases to verify the admin commands, SMART attrbiutes, timestamp, and
short self-test.
"""
from nvmetools import TestSuite, tests
from nvmetools.support.conversions import is_windows_admin

if not is_windows_admin():
    raise Exception("This Test Suite must be run as Administrator.")

with TestSuite("Functional", __doc__) as suite:

    info = tests.suite_start_info(suite)

    tests.admin_commands(suite)
    tests.background_smart(suite)
    tests.smart_data(suite)
    tests.timestamp(suite)

    tests.short_selftest(suite)

    tests.suite_end_info(suite, info)
