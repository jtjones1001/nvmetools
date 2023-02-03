# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Short and extended self-test.

This suite runs Test Cases to verify the short and extended versions of the self-test.
"""
import platform
import time

from nvmetools import TestSuite, tests
from nvmetools.support.conversions import is_windows_admin

if not is_windows_admin():
    raise Exception("This Test Suite must be run as Administrator.")

with TestSuite("Selftest", __doc__) as suite:

    info = tests.suite_start_info(suite)

    tests.short_selftest(suite)

    if platform.system() == "Windows":
        time.sleep(600)
    tests.extended_selftest(suite)

    tests.suite_end_info(suite, info)
