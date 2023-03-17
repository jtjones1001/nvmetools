# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import nvmetools.lib.nvme.requirements as rqmts
from nvmetools.support.framework import TestCase, TestStep
from nvmetools.support.info import Info


def suite_end_info(suite, start_info):
    """Reads information at test suite end and verifies no critical errors, warnings, or changes.

    Verifies drive parameters change as expected across two readings.  Static parameters, such as
    Model and Serial Number, are verified not to change. SMART counter parameters, such as Power-On
    Hours, are verified not to decrease or reset.

    Args:
        suite:  Parent TestSuite instance
        start_info: Instance of Info class with information from start of suite
    """

    with TestCase(suite, "Suite end info", suite_end_info.__doc__) as test:

        with TestStep(test, "Read info", "Read NVMe information using nvmecmd.") as step:

            info = Info(
                test.suite.nvme,
                directory=step.directory,
                tbw=suite.device["TBW"],
                warranty=suite.device["Warranty Years"],
                client_drive=suite.device["Client Drive"],
                compare_info=start_info,
            )

            rqmts.admin_commands_pass(step, info)

            suite.data["end_info"] = test.data["end_info"] = {
                "metadata": info.metadata,
                "full_parameters": info.full_parameters,
                "parameters": info.parameters,
                "compare": info.compare,
                "command log": info.info["nvme"]["command log"],
                "event log": info.info["nvme"]["event log"],
                "self-test log": info.info["nvme"]["self-test log"],
                "error log": info.info["nvme"]["error log"],
            }
            test.data["start_info"] = {
                "metadata": start_info.metadata,
                "full_parameters": start_info.full_parameters,
                "parameters": start_info.parameters,
            }

        with TestStep(test, "Verify info", "Verify drive is healthy and not worn out.") as step:

            rqmts.available_spare_above_threshold(step, start_info)
            rqmts.nvm_system_reliable(step, start_info)
            rqmts.persistent_memory_reliable(step, start_info)
            rqmts.media_not_readonly(step, start_info)
            rqmts.memory_backup_not_failed(step, start_info)
            rqmts.no_media_errors(step, info)
            rqmts.no_critical_time(step, info)
            rqmts.throttle_time_within_limit(step, info, suite.device["Throttle Percent Limit"])
            rqmts.usage_within_limit(step, info)

            rqmts.no_prior_selftest_failures(step, info)

        with TestStep(test, "Verify changes", "Verify no unexpected changes from starting info.") as step:

            rqmts.no_static_parameter_changes(step, info)
            rqmts.no_counter_parameter_decrements(step, info)
            rqmts.accurate_power_on_change(step, info)
            rqmts.no_errorcount_change(step, info)

    return info
