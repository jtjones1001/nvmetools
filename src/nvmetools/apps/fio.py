# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
r"""Define functions for using fio utility.

https://github.com/axboe/fio
https://fio.readthedocs.io/en/latest/fio_doc.html

For windows must be installed in \Program Files\fio\fio.exe
For linux must be installed in /usr/bin/fio

Note: For direct IO units always appear to be power-2

Recommended args for verify:

    "--verify=crc32c",
    "--verify_dump=1",
    "--verify_state_save=0",
    "--verify_async=2",
    "--continue_on_error=verify",

Recommended default args:

    f"--ioengine={FIO_ASYNC_IO}",
    "--direct=1",
    "--numjobs=1",
    "--thread",
    "--output-format=json+",
    f"--filename={fio_target_file}",

Recommended args for logging:

    "--write_lat_log=latency",
        or
    "--write_lat_log=bandwidth",
    "--log_avg_ms=200",
"""
import csv
import json
import os
import platform
import time

from nvmetools.support.conversions import BYTES_IN_GIB, KIB_TO_GB, NS_IN_MS, NS_IN_US
from nvmetools.support.log import log
from nvmetools.support.process import RunProcess

import psutil

FIO_TRIM_IOS = 16
FIO_DELAY_IOS = 16

FIO_BIG_FILE = "fio_big_file.bin"
FIO_VERIFY_FILE = "fio_verify.bin"
FIO_PERFORMANCE_FILE = "fio_performance.bin"


BIG_FILE_SIZE = 0.95
SMALL_FILE_SIZE = 1024 * 1024 * 1024

if "Windows" == platform.system():
    FIO_EXEC = r"\Program Files\fio\fio.exe"
    FIO_ASYNC_IO = "windowsaio"
else:
    FIO_EXEC = "/usr/bin/fio"
    FIO_ASYNC_IO = "libaio"


class _FioMissing(Exception):
    def __init__(self, fio_exec):
        self.code = 60
        self.nvmetools = True
        error_msg = " fio utility could not be found.\n\n"
        error_msg += f" Expected fio utility here: {FIO_EXEC}\n\n"
        error_msg += "    Install the fio utility to above location.\n"
        error_msg += "    fio project:  https://github.com/axboe/fio\n"
        super().__init__(error_msg)


class _FioBadJson(Exception):
    def __init__(self, json_exception):
        self.code = 61
        self.nvmetools = True
        super().__init__(" failed parsing fio JSON file.")


class FioNoSpace(Exception):
    def __init__(self, message=""):
        self.code = 62
        self.nvmetools = True
        super().__init__(message)


class RunFio:
    """Run IO reads and writes using fio utility."""

    FIO_DELAY_IOS = 16

    def __init__(
        self,
        args,
        directory,
        volume,
        wait=True,
        timeout=None,
        file="fio",
        lat_file="raw",
    ):
        """Start IO reads and writes using fio."""

        self.directory = directory
        self.stopped = False
        self.verify_failures = 0
        self.filename = file
        self.latency_filename = lat_file
        self.error_file = os.path.join(self.directory, f"{file}.stderr.log")
        self.io_errors = 0
        self.corruption_errors = 0

        if not os.path.exists(FIO_EXEC):
            raise _FioMissing(FIO_EXEC)

        self.args = [
            FIO_EXEC,
            f"--ioengine={FIO_ASYNC_IO}",
        ]
        self.args.extend(args)
        self.process = RunProcess(self.args, directory, wait=False, timeout_sec=timeout)

        if wait:
            self.wait(timeout)

    def split_log(self, input_log):
        """Split read and write values into own csv file.

        Convert fio csv file with both read and writes into seperate files
        read and write
        """
        filepath = os.path.join(self.directory, input_log)
        prefix = input_log.split("_")[0]
        read_file = os.path.join(self.directory, f"{prefix}_read.csv")
        write_file = os.path.join(self.directory, f"{prefix}_write.csv")

        read_data = []
        write_data = []
        read_sum = 0
        write_sum = 0

        with open(filepath, newline="") as file_object:
            rows = csv.reader(file_object)
            for row in rows:
                if int(row[2]) == 0:
                    read_sum += int(row[1])
                    read_data.append([row[0], row[1], read_sum])

                else:
                    write_sum += int(row[1])
                    write_data.append([row[0], row[1], write_sum])

        with open(read_file, "w", newline="") as file_object:
            csvwriter = csv.writer(file_object)
            for latency in read_data:
                csvwriter.writerow(latency)

        with open(write_file, "w", newline="") as file_object:
            csvwriter = csv.writer(file_object)
            for latency in write_data:
                csvwriter.writerow(latency)

        os.remove(filepath)

    def stop(self):
        """Stop fio gracefully when get ctrl-c."""
        self.process.stop()
        self.return_code = self.process.return_code
        self.stopped = True
        self.wait()

    def wait(self, timeout=None):
        """Wait for IO to finish."""
        self.return_code = self.process.wait(timeout)

        # If app was stopped with ctrl-c returns 128

        if self.stopped and (self.return_code == 128):
            self.return_code = 0

        filepath = os.path.join(self.directory, f"{self.filename}.json")
        errorpath = os.path.join(self.directory, f"{self.filename}.stderr.log")

        # Check if logfile created, sometimes not created if error occurs

        if os.path.exists(filepath):

            # First thing is strip out error message at top of file that is not
            # really json

            with open(filepath, "r") as file_object:
                lines = file_object.read().splitlines()

            if lines[0] != "{":
                error_msg = []
                for index, line in enumerate(lines):

                    if line == "{":
                        json_lines = lines[index:]
                        break
                    if line.strip() == "" or "fio: terminating on signal 2" in line:
                        pass
                    else:
                        error_msg.append(line)
                        if "crc32c: verify failed" in line:
                            self.verify_failures = self.verify_failures + 1

                if len(error_msg) > 0:
                    with open(errorpath, "w") as file_object:
                        file_object.writelines(error_msg)

                with open(filepath, "w") as file_object:
                    file_object.writelines(json_lines)

            # Now load the json log into the object

            try:
                with open(filepath, "r") as file_object:
                    self.logfile = json.load(file_object)
            except json.JSONDecodeError as error:
                raise _FioBadJson(error)

            # "bw" unit is KiB/sec, latency in nS

            read = self.logfile["jobs"][0]["read"]

            self.read_ios = read["total_ios"]
            self.read_bw_kib = read["bw"]
            self.read_bw_gb = self.read_bw_kib * KIB_TO_GB
            self.data_read_gb = read["io_kbytes"] * KIB_TO_GB

            self.read_mean_latency_ms = read["lat_ns"]["mean"] / NS_IN_MS
            self.read_max_latency_ms = read["lat_ns"]["max"] / NS_IN_MS
            self.read_mean_latency_us = read["lat_ns"]["mean"] / NS_IN_US
            self.read_max_latency_us = read["lat_ns"]["max"] / NS_IN_US

            write = self.logfile["jobs"][0]["write"]

            self.write_ios = write["total_ios"]
            self.write_bw_kib = write["bw"]
            self.write_bw_gb = self.write_bw_kib * KIB_TO_GB
            self.data_write_gb = write["io_kbytes"] * KIB_TO_GB

            self.write_mean_latency_ms = write["lat_ns"]["mean"] / NS_IN_MS
            self.write_max_latency_ms = write["lat_ns"]["max"] / NS_IN_MS
            self.write_mean_latency_us = write["lat_ns"]["mean"] / NS_IN_US
            self.write_max_latency_us = write["lat_ns"]["max"] / NS_IN_US

            # if latency file exists get delayed and trimmed latency

            csv_file = os.path.join(self.directory, f"{self.latency_filename}_lat.1.log")
            self.delayed_mean_read_latency_us = 0
            self.delayed_mean_write_latency_us = 0

            self.delayed_mean_read_latency_us = 0
            self.delayed_mean_write_latency_us = 0

            read_latencies = []
            write_latencies = []

            if os.path.exists(csv_file):
                with open(csv_file, "r") as file_object:
                    lreader = csv.reader(file_object)
                    next(lreader)

                    for row in lreader:
                        if int(row[2]) == 0:
                            read_latencies.append(int(row[1]) / NS_IN_US)
                        else:
                            write_latencies.append(int(row[1]) / NS_IN_US)

                    if len(read_latencies):
                        delay_read_latencies = read_latencies[FIO_DELAY_IOS:]
                        read_latencies.sort()
                        trimmed_read_latencies = read_latencies[FIO_TRIM_IOS:-FIO_TRIM_IOS]

                        self.delayed_mean_read_latency_us = sum(delay_read_latencies) / len(delay_read_latencies)
                        self.trimmed_mean_read_latency_us = sum(trimmed_read_latencies) / len(
                            trimmed_read_latencies
                        )

                    if len(write_latencies):
                        delay_write_latencies = write_latencies[FIO_DELAY_IOS:]
                        write_latencies.sort()
                        trimmed_write_latencies = write_latencies[FIO_TRIM_IOS:-FIO_TRIM_IOS]

                        self.delayed_mean_write_latency_us = sum(delay_write_latencies) / len(
                            delay_write_latencies
                        )
                        self.trimmed_mean_write_latency_us = sum(trimmed_write_latencies) / len(
                            trimmed_write_latencies
                        )

        if os.path.exists(self.error_file):
            with open(self.error_file, "r") as file_object:
                for line in file_object.readlines():
                    line = line.strip()
                    if line.find("terminating on signal 2") != -1:
                        if not self.stopped:
                            self.io_errors += 1
                    elif line.find("verify: bad magic header") != -1:
                        self.corruption_errors += 1
                        self.io_errors += 1
                    elif len(line) != 0:
                        self.io_errors += 1

        for job in self.logfile["jobs"]:
            self.io_errors += int(job["error"])

        if self.return_code != 0:
            self.io_errors += 1

        return self.return_code


def _get_target_directory(volume):
    if "Windows" == platform.system():
        return os.path.abspath(os.path.join(volume, "\\" "fio"))
    else:
        return os.path.join(volume, "fio")


def _get_fio_target_directory(volume):
    if "Windows" == platform.system():
        temp_directory = _get_target_directory(volume)
        return temp_directory.replace(":", r"\:")
    else:
        return _get_target_directory(volume)


def get_big_file_path(volume):
    return os.path.join(_get_target_directory(volume), FIO_BIG_FILE)


class FioFiles:
    def __init__(self, directory, volume):
        self.directory = directory
        self.volume = volume
        self.fio_directory = _get_fio_target_directory(self.volume)
        self.bigfile_path = os.path.join(self.fio_directory, FIO_BIG_FILE)
        self.verifyfile_path = os.path.join(self.fio_directory, FIO_VERIFY_FILE)
        self.performancefile_path = os.path.join(self.fio_directory, FIO_PERFORMANCE_FILE)

    def create(self, big=False, verify=False, disk_size=None, wait_sec=0):
        if big:
            self.file_size = int(BIG_FILE_SIZE * disk_size / BYTES_IN_GIB) * BYTES_IN_GIB
            self.file_size_gb = int(BIG_FILE_SIZE * disk_size / BYTES_IN_GIB)

            self.filename = FIO_BIG_FILE
        else:
            self.file_size = SMALL_FILE_SIZE
            self.file_size_gb = SMALL_FILE_SIZE / BYTES_IN_GIB
            self.filename = FIO_VERIFY_FILE if verify else FIO_PERFORMANCE_FILE

        self.filepath = os.path.join(_get_fio_target_directory(self.volume), self.filename)
        self.os_filepath = self.filepath.replace(r"\:", ":")

        if os.path.exists(self.os_filepath):
            log.debug(f"FioFiles: File already exists: {self.os_filepath}")
            return self

        if self.file_size > psutil.disk_usage(self.volume).free:
            raise FioNoSpace("Not enough free space on disk to create fio file")

        fio_args = [
            FIO_EXEC,
            "--direct=1",
            "--thread",
            "--numjobs=1",
            "--rw=write",
            "--iodepth=32",
            "--bs=131072",
            f"--output={os.path.join(self.directory,'fio_setup.json')}",
            "--output-format=json",
            f"--filesize={self.file_size}",
            f"--filename={self.filepath}",
            "--name=fio_setup",
        ]

        if verify:
            fio_args.extend(
                [
                    "--verify_interval=4096",
                    "--verify=crc32c",
                    "--verify_dump=1",
                    "--verify_state_save=0",
                    "--verify_async=2",
                    "--continue_on_error=verify",
                    "--verify_backlog=1",
                ]
            )
        log.debug(f"FioFiles: Creating file: {self.filepath}")
        RunProcess(fio_args, self.directory, wait=True)
        time.sleep(wait_sec)
        return self

    def get(self, big=False, verify=False, disk_size=None, wait_sec=0):
        if big:
            self.file_size = int(BIG_FILE_SIZE * disk_size / BYTES_IN_GIB) * BYTES_IN_GIB
            self.file_size_gb = int(BIG_FILE_SIZE * disk_size / BYTES_IN_GIB)

            self.filename = FIO_BIG_FILE
        else:
            self.file_size = SMALL_FILE_SIZE
            self.file_size = SMALL_FILE_SIZE / BYTES_IN_GIB

            self.filename = FIO_VERIFY_FILE if verify else FIO_PERFORMANCE_FILE
        self.filepath = os.path.join(_get_fio_target_directory(self.volume), self.filename)
        self.os_filepath = self.filepath.replace(r"\:", ":")
        return self


def check_fio_installation():
    if not os.path.exists(FIO_EXEC):
        raise _FioMissing(FIO_EXEC)


def space_for_big_file(info, volume):
    filepath = os.path.join(_get_fio_target_directory(volume), FIO_BIG_FILE)
    os_filepath = filepath.replace(r"\:", ":")
    if os.path.exists(os_filepath):
        return True
    disk_size = float(info.parameters["Size"])
    file_size = int(BIG_FILE_SIZE * disk_size / BYTES_IN_GIB) * BYTES_IN_GIB

    # shutil, psutil, and df return wrong number of bytes on some version of linux
    # value is off by 1000/1024 so use the percent because ratio is correct

    percent_free = 100.0 - psutil.disk_usage(volume).percent
    return file_size < (disk_size * percent_free)


def os_trim(directory, volume, wait_time_sec=600):
    if platform.system() == "Windows":
        RunProcess(["defrag.exe", volume, "/Retrim"], directory, wait=True, timeout_sec=300)
    else:
        RunProcess(["fstrim", volume], directory, wait=True, timeout_sec=300)
    time.sleep(wait_time_sec)


def clean_fio_files(volume):

    bigfile_path = os.path.join(_get_fio_target_directory(volume), FIO_BIG_FILE)
    verifyfile_path = os.path.join(_get_fio_target_directory(volume), FIO_VERIFY_FILE)
    performancefile_path = os.path.join(_get_fio_target_directory(volume), FIO_PERFORMANCE_FILE)

    if os.path.exists(bigfile_path):
        os.remove(bigfile_path)

    if os.path.exists(verifyfile_path):
        os.remove(verifyfile_path)

    if os.path.exists(performancefile_path):
        os.remove(performancefile_path)
