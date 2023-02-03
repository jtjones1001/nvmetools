# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Verifies drive health and wear with self-test diagnostic and SMART attributes.

Check NVMe is a short Test Suite that verifies drive health and wear by running the drive
diagnostic, reviewing SMART data and Self-Test history.
"""
from nvmetools import TestSuite, tests

with TestSuite("Check NVMe Health", __doc__, winadmin=True) as suite:

    info = tests.suite_start_info(suite)
    tests.short_diagnostic(suite)
    tests.suite_end_info(suite, info)
