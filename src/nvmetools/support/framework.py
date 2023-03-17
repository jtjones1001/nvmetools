# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""This module provides a framework for testing devices.

The framework consists of Test Suites, Test Cases, Test Steps, and Requirement Verifications
structured as follows::

    Test Suite
        Test Case
            Test Step
                Verification
                Verification
            Test Step
                Verification
        Test Case
            Test Step
                Verification

The framework automatically runs a test suite and produces these three outputs

    -  Detailed text and json logs
    -  HTML dashboard
    -  Detailed PDF report

Because this framework is based on python and command line usage it can easily be integrated into
existing automation frameworks, test databases such as TestRail, and log storage servers.

The test flow can be changed with:

    - Skip test.  Skips to end of test, same as if the test never ran
    - Stop test.  Stops test case, evaluates pass/fail based on test steps up to the stop.
    - Stop suite.  Stops test suite, evaluates pass/fail based on test cases up to the stop.
    - Abort test.  Aborts test case, sets result to Abort (which is a type of fail)
    - Abort suite.  Aborts test suite, sets result to Abort (which is a type of fail)
    - Unhandled exception.  Same as Abort.

"""  # noqa: E501
import datetime
import glob
import inspect
import json
import logging
import os
import platform
import shutil
import time
import traceback

from nvmetools import DEFAULT_INFO_DIRECTORY, TEST_RESULT_DIRECTORY, USER_INFO_DIRECTORY, __version__
from nvmetools.apps.fio import check_fio_installation
from nvmetools.apps.nvmecmd import check_nvmecmd_permissions
from nvmetools.support.conversions import as_duration, is_admin, is_windows_admin
from nvmetools.support.log import start_logger

RQMT_PASSED = TEST_PASSED = PASSED = "PASSED"
RQMT_FAILED = TEST_FAILED = FAILED = "FAILED"
TEST_ABORTED = ABORTED = "ABORTED"
RQMT_SKIPPED = TEST_SKIPPED = SKIPPED = "SKIPPED"
COMPLETED = "COMPLETED"
STOPPED = "STOPPED"

RESULTS_FILE = "result.json"


class _NoAdmin(Exception):
    def __init__(self):
        self.code = 70
        self.nvmetools = True
        super().__init__("TEST SUITE must be run as admin.")


class _NoWinAdmin(Exception):
    def __init__(self):
        self.code = 71
        self.nvmetools = True
        super().__init__("TEST SUITE must be run as Windows administrator.")


class _InvalidStep(Exception):
    def __init__(self):
        self.code = 72
        self.nvmetools = True
        super().__init__("Parameter step is not type TestStep")


class _InvalidTest(Exception):
    def __init__(self):
        self.code = 73
        self.nvmetools = True
        super().__init__("Parameter test is not type TestCase")


class TestStep:
    def __init__(self, test, title, description=""):
        """Runs a Test Step.

        Args:
            test: Parent TestCase instance running the step
            title: Title of the step
            description: Optional description for the step

        A Test Step is run within a Test Case, which is run within a Test Suite.  A Test Step runs
        any number of requirement verifications, including zero.

        A Test Step result is either PASS or FAIL.  The Test Step result is PASS if all
        verifications PASS, otherwise it is FAIL.

        The step is run using the python with command.  This example runs a step with two
        verifications.  If either verification fails the step result is FAIL.

            .. code-block::

                with TestStep(test, "My step", "Very cool step description") as step:

                    value1, value2 = get_my_values()

                    rqmts.my_requirement(step, value1)
                    rqmts.my_second_requirement(step, value2)

        Attributes:
            test:            Parent TestCase instance running the test step
            suite:           Grandparent TestSuite instance running the test
            step_number:     Step number within the test
            directory:       Working directory for step specific files

        """
        self._title = title
        self._description = description
        self._start_counter = time.perf_counter()
        self.test = test
        self.suite = test.suite
        self.step_number = test.step_number = test.step_number + 1
        directory_name = f"{test.step_number}_{title.lower().replace(' ','_')}"
        self.directory = os.path.realpath(os.path.join(self.test.directory, directory_name))
        os.makedirs(self.directory, exist_ok=False)

        self.state = {
            "title": title,
            "description": self._description,
            "result": ABORTED,
            "flow": "",
            "start time": f"{datetime.datetime.now()}"[:-3],
            "end time": "",
            "end message": "",
            "duration (sec)": "",
            "duration": "",
            "directory": self.directory,
            "directory name": directory_name,
            "verifications": [],
        }

    def __enter__(self):
        log.frames("TestStep", inspect.getouterframes(inspect.currentframe(), context=1))
        log.verbose("")
        log.verbose(f"Step {self.test.step_number}: {self._title}")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):

        duration_seconds = time.perf_counter() - self._start_counter
        self.state["end time"] = f"{datetime.datetime.now()}"[:-3]
        self.state["description"] = self._description
        self.state["duration (sec)"] = f"{duration_seconds:.3f}"
        self.state["duration"] = as_duration(duration_seconds)

        fail_vers = sum(ver["result"] is not PASSED for ver in self.state["verifications"])

        # End normally

        if exc_type is None:
            if fail_vers > 0:
                self.state["result"] = FAILED
            else:
                self.state["result"] = PASSED
            self.state["flow"] = COMPLETED
            self.test.state["steps"].append(self.state)
            return True

        # else, set results and message then forward exception to TestCase

        elif exc_type is TestCase._Skip:
            self.state["result"] = self.state["flow"] = SKIPPED
            self.test.state["steps"].append(self.state)
            self.state["end message"] = "Step skipped with message: {exc_value}"
        elif exc_type in [TestCase._Stop, TestSuite._Stop]:
            if fail_vers > 0:
                self.state["result"] = FAILED
            else:
                self.state["result"] = PASSED
            self.state["flow"] = STOPPED
            self.state["end message"] = "Step stopped with message: {exc_value}"
        elif exc_type in [TestCase._Abort, TestSuite._Abort]:
            self.state["result"] = self.state["flow"] = ABORTED
            self.state["end message"] = "Step aborted with message: {exc_value}"
        else:
            self.state["result"] = self.state["flow"] = ABORTED
            self.state["end message"] = """Step aborted with unknown exception."""

        self.test.state["steps"].append(self.state)
        return False


class TestCase:
    run_on_fail = None
    run_on_exception = None
    run_on_timeout = None
    abort_on_fail = False

    def __init__(self, suite, title, description=""):
        """Runs a Test Case.

        Args:
            suite: Parent TestSuite instance running the test
            title: Title of the test
            description: Optional description for the test

        A Test Case which is run within a Test Suite.  A Test Case runs one or more Test Steps.

        A Test Case result is either PASS, FAIL, ABORT, or SKIP.  If an unhandled
        exception occurs or test.abort() is called the result is ABORT.  This result indicates
        the Test Case did not complete.  If the skip() method is called the result is SKIP.  This
        is the same as if the test was not run.  If not skipped or aborted, if any Test Step fails
        the result is FAIL, otherwise it is PASS.

        The test is run using the python with command.  This example runs a test with one test step.

            .. code-block::

                with TestCase(suite, "My test", "Very cool test description") as test:

                    with TestStep(test, "My step", "Very cool step description") as step:
                        value1, value2 = get_my_values()
                        rqmts.my_requirement(step, value1)

        A test can be stopped using the stop() method.  This example stops a test and sets the result
        based on the results up to that point.

            .. code-block::

                with TestCase(suite, "My test", "Very cool test description") as test:

                    with TestStep(test, "My step", "Very cool step description") as step:

                        value1, value2 = get_my_values()
                        if value1 == 32:
                            test.stop()

        A test can be skipped using the skip() method.  This example skips a test.  For example, if
        the testable feature is not supported.

            .. code-block::

                with TestCase(suite, "My test", "Very cool test description") as test:

                    with TestStep(test, "Feature support", "Verifies feature is supported") as step:

                        feature_supported = get_feature_support()
                        if not feature_supported:
                            test.skip()

        Attributes:
            suite:           Parent TestSuite instance running the test
            step_number:     Number of current test step
            test_number:     Test number within the test suite
            directory:       Working directory for step specific files
            abort_on_fail:   Aborts the test when a verification fails
        """
        self.data = {}
        self.suite = suite
        self._steps = []
        self._start_counter = time.perf_counter()
        self._description = description.split("\n")[0]
        self.details = description
        self.step_number = 0
        suite.test_number += 1
        directory_name = f"{suite.test_number}_{title.lower().replace(' ','_')}"
        self.directory = os.path.realpath(os.path.join(self.suite.directory, directory_name))
        os.makedirs(self.directory, exist_ok=False)

        self.state = {
            "number": suite.test_number,
            "title": title,
            "description": self._description,
            "details": self.details,
            "result": ABORTED,
            "flow": "",
            "start time": f"{datetime.datetime.now()}"[:-3],
            "end time": "",
            "end message": "",
            "duration (sec)": "",
            "duration": "",
            "directory": self.directory,
            "directory name": directory_name,
            "summary": {
                "steps": {"total": 0, "pass": 0, "fail": 0},
                "rqmts": {"total": 0, "pass": 0, "fail": 0},
                "verifications": {"total": 0, "pass": 0, "fail": 0},
            },
            "steps": [],
            "verifications": [],
            "rqmts": {},
        }

    def __enter__(self):
        log.info("")
        log.frames("TestCase", inspect.getouterframes(inspect.currentframe(), context=1))
        log.header(f"TEST {self.suite.test_number} : {self.state['title']}", 45)
        log.info(f"Description : {self.state['description']}")
        log.verbose(f"Start Time  : {self.state['start time']}")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):

        duration_seconds = time.perf_counter() - self._start_counter
        self.state["end time"] = f"{datetime.datetime.now()}"[:-3]
        self.state["description"] = self._description
        self.state["duration (sec)"] = f"{duration_seconds:.3f}"
        self.state["duration"] = as_duration(duration_seconds)
        self.state["data"] = self.data

        fail_steps = sum(step["result"] is not PASSED for step in self.state["steps"])

        unhandled_exception = exc_type in [TestSuite._Stop, TestSuite._Abort]

        if exc_type is None:
            if fail_steps > 0:
                self.state["result"] = FAILED
            else:
                self.state["result"] = PASSED
            self.state["flow"] = COMPLETED

        elif exc_type is TestCase._Skip:
            self.state["result"] = SKIPPED
            self.state["flow"] = SKIPPED
            self.state["end message"] = f"Test skipped with message: {exc_value}"

        elif exc_type in [TestCase._Stop, TestSuite._Stop]:
            log.info("")
            log.info(f"----> STOP : Test stopped with message: {exc_value}", indent=False)
            if fail_steps > 0:
                self.state["result"] = FAILED
            else:
                self.state["result"] = PASSED
            self.state["flow"] = STOPPED
            self.state["end message"] = f"Test stopped with message: {exc_value}"

        elif exc_type in [TestCase._Abort, TestSuite._Abort]:
            log.info("")
            log.info(f"----> ABORT : Test aborted with message: {exc_value}", indent=False)
            self.state["result"] = ABORTED
            self.state["flow"] = ABORTED
            self.state["end message"] = f"Test aborted with message: {exc_value}"

        else:
            self.state["result"] = ABORTED
            self.state["flow"] = ABORTED
            self.state["end message"] = "Test aborted with below exception.  "

            if self.suite.abort_on_exception:
                unhandled_exception = True

            if exc_type is KeyboardInterrupt:
                log.important("")
                log.important("----> TEST ABORTED BY CTRL-C\n\n")
                self.state["end message"] += "<br>Received CTRL-C."
            else:
                log.info("")
                log.info("----> EXCEPTION : Possible script error.", indent=False)
                log.info("----> ", indent=False)

                exception_lines = traceback.format_exception(
                    type(exc_value), exc_value, exc_traceback, limit=-2, chain=False
                )[1:]
                for line in exception_lines:
                    for each_line in line.split("\n"):
                        if len(each_line.strip().replace("\n", "")) > 0:
                            final_line = each_line.strip().replace("\n", "")
                            log.info("---->     " + final_line, indent=False)
                            self.state["end message"] += f"<br>{final_line}"
                    log.info("----> ", indent=False)

        # update the test suite and test results file

        self.update_summary()
        self.suite.state["tests"].append(self.state)
        results_file = os.path.join(self.directory, RESULTS_FILE)
        with open(results_file, "w", encoding="utf-8") as file_object:
            json.dump(self.state, file_object, ensure_ascii=False, indent=4)

        if self.state["result"] == SKIPPED:
            if self.suite.loglevel == 0:
                log.important(f"----> SKIP : TEST {self.suite.test_number} : {self.state['title']}", indent=False)
            else:
                log.info("")
                log.info(f"----> TEST SKIPPED : {exc_value}", indent=False)
        else:
            log.info("")
            log.verbose(f"End Time    : {self.state['end time']} ")
            log.info(f"Duration    : {self.state['duration (sec)']} seconds")
            log.info(
                f"Verifications: {self.state['summary']['verifications']['pass']} passed, "
                + f"{self.state['summary']['verifications']['fail']} failed "
            )
            log.info("")

            if self.state["result"] == PASSED:
                if self.suite.loglevel == 0:
                    log.important(
                        f"      PASS : TEST {self.suite.test_number} : {self.state['title']}", indent=False
                    )
                else:
                    log.info("TEST PASSED")
            else:
                if self.suite.loglevel == 0:
                    log.important(
                        f"----> FAIL : TEST {self.suite.test_number} : {self.state['title']}", indent=False
                    )
                else:
                    log.info("----> TEST FAILED", indent=False)

        # Forward the exceptions to test suite

        if exc_type is KeyboardInterrupt:
            raise TestSuite._Stop
        elif exc_type in [TestSuite._Stop, TestSuite._Abort]:
            return False
        elif unhandled_exception:
            raise TestSuite._Abort(f"Test {self.suite.test_number} had unhandled exception") from None

        elif self.suite.abort_on_exception and self.state["result"] == ABORTED:
            raise TestSuite._Abort(
                f"Test {self.suite.test_number} had exception with Abort-On-Exception enabled"
            ) from None

        elif (self.suite.abort_on_fail or self.abort_on_fail) and self.state["result"] == FAILED:
            raise TestSuite._Stop(f"Test {self.suite.test_number} failed with Abort-On-Fail enabled") from None

        return True

    def abort(self, message=""):
        """Aborts the TestCase and sets result to ABORT."""
        raise self._Abort(message)

    def skip(self, message=""):
        """Skip the TestCase and sets result to SKIPPED."""
        raise self._Skip(message)

    def stop(self, message=""):
        """Stop the TestCase and sets result on completed steps."""
        raise self._Stop(message)

    def update_summary(self):
        self.state = update_test_summary(self.state)

    class _Skip(Exception):
        def __init__(self, message=""):
            log.frames("TestCase.Skip", inspect.getouterframes(inspect.currentframe(), context=1))
            super().__init__(message)

    class _Stop(Exception):
        def __init__(self, message=""):
            log.frames("TestCase.Stop", inspect.getouterframes(inspect.currentframe(), context=1))
            super().__init__(message)

    class _Abort(Exception):
        def __init__(self, message=""):
            log.frames("TestCase.Abort", inspect.getouterframes(inspect.currentframe(), context=1))
            super().__init__(message)


class TestSuite:
    report = False
    loglevel = 1
    show_dashboard = True

    abort_on_fail = False
    abort_on_exception = True

    run_on_fail = None
    run_on_exception = None

    uid = None
    result_directory = TEST_RESULT_DIRECTORY
    admin = False
    winadmin = False
    reporter = None

    def __init__(self, title, description="", *args, **kwargs):
        """Runs a Test Suite.

        Args:
            title: Title of the test
            description: Optional description for the test

        A Test Suite runs one or more Test Cases.

        A Test Suite result is either PASSED, FAILED, or ABORTED.  If an unhandled
        exception occurs during the suite the result is ABORTED.  If not aborted, if any Test Case
        fails the result is FAILED, otherwise it is PASSED.

        The suite is run using the python with command.  This example runs a suite with one test case.

            .. code-block::

                with TestSuite("My test suite", "Very cool suite.") as suite:

                    with TestCase(suite, "My test", "Very cool test description") as test:

                        with TestStep(test, "My step", "Very cool step description") as step:
                            value1, value2 = get_my_values()
                            verify.my_requirement(step, value1)

        In the nvmetools package the test cases are included as a package called tests.

           .. code-block::

                from nvmetools import tests, TestSuite

                with TestSuite("Selftests", "Runs the short and exteself-test.") as suite:

                    tests.short_selftest(suite)
                    tests.extended_selftest(suite)

        If abort_on_fail is True the suite will stop when a test fails.  Note the test will complete
        before the test is stopped.  This example runs a test and enables stop on fail for the
        first step.

            .. code-block::

                with TestCase(suite, "My test", "Very cool test description") as test:

                    test.abort_on_fail = True

                    with TestStep(test, "My step", "Very cool step description") as step:

                        value1, value2 = get_my_values()
                        verify.my_requirement(step, value1))


        A test can be stopped using the stop() method.  This example stops a test and sets the result
        to PASSED or FAILED based on a custom variable.

            .. code-block::

                with TestCase(suite, "My test", "Very cool test description") as test:

                    with TestStep(test, "My step", "Very cool step description") as step:

                        value1, value2 = get_my_values()
                        if value1 == 32:
                            test.stop(force_fail=False)
                        else:
                            test.stop()


        Attributes:
            directory:      Working directory for step specific files
            abort_on_fail:   Aborts suite when a test fails, default is False
            loglevel:        Amount of detail to log, least is 0, most is 3

        """

        for item in kwargs.items():
            self.__setattr__(item[0], item[1])

        if self.admin and not is_admin():
            raise _NoAdmin()
        if platform.system() == "Windows" and self.winadmin and not is_windows_admin():
            raise _NoWinAdmin()

        description_lines = description.split("\n")
        self._description = description_lines[0]
        self.details = self._description

        if len(description_lines) > 2 and description_lines[1].strip() == "":
            second_paragraph = ""
            for line in description_lines[2:]:
                if line.strip() == "":
                    break
                second_paragraph += line.strip().replace("\n", "") + " "
            self.details = second_paragraph.rstrip()

        self._title = title
        self.tests = []
        self._start_counter = time.perf_counter()
        self.test_number = 0
        self.data = {}

        if self.uid is None:
            self.uid = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            time.sleep(1)
            self.directory = os.path.realpath(
                os.path.join(TEST_RESULT_DIRECTORY, title.lower().replace(" ", "_"), self.uid)
            )
        else:
            self.directory = os.path.realpath(os.path.join(TEST_RESULT_DIRECTORY, self.uid))

        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)
        os.makedirs(self.directory, exist_ok=False)

        self.state = {
            "title": title,
            "description": self._description,
            "details": self.details,
            "result": ABORTED,
            "flow": "",
            "complete": False,
            "start time": f"{datetime.datetime.now()}"[:-3],
            "end time": "",
            "end message": "",
            "duration (sec)": "",
            "duration": "",
            "directory": self.directory,
            "script version": __version__,
            "id": self.uid,
            "model": "N/A",
            "system": f"{platform.node()}",
            "location": "N/A",
            "summary": {
                "tests": {"total": 0, "pass": 0, "fail": 0, "skip": 0},
                "rqmts": {"total": 0, "pass": 0, "fail": 0},
                "verifications": {"total": 0, "pass": 0, "fail": 0},
            },
            "tests": [],
            "verifications": [],
            "rqmts": {},
            "data": {},
        }
        global log

        if self.loglevel == 0:
            log = start_logger(self.directory, logging.IMPORTANT, "console.log")
        elif self.loglevel == 1:
            log = start_logger(self.directory, logging.INFO, "console.log")
        elif self.loglevel == 2:
            log = start_logger(self.directory, logging.VERBOSE, "console.log")
        else:
            log = start_logger(self.directory, logging.DEBUG, "console.log")

        if hasattr(self, "volume") and not os.path.exists(self.volume):
            self.stop(f"Volume {self.volume} does not exist")

        results_file = os.path.join(self.directory, RESULTS_FILE)
        with open(results_file, "w", encoding="utf-8") as file_object:
            json.dump(self.state, file_object, ensure_ascii=False, indent=4)

    def __enter__(self):
        log.important("-" * 90, indent=False)
        log.important(f"TEST SUITE : {self.state['title']}", indent=False)
        log.important("-" * 90, indent=False)
        log.info(f"Description : {self.state['description']}", indent=False)
        log.important(f"Start Time  : {datetime.datetime.now()}", indent=False)
        log.important(f"Directory   : {self.directory}", indent=False)
        if self.loglevel == 0:
            log.important("")

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        duration_seconds = time.perf_counter() - self._start_counter
        self.state["end time"] = f"{datetime.datetime.now()}"[:-3]

        if "start_info" in self.data:
            self.state["model"] = self.data["start_info"]["parameters"]["Model"]
            self.state["location"] = f"NVMe {self.nvme}"

        self.state["data"] = self.data
        self.state["duration (sec)"] = f"{duration_seconds:.3f}"
        self.state["duration"] = as_duration(duration_seconds)

        skip_tests = sum(test["result"] is SKIPPED for test in self.state["tests"])
        fail_tests = sum(test["result"] is FAILED for test in self.state["tests"])
        pass_tests = sum(test["result"] is PASSED for test in self.state["tests"])
        abort_tests = sum(test["result"] is ABORTED for test in self.state["tests"])

        if (fail_tests + abort_tests) > 0:
            self.state["result"] = FAILED
        else:
            self.state["result"] = PASSED

        if exc_type is None:
            self.state["flow"] = COMPLETED

        elif exc_type is self._Stop:
            log.info("")
            log.info(f"STOP : TestSuite stop message '{exc_value}'", indent=False)
            self.state["flow"] = STOPPED

        elif exc_type is self._Abort:
            log.important("")
            log.important(f"TEST SUITE ABORTED : {exc_value}", indent=False)
            self.state["result"] = ABORTED
            self.state["flow"] = ABORTED

            self.state["end message"] = f"Test Suite aborted with message: {exc_value}"

        else:
            self.state["result"] = ABORTED
            self.state["flow"] = ABORTED

            self.state["end message"] = """Test aborted with below exception.  """

            log.info("")
            log.info("> EXCEPTION : Possible script error.", indent=False)
            log.info(">    ", indent=False)

            exception_lines = traceback.format_exception(
                type(exc_value), exc_value, exc_traceback, limit=-1, chain=False
            )[1:]

            for line in exception_lines:
                for each_line in line.split("\n"):
                    if len(each_line.strip().replace("\n", "")) > 0:
                        final_line = each_line.strip().replace("\n", "")
                        log.info(">    " + final_line, indent=False)
                        self.state["end message"] += f"<br>{final_line}"

            log.important(" ")
            log.important("TEST SUITE ABORTED : Exception occurred at TestSuite level", indent=False)

        self.update_summary()

        log.important("")
        log.important(f"End Time     : {self.state['end time'] }", indent=False)
        log.important(f"Duration     : {self.state['duration (sec)']} seconds", indent=False)
        log.info(
            f"Tests        : {self.state['summary']['tests']['total']} "
            + f"({self.state['summary']['tests']['pass']} passed, "
            + f"{self.state['summary']['tests']['fail']} failed, "
            + f"{self.state['summary']['tests']['skip']} skipped)",
            indent=False,
        )
        log.info(
            f"Verifications : {self.state['summary']['verifications']['total']} "
            + f"({self.state['summary']['verifications']['pass']} passed, "
            + f"{self.state['summary']['verifications']['fail']} failed)",
            indent=False,
        )

        log.important("-" * 90, indent=False)

        if self.state["result"] == PASSED:
            log.important("TEST SUITE PASSED", indent=False)
        else:
            log.important("TEST SUITE FAILED", indent=False)

        log.important("-" * 90, indent=False)

        results_file = os.path.join(self.directory, RESULTS_FILE)
        with open(results_file, "w", encoding="utf-8") as file_object:
            json.dump(self.state, file_object, ensure_ascii=False, indent=4)

        # create the reports, handle any exceptions

        try:
            if self.report:
                self.reporter(
                    results_directory=self.directory,
                    title=self._title,
                    description=self.details,
                    show_dashboard=self.show_dashboard,
                )
        except Exception:
            log.error("\n  Report creation failed with exception:\n")
            for line in traceback.format_exc(limit=-2, chain=False).split("\n"):
                log.error("     " + line)

        return True

    def get_drive_specification(self):
        """Get the drive specification file."""

        if "start_info" in self.state["data"]:
            filename = f"{self.state['data']['start_info']['parameters']['Model No Spaces']}.json"
        else:
            filename = "default.json"

        filepath = os.path.join(USER_INFO_DIRECTORY, filename)

        if not os.path.exists(filepath):
            filepath = os.path.join(DEFAULT_INFO_DIRECTORY, filename)

        if not os.path.exists(filepath):
            filepath = os.path.join(DEFAULT_INFO_DIRECTORY, "default.json")

        with open(filepath, "r") as file_object:
            self.device = json.load(file_object)

    def abort(self, message=""):
        """Abort the TestSuite.

        Aborts the suite when called.  The suite result is set to failed.
        """
        raise self._Abort(message)

    def stop(self, message=""):
        """Stop the TestSuite.

        Stops the suite when called.  The suite result is determined by the completed tests up to
        the point stop() is called.  If any test failed the result is failed, otherwise it is passed.
        """
        raise self._Stop(message)

    def update_summary(self):
        self.state = update_suite_summary(self.state)

    class _Stop(Exception):
        def __init__(self, message=""):
            log.frames("TestSuite.Stop", inspect.getouterframes(inspect.currentframe(), context=1))
            super().__init__(message)

    class _Abort(Exception):
        def __init__(self, message=""):
            log.frames("TestSuite.Abort", inspect.getouterframes(inspect.currentframe(), context=1))
            super().__init__(message)


def update_suite_summary(state):

    # clear summary

    state["summary"] = {
        "tests": {"total": 0, "pass": 0, "fail": 0, "skip": 0},
        "rqmts": {"total": 0, "pass": 0, "fail": 0},
        "verifications": {"total": 0, "pass": 0, "fail": 0},
    }
    state["verifications"] = []
    state["rqmts"] = {}

    # read tests and update

    state["summary"]["tests"]["total"] = len(state["tests"])
    state["summary"]["tests"]["pass"] = sum(test["result"] == PASSED for test in state["tests"])
    state["summary"]["tests"]["fail"] = sum(test["result"] == FAILED for test in state["tests"]) + sum(
        test["result"] == ABORTED for test in state["tests"]
    )
    state["summary"]["tests"]["skip"] = sum(test["result"] == SKIPPED for test in state["tests"])

    for test in state["tests"]:
        for step in test["steps"]:
            for verification in step["verifications"]:
                state["verifications"].append(verification)
                state["summary"]["verifications"]["total"] += 1

                if verification["title"] not in state["rqmts"]:
                    state["rqmts"][verification["title"]] = {"pass": 0, "fail": 0, "total": 0}

                state["rqmts"][verification["title"]]["total"] += 1

                if verification["result"] == PASSED:
                    state["summary"]["verifications"]["pass"] += 1
                    state["rqmts"][verification["title"]]["pass"] += 1
                else:
                    state["summary"]["verifications"]["fail"] += 1
                    state["rqmts"][verification["title"]]["fail"] += 1

    # update requirement summary

    state["summary"]["rqmts"]["total"] = len(state["rqmts"])
    for rqmt in state["rqmts"]:
        if state["rqmts"][rqmt]["fail"] == 0:
            state["summary"]["rqmts"]["pass"] += 1
        else:
            state["summary"]["rqmts"]["fail"] += 1

    # update result if not aborted

    if state["result"] != ABORTED:
        test_fails = sum(ver["result"] is FAILED for ver in state["tests"])
        test_fails += sum(ver["result"] is ABORTED for ver in state["tests"])

        if test_fails == 0:
            state["result"] = PASSED
        else:
            state["result"] = FAILED

    return state


def update_suite_files(directory=".", reporter=None):
    """Update Test Suite after results files updated.

    This function updates the Test Suite after a user has manually updated the test results.
    This allows the user to enter manual results and then easily create a new dashboard and
    PDF report.

    To manually update a test result edit the results.json file in the test directory.  In
    the ["steps"] section find the step and verification to change.  Change the "result"
    parameter to "PASSED" or "FAILED".  Recommend completing the "reviewer" parameter and
    the "note" parameter with the reason for the change.

    This function updates the following files in a Test Suite:
        results.json
        dashboard.html
        report.pdf
        <test #>   results.json

    Args:
        description: Directory containing Test Suite to update
    """

    full_directory = os.path.abspath(directory)
    list_of_test_results = glob.glob(f"{full_directory}/*/{RESULTS_FILE}")
    suite_results_file = os.path.join(full_directory, RESULTS_FILE)

    with open(suite_results_file, "r") as file_object:
        suite_results = json.load(file_object)

    log = start_logger(full_directory, logging.IMPORTANT, "update_console.log")

    log.important("-" * 90, indent=False)
    log.important(f"UPDATE TEST SUITE : {suite_results['title']}", indent=False)
    log.important("-" * 90, indent=False)
    log.info(f"Description : {suite_results['description']}", indent=False)
    log.important(f"Directory   : {full_directory}", indent=False)
    log.important("")

    suite_results["tests"] = []

    for result_file in list_of_test_results:
        with open(result_file, "r") as file_object:
            results = json.load(file_object)

        new_results = update_test_summary(results)
        suite_results["tests"].append(new_results)

        with open(result_file, "w") as file_object:
            json.dump(new_results, file_object, ensure_ascii=False, indent=4)

    suite_results = update_suite_summary(suite_results)

    with open(suite_results_file, "w") as file_object:
        json.dump(suite_results, file_object, ensure_ascii=False, indent=4)

    if reporter is not None:
        reporter(
            results_directory=full_directory,
            title=suite_results["title"],
            description=suite_results["details"],
        )


def update_test_summary(state):
    """Update Test Case summary after results files updated."""

    # clear summary

    state["summary"] = {
        "steps": {"total": 0, "pass": 0, "fail": 0},
        "rqmts": {"total": 0, "pass": 0, "fail": 0},
        "verifications": {"total": 0, "pass": 0, "fail": 0},
    }
    state["rqmts"] = {}
    state["verifications"] = []

    # read steps and update

    for step in state["steps"]:
        step_fails = 0

        state["summary"]["steps"]["total"] += 1

        for verification in step["verifications"]:
            state["verifications"].append(verification)
            state["summary"]["verifications"]["total"] += 1

            if verification["title"] not in state["rqmts"]:
                state["rqmts"][verification["title"]] = {"pass": 0, "fail": 0, "total": 0}
                state["summary"]["rqmts"]["total"] += 1

            if verification["result"] == PASSED:
                state["summary"]["verifications"]["pass"] += 1
                state["rqmts"][verification["title"]]["pass"] += 1
            else:
                state["summary"]["verifications"]["fail"] += 1
                state["rqmts"][verification["title"]]["fail"] += 1
                step_fails += 1

        if step["result"] == ABORTED:  # leave the same
            pass
        elif step_fails == 0:
            state["summary"]["steps"]["pass"] += 1
            step["result"] = PASSED
        else:
            state["summary"]["steps"]["fail"] += 1
            step["result"] = FAILED

    # update requirement summary

    state["summary"]["rqmts"]["total"] = len(state["rqmts"])
    for rqmt in state["rqmts"]:
        if state["rqmts"][rqmt]["fail"] == 0:
            state["summary"]["rqmts"]["pass"] += 1
        else:
            state["summary"]["rqmts"]["fail"] += 1

    # update result unless skipped or aborted

    if state["result"] != SKIPPED and state["result"] != ABORTED:
        failed_steps = sum(step["result"] is not PASSED for step in state["steps"])
        if failed_steps == 0:
            state["result"] = PASSED
        else:
            state["result"] = FAILED

    return state


def verification(rqmt_id, step, title, verified, value):
    """Verification of a requirement.

    Args:
        rqmt_id: Unique integer ID that identifies the requirement
        step:  The parent TestStep instance
        title: Title of the requirement
        verified: True if the requirement passes verification
        value:  Value to be reported as the result

    This function does not return a value but updates the test step and test case with the
    result of the verification.

    The result is PASSED if verified is True, FAILED if verified is False, and NONE if verified
    is None.  The NONE results allows the verification to be determined later.  This can be useful
    for automation that requires manual review.

    This function is wrapped in a parent function that defines the requirement to verify.
    For example, this parent function verifies there are no prior self-test failures.

    .. code-block::

        def no_prior_selftest_failures(step, info):

            value = int(info.parameters["Number Of Failed Self-Tests"])

            verification(
                rqmt_id=12,
                step=step,
                title="Prior self-test failures shall be 0",
                verified=(value == 0),
                value=value,
            )

    The parent functions are included in a python package that can be imported as rqmts.  This
    code shows how to use the verification defined above.

    .. code-block::

        from nvmetools import rqmts, Info, TestStep

        with TestStep("Selftest failures", "Verify there are no prior selftest failures") as step:
            info = Info(test.suite.nvme, directory=step.directory)
            rqmts.no_prior_selftest_failures(step, info)
    """
    frames = inspect.getouterframes(inspect.currentframe(), context=1)
    debug = f"Verification {frames[1].function} called from {frames[2].filename} line {frames[2].lineno}"

    if step.suite.loglevel == 2 and len(step.state["verifications"]) == 0:
        log.verbose("")
    elif step.suite.loglevel == 1 and step.test.state["summary"]["verifications"]["fail"] == 0 and (not verified):
        log.info("")
    else:
        log.debug("")
    log.debug(debug)

    if not isinstance(step, TestStep):
        raise _InvalidStep(debug)

    step.suite.state["summary"]["verifications"]["total"] += 1
    ver_number = step.suite.state["summary"]["verifications"]["total"]

    if verified is None:
        result = RQMT_SKIPPED
        log.info(f"----> SKIP #{ver_number} : {title} [value: {value}]", indent=False)
    elif verified:
        result = RQMT_PASSED
        log.verbose(f"PASS #{ver_number} : {title} [value: {value}]")
    else:
        result = RQMT_FAILED
        log.info(f"----> FAIL #{ver_number} : {title} [value: {value}]", indent=False)

    state = {
        "number": ver_number,
        "id": rqmt_id,
        "title": title,
        "result": result,
        "value": value,
        "time": f"{datetime.datetime.now()}",
        "reviewer": "",
        "note": "",
        "test": step.test.state["title"],
        "test number": step.test.state["number"],
    }
    step.state["verifications"].append(state)
    step.test.update_summary()

    if result == RQMT_FAILED and step.test.abort_on_fail:
        step.test.abort(f"Verification #{ver_number} failed with Abort On Fail enabled : {title}")
