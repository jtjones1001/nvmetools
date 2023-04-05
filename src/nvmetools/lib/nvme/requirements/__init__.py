# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Requirements for testing NVMe solid state drives (SSD).

All NVMe requirements are combined into this single python package so they
can easily be imported and run as shown here.

    .. code-block::

        import nvmetools.lib.nvme.requirements as rqmts

           # call from within a TestStep instance...

                rqmts.accurate_power_on_change(step)

"""
from nvmetools.lib.nvme.requirements.fio import no_data_corruption, no_io_errors
from nvmetools.lib.nvme.requirements.general import _force_fail, _force_none, _force_pass
from nvmetools.lib.nvme.requirements.info import (
    accurate_power_on_change,
    admin_command_avg_latency,
    admin_command_max_latency,
    admin_command_reliability,
    admin_commands_pass,
    available_spare_above_threshold,
    data_written_within_limit,
    idle_temperature_delta,
    media_not_readonly,
    memory_backup_not_failed,
    no_counter_parameter_decrements,
    no_critical_time,
    no_errorcount_change,
    no_errors_reading_samples,
    no_media_errors,
    no_prior_selftest_failures,
    no_static_parameter_changes,
    nvm_system_reliable,
    persistent_memory_reliable,
    power_on_hours_within_limit,
    review_wear_values,
    smart_latency_increase,
    smart_read_data,
    smart_write_data,
    throttle_time_within_limit,
    usage_within_limit,
    verify_empty_drive,
    verify_full_drive,
)
from nvmetools.lib.nvme.requirements.performance import (
    random_read_4k_qd1_bandwidth,
    random_write_4k_qd1_bandwidth,
    review_first_burst_bandwidth,
    review_io_bandwidth,
    review_power_entry_timeout,
    review_power_exit_latency,
    review_short_power_exit_latency,
    sequential_read_128k_qd32_bandwidth,
    sequential_write_128k_qd32_bandwidth,
    trim_command_pass
)
from nvmetools.lib.nvme.requirements.selftest import (
    selftest_linearity,
    selftest_monotonicity,
    selftest_pass,
    selftest_poweron_hours,
    selftest_runtime,
)
from nvmetools.lib.nvme.requirements.timestamp import (
    timestamp_absolute_accuracy,
    timestamp_did_not_stop,
    timestamp_linearity,
    timestamp_relative_accuracy,
    timestamp_supported,
)
