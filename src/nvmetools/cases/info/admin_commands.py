# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
from nvmetools import InfoSamples, TestCase, TestStep, rqmts


def admin_commands(suite):
    """Verify admin commands reliability and performance (continuous running).

    This test runs a subset of admin commands several thousand times to get a large
    sample to ensure reliability.  The commands are run continuously, there  is no
    interval between commands.  This is not a practical use case and is only used to
    verify reliability.

    The admin commands run are Identify Controller, Identify Namespace, Get Log Page,
    and Get Feature.

    The test verifies the average and maximum latencies.  The information returned by
    the commands is verified as follows:

        Static parameters shall not change
        Counter parameters shall not decrement
        Dynamic parameters are not verified

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Admin commands", admin_commands.__doc__) as test:

        with TestStep(test, "Run commands") as step:

            info_samples = InfoSamples(
                nvme=suite.nvme,
                samples=5000,
                interval=0,
                directory=step.directory,
            )
            rqmts.admin_commands_pass(step, info_samples)
            rqmts.admin_command_reliability(step, info_samples)
            rqmts.no_static_parameter_changes(step, info_samples)
            rqmts.no_counter_parameter_decrements(step, info_samples)
            rqmts.admin_command_avg_latency(step, info_samples, suite.device["Average Admin Cmd Limit mS"])
            rqmts.admin_command_max_latency(step, info_samples, suite.device["Maximum Admin Cmd Limit mS"])

            test.data["Average Admin Cmd Limit mS"] = suite.device["Average Admin Cmd Limit mS"]
            test.data["Maximum Admin Cmd Limit mS"] = suite.device["Maximum Admin Cmd Limit mS"]

            test.data["sample size"] = info_samples.samples
            test.data["commands run"] = info_samples.total_commands
            test.data["commands failed"] = info_samples.total_command_fails
            test.data["command types"] = info_samples.command_types
