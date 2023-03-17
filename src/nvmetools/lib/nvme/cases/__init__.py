# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Test Cases for NVMe solid state drives (SSD).

All NVMe Test Cases are combined into this single python package so they can
easily be imported and run as shown here.

    .. code-block::

        import nvmetools.lib.nvme.cases as tests

        with TestSuite("suite") as suite:

            tests.timestamp(suite)


.. warning::
   The NVMe Test Cases provided in this release are examples only.

"""
from nvmetools.lib.nvme.cases.features.timestamp import timestamp
from nvmetools.lib.nvme.cases.firmware.firmware_activate import firmware_activate
from nvmetools.lib.nvme.cases.firmware.firmware_download import firmware_download
from nvmetools.lib.nvme.cases.firmware.firmware_security import firmware_security
from nvmetools.lib.nvme.cases.firmware.firmware_update import firmware_update
from nvmetools.lib.nvme.cases.info.admin_commands import admin_commands
from nvmetools.lib.nvme.cases.info.suite_end_info import suite_end_info
from nvmetools.lib.nvme.cases.info.suite_start_info import suite_start_info
from nvmetools.lib.nvme.cases.performance.address_alignment import address_alignment
from nvmetools.lib.nvme.cases.performance.big_file_reads import big_file_reads
from nvmetools.lib.nvme.cases.performance.big_file_writes import big_file_writes
from nvmetools.lib.nvme.cases.performance.data_compression import data_compression
from nvmetools.lib.nvme.cases.performance.data_deduplication import data_deduplication
from nvmetools.lib.nvme.cases.performance.idle_latency import idle_latency
from nvmetools.lib.nvme.cases.performance.long_burst_performance import long_burst_performance
from nvmetools.lib.nvme.cases.performance.long_burst_performance_full import long_burst_performance_full
from nvmetools.lib.nvme.cases.performance.read_buffer import read_buffer
from nvmetools.lib.nvme.cases.performance.short_burst_performance import short_burst_performance
from nvmetools.lib.nvme.cases.performance.short_burst_performance_full import short_burst_performance_full
from nvmetools.lib.nvme.cases.selftest.extended_selftest import extended_selftest
from nvmetools.lib.nvme.cases.selftest.short_diagnostic import short_diagnostic
from nvmetools.lib.nvme.cases.selftest.short_selftest import short_selftest
from nvmetools.lib.nvme.cases.smart.background_smart import background_smart
from nvmetools.lib.nvme.cases.smart.smart_data import smart_data
from nvmetools.lib.nvme.cases.stress.burst_stress import burst_stress
from nvmetools.lib.nvme.cases.stress.high_bandwidth_stress import high_bandwidth_stress
from nvmetools.lib.nvme.cases.stress.high_iops_stress import high_iops_stress
from nvmetools.lib.nvme.cases.stress.read_disturb_stress import read_disturb_stress
from nvmetools.lib.nvme.cases.stress.temperature_cycle_stress import temperature_cycle_stress
