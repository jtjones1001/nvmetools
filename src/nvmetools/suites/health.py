# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Verifies drive health and wear with self-test diagnostic and SMART attributes.

Check NVMe is a short Test Suite that verifies drive health and wear by running the drive
diagnostic, reviewing SMART data and Self-Test history.
"""
from nvmetools import TestSuite, tests
from nvmetools.support.conversions import is_windows_admin

if not is_windows_admin():
    raise Exception("This Test Suite must be run as Administrator.")

with TestSuite("Check NVMe Health", __doc__) as suite:

    info = tests.suite_start_info(suite)
    tests.short_diagnostic(suite)
    tests.suite_end_info(suite, info)
