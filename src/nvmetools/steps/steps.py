# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Test Steps for NVMe solid state drives (SSD).

All NVMe Test Steps are combined into this single python package (nvmetools.steps) so they can
easily be imported and run as shown here.

    .. code-block::

        from nvmetools import steps

        with TestSuite("Example suite") as suite:
            with TestCase(suite, "Example test") as test:

                start_info = steps.test_start_info(test)

                # Do some stuff

                steps.test_end_info(test, start_info)

"""
import os
import time

from nvmetools import Info, InfoSamples, TestStep, log, rqmts
from nvmetools.apps.fio import FioFiles
from nvmetools.support.conversions import BYTES_IN_GB


def test_start_info(test):
    """Read and verify drive information at start of test case.

    Args:
        test: Parent TestCase instance

    Returns:
        Instance of Info class with NVMe information

    """
    with TestStep(
        test, "Test start info", "Read test start info and verify drive not in error state.", stop_on_fail=True
    ) as step:
        start_info = Info(test.suite.nvme, directory=step.directory)
        rqmts.no_critical_warnings(step, start_info)

    return start_info


def test_end_info(test, start_info):
    """Read and verify drive information at end of test case.

    Args:
        test: Parent TestCase instance
        start_info:  NVMe info at start of test as Info instance

    """
    with TestStep(
        test,
        "Test end info",
        "Read test end info and verify no errors or unexpected changes occurred during test.",
    ) as step:
        end_info = Info(test.suite.nvme, directory=step.directory, compare_info=start_info)

        rqmts.no_critical_warnings(step, end_info)
        rqmts.no_errorcount_change(step, end_info)
        rqmts.no_static_parameter_changes(step, end_info)
        rqmts.no_counter_parameter_decrements(step, end_info)

    return end_info


def get_fio_big_file(test, disk_size):
    """Get or create a big fio data file for IO reads and writes.

    Args:
        test: Parent TestCase instance
        disk_size:  Size of disk in bytes

    """
    with TestStep(
        test,
        "Get fio file",
        "Get or create big file without verification headers.",
        stop_on_fail=True,
    ) as step:
        fio_files = FioFiles(step.directory, test.suite.volume)
        fio_file = fio_files.create(big=True, verify=False, wait_sec=180, disk_size=disk_size)

        test.data["file size"] = fio_file.file_size
        test.data["file size gb"] = fio_file.file_size / BYTES_IN_GB
        test.data["fio filepath"] = fio_file.os_filepath
        test.data["file ratio"] = float(fio_file.file_size / float(disk_size)) * 100.0
    return fio_file


def get_fio_performance_file(test):
    """Get or create a fio data file for IO reads and writes without verify.

    Args:
        test: Parent TestCase instance

    """
    with TestStep(
        test,
        "Get fio file",
        "Get or create small file without verification headers.",
        stop_on_fail=True,
    ) as step:
        fio_files = FioFiles(step.directory, test.suite.volume)
        fio_file = fio_files.create(big=False, verify=False, wait_sec=180)

        test.data["file size"] = fio_file.file_size
        test.data["file size gb"] = fio_file.file_size / BYTES_IN_GB
        test.data["fio filepath"] = fio_file.os_filepath

    return fio_file


def get_fio_small_file(test):
    """Get or create a fio data file for IO reads and writes with verify.

    Args:
        test: Parent TestCase instance

    """
    with TestStep(
        test,
        "Get fio file",
        "Get or create small file with verification headers.",
        stop_on_fail=True,
    ) as step:
        fio_files = FioFiles(step.directory, test.suite.volume)
        fio_file = fio_files.create(big=False, verify=True, wait_sec=180)

        test.data["file size"] = fio_file.file_size
        test.data["file size gb"] = fio_file.file_size / BYTES_IN_GB
        test.data["fio filepath"] = fio_file.os_filepath

    return fio_file


def get_fio_stress_file(test, disk_size):
    """Get or create a fio data file for IO reads and writes with verify.

    Args:
        test: Parent TestCase instance
        disk_size:  Size of disk in bytes

    """
    with TestStep(test, "Get fio file", "Use big file if exists, else get or create a small file.") as step:

        step.stop_on_fail = True

        fio_files = FioFiles(step.directory, test.suite.volume)
        if os.path.exists(fio_files.bigfile_path):
            fio_file = fio_files.create(big=True, disk_size=float(disk_size))
        else:
            fio_file = fio_files.create(big=False, verify=True)

        test.data["file size"] = fio_file.file_size
        test.data["file size gb"] = fio_file.file_size / BYTES_IN_GB
        test.data["fio filepath"] = fio_file.os_filepath
        test.data["file ratio"] = float(fio_file.file_size / float(disk_size)) * 100.0
    return fio_file


def start_info_samples(test, cmd_file="state", delay_sec=10):
    """Start sampling SMART and power state info every second.

    Args:
        test: Parent TestCase instance
        cmd_file: cmd file to use for reading samples
        delay_sec: Seconds to delay before returning, guarantees some sample
    """
    with TestStep(test, "Sample info", "Start sampling SMART and power state info every second.") as step:
        info_samples = InfoSamples(
            test.suite.nvme,
            directory=step.directory,
            wait=False,
            samples=100000,
            interval=1000,
            cmd_file=cmd_file,
        )
        log.debug(f"Waiting {delay_sec} seconds to start IO")
        time.sleep(delay_sec)

    return info_samples


def stop_info_samples(test, info_samples, delay_sec=10):
    """Stop sampling SMART and power state info every second.

    Args:
        test: Parent TestCase instance
        delay_sec: Seconds to delay before stopping, guarantees some samples
    """
    with TestStep(test, "Verify samples", "Stop sampling and verify no sample errors") as step:
        info_samples.stop()
        rqmts.no_counter_parameter_decrements(step, info_samples)
        rqmts.no_errorcount_change(step, info_samples)


def wait_for_idle(test, wait_sec=180):
    """Wait for drive to return to idle.

    Args:
        test: Parent TestCase instance
        wait_sec: Number of seconds to waut

    """
    with TestStep(test, "Idle wait", "Wait for idle temperature and garbage collection") as step:

        idle_info_samples = InfoSamples(
            nvme=test.suite.nvme,
            samples=wait_sec,
            interval=1000,
            cmd_file="logpage02",
            directory=step.directory,
        )
        rqmts.admin_commands_pass(step, idle_info_samples)
        rqmts.no_static_parameter_changes(step, idle_info_samples)
        rqmts.no_counter_parameter_decrements(step, idle_info_samples)
        rqmts.admin_command_avg_latency(step, idle_info_samples, test.suite.device["Average Admin Cmd Limit mS"])
        rqmts.admin_command_max_latency(step, idle_info_samples, test.suite.device["Maximum Admin Cmd Limit mS"])
