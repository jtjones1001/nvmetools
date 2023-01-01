# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Test Suites for NVMe solid state drives (SSD) run using the testnvme console command..

.. highlight:: none

The testnvme command passes the same standard parameters to each Test Suite

    - nvme:          NVMe to test
    - volume:        Logical volume to test
    - loglevel:      Amount of detail to include in the logging
    - uid:           Unique ID to use for directory name

The first test case in every Test Suite is suite_start_info and the last test case is suite_end_info.

"""
from nvmetools.suites.common import firmware, functional, health, performance, selftest, stress
from nvmetools.suites.demo import big_demo, short_demo
from nvmetools.suites.dev import dev, devinfo
