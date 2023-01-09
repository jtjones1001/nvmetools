# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""This module provides test cases for reading and verifying NVMe information."""
import os
import platform
import time

from nvmetools import Info, TestCase, TestStep, fio, log, rqmts, steps
from nvmetools.support.conversions import as_int

import psutil


def smart_data(suite):
    """Verify SMART data read/written attributes are accurate.

    Compares the data read and written reported by SMART against the OS counters reported by
    psutil.  This verifies the SMART attributes are accurate. It also confirms the volume
    specified resides on the physical nvme specified.

    The SMART attributes are only accurate to 512,000 bytes.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "SMART data", smart_data.__doc__) as test:

        test.data["smart data lsb"] = SMART_DATA_LSB = 512000
        test.data["smart data limit"] = SMART_DATA_LIMIT = 512000
        test.data["smart data run time"] = SMART_DATA_FIO_RUNTIME = 180

        # -----------------------------------------------------------------------------------------
        #  Get fio file if does not already exist
        # -----------------------------------------------------------------------------------------
        fio_file = steps.get_fio_performance_file(test)

        # -----------------------------------------------------------------------------------------
        #  Get start info
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Start info", "Verify not in error state", stop_on_fail=True) as step:

            if platform.system() == "Windows":
                drive_name = f"PhysicalDrive{suite.nvme}"
            else:
                drive_name = f"nvme{suite.nvme}n1"

            start_counters = psutil.disk_io_counters(perdisk=True)[drive_name]
            start_info = Info(nvme=suite.nvme, directory=step.directory)
            rqmts.no_critical_warnings(step, start_info)

        # -----------------------------------------------------------------------------------------
        # Run fio
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "IO", "Run IO to generate read and write data") as step:

            high_bw = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                "--allow_file_create=0",
                f"--filesize={fio_file.file_size}",
                f"--filename={fio_file.filepath}",
                "--verify=crc32c",
                "--verify_dump=1",
                "--verify_state_save=0",
                "--verify_async=2",
                "--continue_on_error=verify",
                "--rw=rw",
                "--iodepth=8",
                "--bs=1M",
                "--rwmixread=50",
                f"--size={fio_file.file_size}",
                f"--output={os.path.join(step.directory,'fio.json')}",
                "--output-format=json",
                "--time_based",
                f"--runtime={SMART_DATA_FIO_RUNTIME}",
                "--name=fio",
            ]

            fio_info = fio.RunFio(args=high_bw, directory=step.directory, volume=suite.volume)
            rqmts.no_io_errors(step, fio_info)
            rqmts.no_data_corruption(step, fio_info)

        # -----------------------------------------------------------------------------------------
        # Read final information
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "End info", "Verify no unexpected changes during test") as step:
            time.sleep(10)
            end_counters = psutil.disk_io_counters(perdisk=True)[drive_name]
            end_info = Info(suite.nvme, directory=step.directory, compare_info=start_info)

            rqmts.no_critical_warnings(step, end_info)
            rqmts.no_errorcount_change(step, end_info)
            rqmts.no_static_parameter_changes(step, end_info)
            rqmts.no_counter_parameter_decrements(step, end_info)

            test.data["write"] = {
                "fio": fio_info.logfile["jobs"][0]["write"]["io_bytes"],
                "counter": end_counters.write_bytes - start_counters.write_bytes,
                "smart": SMART_DATA_LSB
                * (
                    as_int(end_info.parameters["Data Units Written"])
                    - as_int(start_info.parameters["Data Units Written"])
                ),
            }
            test.data["write"]["delta"] = {
                "fio": test.data["write"]["fio"] - test.data["write"]["counter"],
                "smart": test.data["write"]["smart"] - test.data["write"]["counter"],
            }
            test.data["read"] = {
                "fio": fio_info.logfile["jobs"][0]["read"]["io_bytes"],
                "counter": end_counters.read_bytes - start_counters.read_bytes,
                "smart": SMART_DATA_LSB
                * (
                    as_int(end_info.parameters["Data Units Read"])
                    - as_int(start_info.parameters["Data Units Read"])
                ),
            }
            test.data["read"]["delta"] = {
                "fio": test.data["read"]["fio"] - test.data["read"]["counter"],
                "smart": test.data["read"]["smart"] - test.data["read"]["counter"],
            }
            for io_type in ["read", "write"]:
                for method in ["fio", "smart", "counter"]:
                    value = test.data[io_type][method]
                    name = f"{method} {io_type} bytes"
                    log.debug(f"          {name:20} {value:,}")

                log.debug("")

        rqmts.smart_read_data(step, abs(test.data["read"]["delta"]["smart"]), SMART_DATA_LIMIT)
        rqmts.smart_write_data(step, abs(test.data["write"]["delta"]["smart"]), SMART_DATA_LIMIT)
