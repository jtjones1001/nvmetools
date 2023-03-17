# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import nvmetools.lib.nvme.requirements as rqmts
from nvmetools.support.framework import TestCase, TestStep
from nvmetools.support.info import Info


def suite_start_info(suite):
    """Read and verify drive information at start of test suite.

    Reads information about the NVMe drive directly from the drive and the Operating System (OS)
    using the nvmecmd utility.  This utility reads most of the drive information using NVMe Admin
    Commands but a small amount of information, such as PCIe root port and link speed and width,
    are read from the OS.

    Verifies no critical warnings or errors, no excessive throttling, no prior self-test failures,
    and the drive is not worn out.

    This test should be run at the start of suite so the info can be referenced at the end of the
    suite.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Suite start info", suite_start_info.__doc__) as test:

        with TestStep(test, "Read info", "Read NVMe information using nvmecmd.") as step:

            info = Info(
                nvme=suite.nvme,
                directory=step.directory,
                tbw=suite.device["TBW"],
                warranty=suite.device["Warranty Years"],
                client_drive=suite.device["Client Drive"],
            )

            rqmts.admin_commands_pass(step, info)

            # add data needed for generating report and dashboard

            suite.data["start_info"] = {
                "metadata": info.metadata,
                "full_parameters": info.full_parameters,
                "parameters": info.parameters,
                "command log": info.info["nvme"]["command log"],
                "event log": info.info["nvme"]["event log"],
                "self-test log": info.info["nvme"]["self-test log"],
                "error log": info.info["nvme"]["error log"],
            }
            suite.get_drive_specification()

            test.data["parameters"] = info.parameters
            test.data["commands"] = info.summary["command times"]
            test.data["Throttle Percent Limit"] = suite.device["Throttle Percent Limit"]
            test.data["Wear Percent Limit"] = suite.device["Wear Percent Limit"]

        with TestStep(test, "Verify info", "Verify drive is healthy and not worn out.") as step:

            rqmts.available_spare_above_threshold(step, info)
            rqmts.nvm_system_reliable(step, info)
            rqmts.persistent_memory_reliable(step, info)
            rqmts.media_not_readonly(step, info)
            rqmts.memory_backup_not_failed(step, info)

            rqmts.no_media_errors(step, info)
            rqmts.no_critical_time(step, info)

            rqmts.throttle_time_within_limit(step, info, suite.device["Throttle Percent Limit"])
            rqmts.usage_within_limit(step, info, suite.device["Wear Percent Limit"])

            rqmts.no_prior_selftest_failures(step, info)

    return info
