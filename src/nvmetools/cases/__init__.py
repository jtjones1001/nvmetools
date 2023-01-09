# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Test Cases for NVMe solid state drives (SSD).

All NVMe Test Cases are combined into this single python package (nvmetools.tests) so they can
easily be imported and run as shown here.

    .. code-block::

        from nvmetools import tests

        with TestSuite("suite") as suite:

            tests.timestamp(suite)


.. warning::
   The NVMe Test Cases provided in this release are examples only.

"""
from nvmetools.cases.features.timestamp import timestamp
from nvmetools.cases.firmware.firmware_activate import firmware_activate
from nvmetools.cases.firmware.firmware_download import firmware_download
from nvmetools.cases.firmware.firmware_security import firmware_security
from nvmetools.cases.firmware.firmware_update import firmware_update
from nvmetools.cases.info.admin_commands import admin_commands
from nvmetools.cases.info.suite_end_info import suite_end_info
from nvmetools.cases.info.suite_start_info import suite_start_info
from nvmetools.cases.performance.address_alignment import address_alignment
from nvmetools.cases.performance.big_file_reads import big_file_reads
from nvmetools.cases.performance.big_file_writes import big_file_writes
from nvmetools.cases.performance.data_compression import data_compression
from nvmetools.cases.performance.data_deduplication import data_deduplication
from nvmetools.cases.performance.idle_latency import idle_latency
from nvmetools.cases.performance.long_burst_performance import long_burst_performance
from nvmetools.cases.performance.long_burst_performance_full import long_burst_performance_full
from nvmetools.cases.performance.read_buffer import read_buffer
from nvmetools.cases.performance.short_burst_performance import short_burst_performance
from nvmetools.cases.performance.short_burst_performance_full import short_burst_performance_full
from nvmetools.cases.selftest.extended_selftest import extended_selftest
from nvmetools.cases.selftest.short_diagnostic import short_diagnostic
from nvmetools.cases.selftest.short_selftest import short_selftest
from nvmetools.cases.smart.background_smart import background_smart
from nvmetools.cases.smart.smart_data import smart_data
from nvmetools.cases.stress.burst_stress import burst_stress
from nvmetools.cases.stress.high_bandwidth_stress import high_bandwidth_stress
from nvmetools.cases.stress.high_iops_stress import high_iops_stress
from nvmetools.cases.stress.read_disturb_stress import read_disturb_stress
from nvmetools.cases.stress.temperature_cycle_stress import temperature_cycle_stress
