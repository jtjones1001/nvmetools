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
        tests.long_burst_performance(suite)

        tests.suite_end_info(suite, info)
