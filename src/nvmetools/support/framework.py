# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""This module provides a framework for testing NVMe devices.

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
    -  Detailed report

Because this framework is based on python and command line usage it can easily be integrated into
existing automation frameworks, test databases such as TestRail, and log storage servers.

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


from nvmetools import DEFAULT_INFO_DIRECTORY, TEST_SUITE_DIRECTORY, USER_INFO_DIRECTORY, __version__
from nvmetools.apps.nvmecmd import check_nvmecmd_permissions
from nvmetools.support.conversions import as_duration, is_admin
from nvmetools.support.log import start_logger
from nvmetools.support.report import create_reports

SKIPPED = "SKIPPED"
PASSED = "PASSED"
FAILED = "FAILED"
ABORTED = "ABORTED"
STARTED = "STARTED"

RESULTS_FILE = "result.json"


class TestStep:
    stop_on_fail = False
    __force_fail = False

    def __init__(self, test, title, description="", stop_on_fail=False):
        """Runs a Test Step.

        Args:
            test: Parent TestCase instance running the step
            title: Title of the step
            description: Optional description for the step

        A Test Step is run within a Test Case which is run within a Test Suite.  A Test Step runs
        any number of requirement verifications, including zero.

        A Test Step result is either PASSED or FAILED.  If no verifications failed the Test Step
        result is PASSED, otherwise it is FAILED.  The one exception if the stop() method is called,
        see below for details.

        The step is run using the python with command.  This example runs a step with two
        verifications.  If either verification fails the step result is FAILED.

            .. code-block::

                with TestStep(test, "My step", "Very cool step description") as step:

                    value1, value2 = get_my_values()

                    verify.my_requirement(step, value1)
                    verify.my_second_requirement(step, value2)


        If stop_on_fail is True the step will stop when a verification fails.  This example runs a
        test step and enables stop on fail for the first verification.

            .. code-block::

                with TestStep(test, "My step", "Very cool step description") as step:

                    value1, value2 = get_my_values()

                    step.stop_on_fail = True
                    verify.my_requirement(step, value1)

                    step.stop_on_fail = False
                    verify.my_second_requirement(step, value2)


        A step can be stopped using the stop() method.  This example stops a step and sets the result
        to PASSED or FAILED based on a custom variable.

            .. code-block::

                with TestStep(test, "My step", "Very cool step description") as step:

                    value1, value2 = get_my_values()

                    if value1 == 32:
                        step.stop(force_fail=False)
                    else:
                        step.stop()

        Attributes:
            test:            Parent TestCase instance running the test step
            suite:           Grandparent TestSuite instance running the test
            step_number:     Step number within the test
            directory:       Working directory for step specific files
            stop_on_fail:    Stops step on a failed verification, default is False

        """
        self._title = title
        self.stop_on_fail = stop_on_fail
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
            "force fail": False,
            "start time": f"{datetime.datetime.now()}"[:-3],
            "end time": "",
            "duration (sec)": "",
            "duration": "",
            "directory": self.directory,
            "directory name": directory_name,
            "verifications": [],
        }

    def __enter__(self):
        log.frames("TestStep", inspect.getouterframes(inspect.currentframe(), context=1))
        log.verbose(f"Step {self.test.step_number}: {self._title}")
        log.verbose("")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        duration_seconds = time.perf_counter() - self._start_counter
        self.state["end time"] = f"{datetime.datetime.now()}"[:-3]
        self.state["description"] = self._description
        self.state["duration (sec)"] = f"{duration_seconds:.3f}"
        self.state["duration"] = as_duration(duration_seconds)

        pass_vers = sum(ver["result"] is PASSED for ver in self.state["verifications"])
        fail_vers = sum(ver["result"] is not PASSED for ver in self.state["verifications"])

        if self.suite.loglevel > 1:
            if fail_vers != 0:
                log.important("")
            elif pass_vers != 0:
                log.verbose("")

        # End normally

        if exc_type is None:
            if self.__force_fail or fail_vers > 0:
                self.state["result"] = FAILED
            else:
                self.state["result"] = PASSED
            self.test.state["steps"].append(self.state)

        # Stopped because of framework exception, determine pass/fail and then forward exception

        elif hasattr(exc_value, "nvme_framework_exception"):
            if self.__force_fail or fail_vers > 0:
                self.state["result"] = FAILED
            else:
                self.state["result"] = PASSED
            self.test.state["steps"].append(self.state)

            # if step stop then it was handled, else send to parent test case
            if exc_type is not self.__Stop:
                return False

        # Stopped with unknown exception, forward to parent test case

        else:
            self.state["result"] = ABORTED
            self.test.state["steps"].append(self.state)
            return False

        if self.state["result"] == FAILED and self.test.stop_on_fail:
            self.test.stop()

        return True

    class __Stop(Exception):
        nvme_framework_exception = True

        def __init__(self, message=""):
            log.frames("TestStep.Stop", inspect.getouterframes(inspect.currentframe(), context=1))
            log.info(f"----> STEP STOP : {message}", indent=False)
            log.info("")
            super().__init__("TestStep.Stop")

    def stop(self, message="", force_fail=True):
        """Stop the TestStep.

        Stops the step when called.  By default will force the step to fail.  If force_fail=False
        the step result is determined by the completed verifications up to the point stop() is
        called.  If any verification failed the step result is failed, otherwise it is passed.

        Args:
            force_fail: Forces step to fail if True

        """
        self.__force_fail = force_fail
        self.state["force fail"] = force_fail
        raise self.__Stop(message)


class TestCase:
    stop_on_fail = False
    __force_fail = False

    def __init__(self, suite, title, description="", stop_on_fail=False):
        """Runs a Test Case.

        Args:
            suite: Parent TestSuite instance running the test
            title: Title of the test
            description: Optional description for the test

        A Test Case which is run within a Test Suite.  A Test Case runs one or more Test Steps.

        A Test Case result is either PASSED, FAILED, ABORTED, or SKIPPED.  If an unhandled
        exception occurs during the test the result is ABORTED.  If the skip() method is
        called the result is SKIPPED.  If not skipped or aborted, if any Test Step fails the result
        is FAILED, otherwise it is PASSED.

        The test is run using the python with command.  This example runs a test with one test step.

            .. code-block::

                with TestCase(suite, "My test", "Very cool test description") as test:

                    with TestStep(test, "My step", "Very cool step description") as step:
                        value1, value2 = get_my_values()
                        verify.my_requirement(step, value1)


        If stop_on_fail is True the test will stop when a step fails.  Note the step will complete
        before the test is stopped.  This example runs a test and enables stop on fail for the
        first step.

            .. code-block::

                with TestCase(suite, "My test", "Very cool test description") as test:

                    test.stop_on_fail = True

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


        A test can be skipped using the skip() method.  This example skips a test if the testable
        feature is not supported.

            .. code-block::

                with TestCase(suite, "My test", "Very cool test description") as test:

                    with TestStep(test, "Feature support", "Verifies feature is supported") as step:

                        feature_supported = get_feature_support()
                        if not feature_supported:
                            test.skip()

        Attributes:
            suite:          Parent TestSuite instance running the test
            test_number:     Test number within the test suite
            directory:       Working directory for step specific files
            stop_on_fail:    Stops step on a failed verification, default is False

        """
        self.data = {}
        self.suite = suite
        self.stop_on_fail = stop_on_fail
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
            "force fail": False,
            "start time": f"{datetime.datetime.now()}"[:-3],
            "end time": "",
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
        log.frames("TestCase", inspect.getouterframes(inspect.currentframe(), context=1))
        log.header(f"TEST {self.suite.test_number} : {self.state['title']}", 45)
        log.info(f"Description : {self.state['description']}")
        log.verbose(f"Start Time  : {self.state['start time']}")
        log.info("")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        duration_seconds = time.perf_counter() - self._start_counter
        self.state["end time"] = f"{datetime.datetime.now()}"[:-3]
        self.state["description"] = self._description
        self.state["duration (sec)"] = f"{duration_seconds:.3f}"
        self.state["duration"] = as_duration(duration_seconds)
        self.state["data"] = self.data

        fail_steps = sum(step["result"] is not PASSED for step in self.state["steps"])

        if exc_type is None or hasattr(exc_value, "nvme_framework_exception"):

            if exc_type is self.__Skip:
                self.state["result"] = SKIPPED
            elif self.__force_fail or fail_steps > 0:
                self.state["result"] = FAILED
            else:
                self.state["result"] = PASSED
        else:
            self.state["result"] = ABORTED

        self.update_summary()
        self.suite.state["tests"].append(self.state)

        results_file = os.path.join(self.directory, RESULTS_FILE)
        with open(results_file, "w", encoding="utf-8") as file_object:
            json.dump(self.state, file_object, ensure_ascii=False, indent=4)

        if self.suite.loglevel == 1:
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
                log.important(f"     PASS : TEST {self.suite.test_number} : {self.state['title']}", indent=False)
            else:
                log.info("TEST PASSED")
                log.info("")
        elif self.state["result"] == SKIPPED:
            if self.suite.loglevel == 0:
                log.important(f" --> SKIP : TEST {self.suite.test_number} : {self.state['title']}", indent=False)
            else:
                log.info("----> TEST SKIPPED", indent=False)
                log.info("")
        elif self.state["result"] == ABORTED:
            if exc_type is KeyboardInterrupt:
                log.error(" ----> TEST ABORTED BY CTRL-C\n\n")
                self.suite.stop()
            else:
                log.exception(" ----> TEST ABORTED WITH BELOW EXCEPTION\n\n")
                log.error(" ")
        else:
            if self.suite.loglevel == 0:
                log.important(f" --> FAIL : TEST {self.suite.test_number} : {self.state['title']}", indent=False)
            else:
                log.info("----> TEST FAILED", indent=False)
                log.info("")

        if (
            exc_type is not self.__Stop
            and exc_type is not self.__Skip
            and hasattr(exc_value, "nvme_framework_exception")
        ):
            return False

        if self.state["result"] == FAILED and self.suite.stop_on_fail:
            self.suite.stop()

        return True

    def skip(self, message=""):
        """Skip the TestCase.

        Skips the test when called.
        """
        raise self.__Skip(message)

    def stop(self, message="", force_fail=True):
        """Stop the TestCase.

        Stops the test when called.  By default will force the test to fail.  If force_fail=False
        the test result is determined by the completed steps up to the point stop() is
        called.  If any step failed the test result is failed, otherwise it is passed.

        Args:
            force_fail: Forces test to fail if True

        """
        self.__force_fail = force_fail
        self.state["force fail"] = force_fail

        raise self.__Stop(message)

    def update_summary(self):
        self.state = update_test_summary(self.state)

    class __Skip(Exception):
        nvme_framework_exception = True

        def __init__(self, message=""):
            log.frames("TestCase.Skip", inspect.getouterframes(inspect.currentframe(), context=1))
            log.info(f"----> TEST SKIP : {message}", indent=False)
            log.info("")
            super().__init__("TestCase.Skip")

    class __Stop(Exception):
        nvme_framework_exception = True

        def __init__(self, message=""):
            log.frames("TestCase.Stop", inspect.getouterframes(inspect.currentframe(), context=1))
            log.info(f"----> TEST STOP : {message}", indent=False)
            log.info("")
            super().__init__("TestCase.Stop")


class TestSuite:
    create_reports = True
    loglevel = 1
    show_dashboard = True
    stop_on_fail = False
    uid = None

    __force_fail = False

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




        If stop_on_fail is True the test will stop when a step fails.  Note the step will complete
        before the test is stopped.  This example runs a test and enables stop on fail for the
        first step.

            .. code-block::

                with TestCase(suite, "My test", "Very cool test description") as test:

                    test.stop_on_fail = True

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
            stop_on_fail:    Stops step on a failed verification, default is False
            loglevel:        Amount of detail to log, least is 0, most is 3

        """

        for item in kwargs.items():
            self.__setattr__(item[0], item[1])

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
            os.path.join(TEST_SUITE_DIRECTORY, title.lower().replace(" ", "_"), self.uid)
        )
        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)
        os.makedirs(self.directory, exist_ok=False)

        self.state = {
            "title": title,
            "description": self._description,
            "details": self.details,
            "result": ABORTED,
            "force fail": False,
            "complete": False,
            "start time": f"{datetime.datetime.now()}"[:-3],
            "end time": "",
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

        check_nvmecmd_permissions()
        self.get_drive_specification()
        results_file = os.path.join(self.directory, RESULTS_FILE)
        with open(results_file, "w", encoding="utf-8") as file_object:
            json.dump(self.state, file_object, ensure_ascii=False, indent=4)

    def __enter__(self):
        log.frames("TestSuite", inspect.getouterframes(inspect.currentframe(), context=1), indent=False)
        log.important(" " + "-" * 90, indent=False)
        log.important(f" TEST SUITE : {self.state['title']}", indent=False)
        log.important(" " + "-" * 90, indent=False)
        log.info(f" Description : {self.state['description']}", indent=False)
        log.important(f" Start Time  : {datetime.datetime.now()}", indent=False)
        log.important(f" Directory   : {self.directory}", indent=False)
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

        fail_tests = sum(test["result"] is not PASSED for test in self.state["tests"])
        aborted_tests = sum(test["result"] is ABORTED for test in self.state["tests"])

        if exc_type is None or exc_type is self.__Stop:
            if aborted_tests == 0:
                self.state["complete"] = True

            if self.__force_fail or fail_tests > 0:
                self.state["result"] = FAILED
            else:
                self.state["result"] = PASSED

        else:
            log.exception(" ----> TEST SUITE ABORTED WITH BELOW EXCEPTION\n\n")
            log.error(" ")
            self.state["result"] = ABORTED

        self.update_summary()

        if self.loglevel == 0:
            log.important("")

        log.important(f" End Time     : {self.state['end time'] }", indent=False)
        log.important(f" Duration     : {self.state['duration (sec)']} seconds", indent=False)
        log.info(
            f" Tests        : {self.state['summary']['tests']['total']} "
            + f"({self.state['summary']['tests']['pass']} passed, "
            + f"{self.state['summary']['tests']['fail']} failed)",
            indent=False,
        )
        log.info(
            f" Verifications : {self.state['summary']['verifications']['total']} "
            + f"({self.state['summary']['verifications']['pass']} passed, "
            + f"{self.state['summary']['verifications']['fail']} failed)",
            indent=False,
        )
        log.important(" " + "-" * 90, indent=False)

        if self.state["result"] == PASSED:
            log.important(" TEST SUITE PASSED", indent=False)
        else:
            log.important(" TEST SUITE FAILED", indent=False)

        log.important(" " + "-" * 90, indent=False)

        results_file = os.path.join(self.directory, RESULTS_FILE)
        with open(results_file, "w", encoding="utf-8") as file_object:
            json.dump(self.state, file_object, ensure_ascii=False, indent=4)

        if self.create_reports:
            create_reports(
                results_directory=self.directory,
                title=self._title,
                description=self.details,
                show_dashboard=self.show_dashboard,
            )
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

    def stop(self, message="", force_fail=True):
        """Stop the TestSuite.

        Stops the suite when called.  By default will force the suite to fail.  If force_fail=False
        the suite result is determined by the completed tests up to the point stop() is
        called.  If any test failed the result is failed, otherwise it is passed.

        Args:
            force_fail: Forces suite to fail if True

        """
        self.__force_fail = force_fail
        self.state["force fail"] = force_fail
        raise self.__Stop(message)

    def update_summary(self):
        self.state = update_suite_summary(self.state)

    class __Stop(Exception):
        nvme_framework_exception = True

        def __init__(self, message=""):
            log.frames("TestSuite.Stop", inspect.getouterframes(inspect.currentframe(), context=1))
            log.info(f"----> TEST SUITE STOP : {message}", indent=False)
            log.info("")
            super().__init__("TestSuite.Stop")


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
    state["summary"]["tests"]["fail"] = sum(test["result"] == FAILED for test in state["tests"])
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
        test_fails = sum(ver["result"] is not PASSED for ver in state["tests"])
        if test_fails == 0 and not state["force fail"]:
            state["result"] = PASSED
        else:
            state["result"] = FAILED

    return state


def update_suite_files(directory="."):
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

    log.important(" " + "-" * 90, indent=False)
    log.important(f" UPDATE TEST SUITE : {suite_results['title']}", indent=False)
    log.important(" " + "-" * 90, indent=False)
    log.info(f" Description : {suite_results['description']}", indent=False)
    log.important(f" Directory   : {full_directory}", indent=False)
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

    create_reports(
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

        if step_fails == 0 and not step["force fail"]:
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
        if failed_steps == 0 and not state["force fail"]:
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

    Verification is True if a requirement is met and False if not.  For example, the
    verification of requirement 'Media and Integrity Errors shall be 0' is True if there
    are no errors and False if there are errors.

    This function does not return a value but updates the test step and test case with the
    result of the verification.  If step stop_on_fail is True and the verification fails
    step.stop() is called.

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
    log.debug(f"  Verification {frames[1].function} called from {frames[2].filename} line {frames[2].lineno}")

    # must update verification number in test suite directly

    step.suite.state["summary"]["verifications"]["total"] += 1
    ver_number = step.suite.state["summary"]["verifications"]["total"]

    if verified:
        log.verbose(f"  PASS #{ver_number} : {title} [value: {value}]")
    else:
        log.info(f"------> FAIL #{ver_number} : {title} [value: {value}]", indent=False)

    state = {
        "number": ver_number,
        "id": rqmt_id,
        "title": title,
        "result": PASSED if verified else FAILED,
        "value": value,
        "time": f"{datetime.datetime.now()}",
        "reviewer": "",
        "note": "",
        "test": step.test.state["title"],
        "test number": step.test.state["number"],
    }
    step.state["verifications"].append(state)
    step.test.update_summary()

    if step.stop_on_fail and not verified:
        step.stop()
