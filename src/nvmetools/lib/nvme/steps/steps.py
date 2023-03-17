# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Test Steps for NVMe solid state drives (SSD).

All NVMe Test Steps are combined into this single python package so they can
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

import nvmetools.lib.nvme.requirements as rqmts
from nvmetools.apps.fio import FioFiles
from nvmetools.support.conversions import BYTES_IN_GB
from nvmetools.support.framework import TestStep
from nvmetools.support.info import Info, InfoSamples
from nvmetools.support.log import log

import psutil


def test_start_info(test):
    """Read and verify drive information at start of test case.

    Args:
        test: Parent TestCase instance

    Returns:
        Instance of Info class with NVMe information

    """
    with TestStep(
        test, "Test start info", "Read test start info and verify drive not in error state."
    ) as step:
        start_info = Info(test.suite.nvme, directory=step.directory)
        rqmts.available_spare_above_threshold(step, start_info)
        rqmts.nvm_system_reliable(step, start_info)
        rqmts.persistent_memory_reliable(step, start_info)
        rqmts.media_not_readonly(step, start_info)
        rqmts.memory_backup_not_failed(step, start_info)
        rqmts.no_media_errors(step, start_info)

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

        rqmts.available_spare_above_threshold(step, start_info)
        rqmts.nvm_system_reliable(step, start_info)
        rqmts.persistent_memory_reliable(step, start_info)
        rqmts.media_not_readonly(step, start_info)
        rqmts.memory_backup_not_failed(step, start_info)
        rqmts.no_media_errors(step, start_info)

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


def verify_empty_drive(test, volume, info):

    disk_size = float(info.parameters["Size"].split()[0])
    free_space = psutil.disk_usage(volume).free

    with TestStep(test, "Empty drive", "Verify the drive free space.") as step:
        rqmts.verify_empty_drive(step, free_space, disk_size)


def verify_full_drive(test, volume, info):

    disk_size = float(info.parameters["Size"].split()[0])
    free_space = psutil.disk_usage(volume).free

    with TestStep(test, "Full drive", "Verify the drive is full.") as step:
        rqmts.verify_full_drive(step, free_space, disk_size)


def start_info_samples(test, cmd_file="state", delay_sec=10, interval_ms=1000):
    """Start sampling SMART and power state info every second.

    Args:
        test: Parent TestCase instance
        cmd_file: cmd file to use for reading samples
        delay_sec: Seconds to delay before returning, guarantees some sample
    """
    with TestStep(
        test, "Sample info", f"Start sampling SMART and power state info every {interval_ms/1000:0.1f} seconds."
    ) as step:
        info_samples = InfoSamples(
            test.suite.nvme,
            directory=step.directory,
            wait=False,
            samples=100000,
            interval=interval_ms,
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
        rqmts.no_errors_reading_samples(step, info_samples)


def idle_wait(test, wait_sec=180):
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
