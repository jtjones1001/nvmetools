# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Demonstration Test Suite with a few NVMe Test Cases.

Test suite with a few Test Cases that run very quickly for short demonstrations.
"""
from nvmetools.lib.nvme import TestCase, TestStep, TestSuite, rqmts, tests


with TestSuite("BVT Simple", __doc__, uuid=r"bvt\simple") as suite:
    info = tests.suite_start_info(suite)
    tests.firmware_update(suite)
    tests.suite_end_info(suite, info)


with TestSuite("BVT Multiple Pass", __doc__, uuid=r"bvt\multiple_pass") as suite:
    info = tests.suite_start_info(suite)

    for _i in range(200):
        with TestCase(suite, "Same Test", " Looping") as test:
            with TestStep(test, "Step 1") as step:
                rqmts._force_pass(step)

    tests.suite_end_info(suite, info)


with TestSuite("BVT One Test Fail", __doc__, uuid=r"bvt\one_fail") as suite:
    info = tests.suite_start_info(suite)

    for _i in range(500):
        with TestCase(suite, "Same Test", " Looping") as test:
            with TestStep(test, "Step 1") as step:
                rqmts._force_pass(step)

    for _i in range(500):
        with TestCase(suite, "Same Test", " Looping") as test:
            with TestStep(test, "Step 1") as step:
                rqmts._force_fail(step)

    tests.suite_end_info(suite, info)

# Check the test.stop() function

with TestSuite("BVT Stop", __doc__, uuid=r"bvt\stop") as suite:
    info = tests.suite_start_info(suite)

    with TestCase(suite, "Stop Step Pass") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_pass(step)
            test.stop("Stop test with pass result")

    with TestCase(suite, "Stop Step Fail") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_fail(step)
            test.stop("Stop test with fail result")

    with TestCase(suite, "Stop Step None") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_none(step)
            test.stop("Stop test with fail result")

    with TestCase(suite, "Stop Step Fail2") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_pass(step)
            rqmts._force_pass(step)
            rqmts._force_pass(step)
            rqmts._force_none(step)
            test.stop("Stop test with fail result")

    with TestCase(suite, "Stop Pass") as test:
        test.stop("Stop test with pass result")

    with TestCase(suite, "Stop Fail") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_fail(step)
        test.stop("Stop test with fail result")

    with TestCase(suite, "Stop None") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_none(step)
        test.stop("Stop test with fail result")

    tests.suite_end_info(suite, info)

with TestSuite("BVT Test Abort", __doc__, uuid=r"bvt\test_abort`") as suite:
    suite.abort_on_exception = False
    info = tests.suite_start_info(suite)

    with TestCase(suite, "Abort Step Pass") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_pass(step)
            test.abort("Abort test with pass result")

    with TestCase(suite, "Abort Step Fail") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_fail(step)
            test.abort("Abort test with fail result")

    with TestCase(suite, "Abort Step None") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_none(step)
            test.abort("Abort test with fail result")

    with TestCase(suite, "Abort Step Fail2") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_pass(step)
            rqmts._force_pass(step)
            rqmts._force_pass(step)
            rqmts._force_none(step)
            test.abort("Abort test with fail result")

    with TestCase(suite, "Abort Pass") as test:
        test.abort("Abort test with pass result")

    with TestCase(suite, "Abort Fail") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_fail(step)
        test.abort("Abort test with fail result")

    with TestCase(suite, "Abort None") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_none(step)
        test.abort("Abort test with fail result")

    tests.suite_end_info(suite, info)


with TestSuite("BVT Test Abort and Stop", __doc__, uuid=r"bvt\test_abort_stop`") as suite:
    suite.abort_on_exception = True
    info = tests.suite_start_info(suite)

    with TestCase(suite, "Abort Step Pass") as test:
        with TestStep(test, "Step1") as step:
            rqmts._force_pass(step)
            test.abort("Abort test with pass result")

with TestSuite("BVT Suite Abort", __doc__, uuid=r"bvt\suite_abort") as suite:
    info = tests.suite_start_info(suite)
    suite.abort("Abort suite after first test")
    tests.firmware_update(suite)
    tests.suite_end_info(suite, info)

with TestSuite("BVT Suite Stop", __doc__, uuid=r"bvt\suite_stop") as suite:
    info = tests.suite_start_info(suite)
    suite.stop("Stop suite after first test")
    tests.firmware_update(suite)
    tests.suite_end_info(suite, info)


with TestSuite("BVT Abort Suite On Fail", __doc__, uuid=r"bvt\last") as suite:
    info = tests.suite_start_info(suite)

    suite.abort_on_fail = True
    for _i in range(3):
        with TestCase(suite, "Same Test", " Looping") as test:
            with TestStep(test, "Step 1") as step:
                rqmts._force_pass(step)

    for _i in range(3):
        with TestCase(suite, "Same Test", " Looping") as test:
            with TestStep(test, "Step 1") as step:
                rqmts._force_fail(step)

    tests.suite_end_info(suite, info)
