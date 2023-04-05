# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""python package of pdf report functions."""


from nvmetools.lib.nvme.reports.features import timestamp
from nvmetools.lib.nvme.reports.firmware import (
    firmware_activate,
    firmware_download,
    firmware_security,
    firmware_update
)
from nvmetools.lib.nvme.reports.info import admin_commands, suite_end_info, suite_start_info
from nvmetools.lib.nvme.reports.performance import (
    address_alignment,
    big_file_reads,
    big_file_writes,
    data_compression,
    data_deduplication,
    idle_latency,
    long_burst_performance,
    long_burst_performance_full_drive,
    read_buffer,
    short_burst_performance,
    short_burst_performance_full_drive,
    trim
)
from nvmetools.lib.nvme.reports.selftest import extended_selftest, short_diagnostic, short_selftest
from nvmetools.lib.nvme.reports.smart import (
    background_smart,
    smart_data,
)
from nvmetools.lib.nvme.reports.stress import (
    burst_stress,
    high_bandwidth_stress,
    high_iops_stress,
    read_disturb_stress,
    temperature_cycle_stress,
)
