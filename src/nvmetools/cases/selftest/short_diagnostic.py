# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import copy

import nvmetools.requirements as rqmts
from nvmetools.apps.nvmecmd import Selftest
from nvmetools.support.framework import TestCase, TestStep


def short_diagnostic(suite):
    """Verify short self-test diagnostic completes in 2 minutes without error.

    The short Self-test is a diagnostic testing sequence that tests the integrity and functionality of the
    controller and may include testing of the media associated with namespaces.   The run time is 2 minutes
    or less. The results are reported in Log Page 6 during and after the self-test."

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Short diagnostic", short_diagnostic.__doc__) as test:

        with TestStep(test, "Diagnostic") as step:

            selftest = Selftest(nvme=suite.nvme, directory=step.directory, extended=False)

            rqmts.selftest_pass(step, selftest)
            rqmts.selftest_runtime(step, selftest)
            rqmts.selftest_monotonicity(step, selftest)
            rqmts.selftest_linearity(step, selftest)
            rqmts.selftest_poweron_hours(step, selftest)

            test.data = copy.deepcopy(selftest.data)
