# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
from nvmetools import Info, SkipTest, TestCase, TestStep, rqmts


def test_name_here(suite):
    """One line decription.

    Detailed description here...
    """
    with TestCase(suite, "Test name here", test_name_here.__doc__) as test:

        # Skip test if needed

        raise SkipTest

        # add parameters to test data dictionary

        test.data["Throttle Percent Limit"] = suite.device["Throttle Percent Limit"]
        test.data["Wear Percent Limit"] = suite.device["Wear Percent Limit"]

        # add a test step to do some stuff

        with TestStep(test, "Read info", "Read NVMe information using nvmecmd.") as step:

            info = Info(
                nvme=suite.nvme,
                directory=step.directory,
                tbw=suite.device["TBW"],
                warranty=suite.device["Warranty Years"],
                client_drive=suite.device["Client Drive"],
            )

            rqmts.admin_commands_pass(step, info)

            test.data["parameters"] = info.parameters
            test.data["commands"] = info.summary["command times"]

    # return data if needed, else remove

    return info
