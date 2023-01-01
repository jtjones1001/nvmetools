# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
r"""Define functions for using nvmecmd utility.

nvmecmd uses admin commands to communicate with nvme device
some admin commands, like self-test, require admin rights
nvmecmd is included with the package in <package>\resources\nvmecmd
nvmecmd requires output directory to be there before it runs
nvmecmd -v input enables verbose logging

//------------------------------------------------------------------------------
// Exit codes for nvmecmd from C++ project
//------------------------------------------------------------------------------
inline const int NVMECMD_USAGE_ERROR_CODE = 16;
inline const int NVMECMD_EXCEPTION_CODE   = 17;
inline const int NVMECMD_NO_NVME_DRIVES = 18;
inline const int NVMECMD_NVME_DRIVE_NOT_FOUND = 19;

inline const int READINFO_FIRST_SAMPLE_READ_ERROR = 20;
inline const int READINFO_FAIL_SAMPLES = 21;
inline const int READINFO_FAIL_LIMIT = 22;

inline const int SELFTEST_NOT_SUPPORTED_ERROR = 30;
inline const int SELFTEST_NOT_STARTED_ERROR = 31;
inline const int SELFTEST_NO_EDSTT_ERROR = 32;
inline const int SELFTEST_FAILED = 33;
inline const int SELFTEST_ABORT_FAILED_ERROR = 34;
inline const int SELFTEST_WRONG_STATUS_ERROR = 35;
inline const int SELFTEST_ABORT_READ_ERROR = 36;
"""
import json
import os
import platform

from nvmetools import SRC_DIRECTORY
from nvmetools.support.conversions import (
    MS_IN_MIN,
    MS_IN_SEC,
    SEC_IN_MIN,
    as_datetime,
    as_int,
    as_linear,
    as_monotonic,
    is_debug,
)
from nvmetools.support.process import RunProcess

LINEAR_LIMIT = 0.9

NVMECMD_DIR = os.path.join(SRC_DIRECTORY, "nvmetools", "resources", "nvmecmd")

if "Windows" == platform.system():
    NVMECMD_EXEC = os.path.join(NVMECMD_DIR, "nvmecmd.exe")
else:
    NVMECMD_EXEC = os.path.join(NVMECMD_DIR, "nvmecmd")

READ_INFO_FILE = "nvme.info.json"
FIRST_SAMPLE_READ_FILE = "nvme.info.sample-1.json"
SELFTEST_FILE = "selftest.summary.json"
READ_SUM_FILE = "read.summary.json"
TRACE_LOG = "nvmecmd.trace.log"
NVMECMD_READ_CMD = os.path.join(NVMECMD_DIR, "read.cmd.json")
NVMECMD_SELFTEST_CMD = os.path.join(NVMECMD_DIR, "self-test.cmd.json")
NVMECMD_EXT_SELFTEST_CMD = os.path.join(NVMECMD_DIR, "extended-self-test.cmd.json")

# Use exception code 51-55 for this module


class _NoNvme(Exception):
    def __init__(self, nvme):
        self.code = 51
        self.nvmetools = True
        super().__init__(f" NVME device {nvme} was not found.")


class _NvmecmdBadJson(Exception):
    def __init__(self, error, file):
        self.code = 52
        self.nvmetools = True
        error_msg = f"{file} @line {error.lineno} @col {error.colno}"
        super().__init__(f" failed parsing nvmecmd JSON file {error_msg}.")


class _NvmecmdException(Exception):
    def __init__(self, directory):
        self.code = 53
        self.nvmetools = True
        tracelog = os.path.join(directory, TRACE_LOG)
        super().__init__(f" nvmecmd had exception, see {tracelog}.")


class NvmecmdPermissionError(Exception):
    """Custom exception to indicate nvmecmd missing permission."""

    def __init__(self):
        """Initialize exception."""
        self.code = 54
        self.nvmetools = True
        error_msg = " nvmecmd utility does not have permission to access NVMe.\n\n"
        error_msg += " To give permission run these commands:\n\n"
        error_msg += f"  sudo chmod 777 {NVMECMD_EXEC} \n"
        error_msg += f"  sudo setcap cap_sys_admin,cap_dac_override=ep {NVMECMD_EXEC} \n"
        super().__init__(error_msg)


def check_nvmecmd_permissions():
    """Check nvmecmd permission to read NVMe device."""
    if "Windows" != platform.system():
        attribute = "security.capability"
        expected_value = "0100000202002000000000000000000000000000"
        try:
            current_value = os.getxattr(NVMECMD_EXEC, attribute).hex()
            if current_value != expected_value:
                raise NvmecmdPermissionError()
        except OSError:
            raise NvmecmdPermissionError()

        if int(oct(os.stat(NVMECMD_EXEC).st_mode)[-3:]) != 777:
            raise NvmecmdPermissionError()

    # TODO: Check check_nvmecmd_permissions on other versions of Linux, only tested on Fedora


class Read:
    """Read NVMe information using nvmecmd utility.

    Attributes:
       info (json): Information read from nvme.info.json.
       return_code (int): return code.
       run_time (float): Time process ran in seconds.
       summary (json): Summary information from read.summary.json.
    """

    def __init__(
        self,
        nvme=0,
        directory=".",
        samples=1,
        interval=0,
        cmd_file="read",
        wait=True,
    ):
        """Start reading information.

        Args:
           nvme: NVMe device number.
           directory: Directory to log results.
           samples: Number of samples to read.
           intervalerval between samples in mS.
           cmd_file: Name of cmd file to use for the read.
           wait:  Waits for read to complete if True.
        """
        cmd_file_path = os.path.join(NVMECMD_DIR, f"{cmd_file}.cmd.json")
        self._samples = samples
        self._directory = os.path.abspath(directory)
        self._nvme = nvme

        check_nvmecmd_permissions()

        args = [
            NVMECMD_EXEC,
            cmd_file_path,
            "--dir",
            f"{self._directory}",
            "--nvme",
            f"{self._nvme}",
            "--samples",
            f"{self._samples}",
            "--interval",
            f"{interval}",
        ]
        if is_debug():
            args.append("-v")

        if interval == 0:
            self._timeout = 60 + samples
        else:
            self._timeout = 60 + samples * interval / MS_IN_SEC

        self._process = RunProcess(args, directory, wait=False)
        if wait:
            self.wait()

    def wait(self):
        """Wait for information to be ready.

        Returns:
           Return code from nvmecmd process.

        Raises:
           _NvmecmdBadJson if the info or summary file not correctly formatted.
        """
        self._process.wait(self._timeout)
        self.return_code = self._process.return_code
        self.run_time = self._process.run_time

        if self.return_code in [16, 17]:
            raise _NvmecmdException(self._directory)
        if self.return_code in [18, 19]:
            raise _NoNvme(self._nvme)

        info_file = FIRST_SAMPLE_READ_FILE if self._samples > 1 else READ_INFO_FILE

        try:
            info_file = os.path.join(self._directory, info_file)
            with open(info_file, "r") as file_object:
                self.info = json.load(file_object)

            summary_file = os.path.join(self._directory, READ_SUM_FILE)
            with open(summary_file, "r") as file_object:
                self.summary = json.load(file_object)

        except json.JSONDecodeError as error:
            raise _NvmecmdBadJson(error, summary_file)

        if not is_debug() and self.return_code == 0:
            tracelog = os.path.join(self._directory, TRACE_LOG)
            os.remove(tracelog)

        return self.return_code

    def stop(self):
        """Stop reading information gracefully.

        Stops the read when doing multiple samples by stopping the nvmecmd process.
        """
        self._process.stop()


class Selftest:
    """Run drive self-test diagnostic.

    Runs the short or extended self-test diagnostic.

    Attributes:
       data (dictionary): Dictionary of parameters
    """

    def __init__(self, nvme, directory, extended=False, limit_min=2):
        """Run self-test diagnostic.

        Args:
            nvme:  nvme device number.
            directory: Directory where results are logged.
            extended: Runs extended self-test if True, else the short self-test.
            limit_min: Time limit for self-test in minutes.
        """
        self._directory = directory
        self._nvme = nvme
        self._extended = extended
        self.data = {}
        self.data["runtime limit"] = limit_min

        if extended:
            cmd_file = NVMECMD_EXT_SELFTEST_CMD
        else:
            cmd_file = NVMECMD_SELFTEST_CMD

        check_nvmecmd_permissions()

        args = [
            NVMECMD_EXEC,
            cmd_file,
            "--dir",
            f"{directory}",
            "--nvme",
            f"{nvme}",
        ]
        if is_debug():
            args.append("-v")

        self.data["return code"] = RunProcess(args, directory).return_code

        if self.data["return code"] in [16, 17]:
            raise _NvmecmdException(directory)
        if self.data["return code"] in [18, 19]:
            raise _NoNvme(nvme)
        if self.data["return code"] not in [30, 31, 32]:
            try:
                info_file = os.path.join(directory, SELFTEST_FILE)
                with open(info_file, "r") as file_object:
                    self.data["logfile"] = json.load(file_object)
            except json.JSONDecodeError as error:
                raise _NvmecmdBadJson(error, info_file)

            elapsed_time = []
            elapsed_progress_time = [0]  # first sample has status 0 but want to start at 0,0
            elapsed_progress = [0]

            details = self.data["logfile"]["selftest details"]
            self.data["runtime"] = details["run time in ms"] / MS_IN_MIN
            start = as_datetime(details["status"][0]["timestamp"])

            for sample in details["status"]:
                delta = as_datetime(sample["timestamp"]) - start
                elapsed_time.append(delta.total_seconds() / SEC_IN_MIN)
                if sample["status"] != 0:
                    elapsed_progress.append(int(sample["percent complete"]))
                    elapsed_progress_time.append(delta.total_seconds() / SEC_IN_MIN)

            self.data["monotonic"] = as_monotonic(elapsed_progress)
            self.data["linear"] = as_linear(elapsed_progress_time, elapsed_progress)
            self.data["result_poh"] = as_int(details["log page 6 power on hours"])
            self.data["last_poh"] = as_int(details["status"][-1]["Power On Hours"])
            self.data["second_last_poh"] = as_int(details["status"][-2]["Power On Hours"])

        if not is_debug() and self.data["return code"] == 0:
            tracelog = os.path.join(directory, TRACE_LOG)
            os.remove(tracelog)
