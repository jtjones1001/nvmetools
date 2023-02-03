# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import copy
import os
import time

from nvmetools import InfoSamples, TestCase, TestStep, fio, rqmts, steps
from nvmetools.support.conversions import MS_IN_SEC, NS_IN_MS


def background_smart(suite):
    """Verify effect of Get Log Page 2 on normal read/write IO.

    This test runs the Get Log Page 2 command several thousand times to get a large
    sample to ensure reliability.  This command reads SMART attributes.  There is
    an interval between commands to ensure plenty of idle time.

    The command is run standalone and with IO reads and writes running.

    The test verifies the average and maximum latencies.  The information returned by
    the commands is verified as follows:

        Dynamic parameters have no requirement

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Background SMART", background_smart.__doc__) as test:

        test.data["interval ms"] = ADMIN_LOG2_INTERVAL_MS = 500
        test.data["samples"] = ADMIN_LOG2_SAMPLE = 1825
        test.data["slow latency limit"] = SMART_IO_LATENCY_INCREASE_LIMIT = 50

        # -----------------------------------------------------------------------------------------
        # Create fio file if does not already exist
        # -----------------------------------------------------------------------------------------
        fio_file = steps.get_fio_small_file(test)

        # -----------------------------------------------------------------------------------------
        # Wait to ensure drive is back to idle temperature and no garbage collection underway
        # -----------------------------------------------------------------------------------------
        steps.idle_wait(test)

        # -----------------------------------------------------------------------------------------
        # SMART baseline
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "SMART baseline", f"Run Get Log Page 2 command {ADMIN_LOG2_SAMPLE:,} times") as step:

            logpage2 = InfoSamples(
                nvme=suite.nvme,
                samples=ADMIN_LOG2_SAMPLE,
                interval=ADMIN_LOG2_INTERVAL_MS,
                cmd_file="logpage02",
                directory=step.directory,
            )
            rqmts.admin_commands_pass(step, logpage2)
            rqmts.no_static_parameter_changes(step, logpage2)
            rqmts.no_counter_parameter_decrements(step, logpage2)
            rqmts.admin_command_avg_latency(step, logpage2, suite.device["Average Admin Cmd Limit mS"])
            rqmts.admin_command_max_latency(step, logpage2, suite.device["Maximum Admin Cmd Limit mS"])

        # -----------------------------------------------------------------------------------------
        # fio baseline
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "IO baseline", "Baseline IO reads and writes using fio") as step:

            fio_runtime = ADMIN_LOG2_SAMPLE * (ADMIN_LOG2_INTERVAL_MS / MS_IN_SEC) + 20

            fio_base_args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                "--allow_file_create=0",
                f"--filesize={fio_file.file_size}",
                f"--filename={fio_file.filepath}",
                "--rw=randrw",
                "--iodepth=2",
                "--bs=4096",
                "--rwmixread=50",
                f"--size={fio_file.file_size}",
                "--verify=crc32c",
                "--verify_dump=1",
                "--verify_state_save=0",
                "--verify_async=2",
                "--continue_on_error=verify",
                "--time_based",
                "--write_lat_log=latency",
                "--log_avg_ms=200",
                "--output-format=json+",
                "--name=fio",
            ]
            args = copy.copy(fio_base_args)
            args.append(f"--output={os.path.join(step.directory,'fio.json')}")
            args.append(f"--runtime={fio_runtime}")

            fio_result = fio.RunFio(args, step.directory, suite.volume)
            fio_result.split_log("latency_lat.1.log")

            rqmts.no_io_errors(step, fio_result)
            rqmts.no_data_corruption(step, fio_result)

        # -----------------------------------------------------------------------------------------
        # Wait to ensure drive is back to idle temperature and no garbage collection underway
        # -----------------------------------------------------------------------------------------
        steps.idle_wait(test)

        # -----------------------------------------------------------------------------------------
        # Run fio and Get Log Page 2 concurrently.
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "SMART and IO", "Run IO and Get Log Page 2 concurrently") as step:

            fio_args = copy.copy(fio_base_args)
            fio_args.append(f"--output={os.path.join(step.directory,'fio.json')}")
            fio_args.append(f"--runtime={fio_runtime}")
            fio_logpage2 = fio.RunFio(fio_args, step.directory, suite.volume, wait=False)

            time.sleep(10)
            logpage2_fio = InfoSamples(
                nvme=suite.nvme,
                samples=ADMIN_LOG2_SAMPLE,
                interval=ADMIN_LOG2_INTERVAL_MS,
                cmd_file="logpage02",
                directory=step.directory,
            )
            rqmts.admin_commands_pass(step, logpage2_fio)
            rqmts.no_static_parameter_changes(step, logpage2_fio)
            rqmts.no_counter_parameter_decrements(step, logpage2_fio)
            rqmts.admin_command_avg_latency(step, logpage2_fio, suite.device["Average Admin Cmd Limit mS"])
            rqmts.admin_command_max_latency(step, logpage2_fio, suite.device["Maximum Admin Cmd Limit mS"])

            fio_logpage2.wait(timeout=120)
            fio_logpage2.split_log("latency_lat.1.log")
            rqmts.no_io_errors(step, fio_logpage2)
            rqmts.no_data_corruption(step, fio_logpage2)

            # Add data to the results file

            for fio_object in [fio_result, fio_logpage2]:
                if fio_object == fio_result:
                    label = "fio"
                else:
                    label = "both"

                test.data[label] = {}
                for io_type in ["read", "write"]:
                    test.data[label][f"{io_type} avg"] = (
                        fio_object.logfile["jobs"][0][io_type]["lat_ns"]["mean"] / NS_IN_MS
                    )
                    test.data[label][f"{io_type} max"] = (
                        fio_object.logfile["jobs"][0][io_type]["lat_ns"]["max"] / NS_IN_MS
                    )
                    bins = fio_object.logfile["jobs"][0][io_type]["clat_ns"]["bins"]
                    count = 0
                    tmp = []
                    for cmd_bin in reversed(bins):
                        for _index in range(bins[cmd_bin]):
                            if count < ADMIN_LOG2_SAMPLE:
                                tmp.append(int(cmd_bin) / NS_IN_MS)
                                count += 1
                    test.data[label][f"{io_type} slow"] = sum(tmp) / len(tmp)

            test.data["delta"] = {}
            test.data["percent"] = {}

            for io_type in [
                "read avg",
                "read max",
                "read slow",
                "write avg",
                "write max",
                "write slow",
            ]:
                test.data["delta"][io_type] = test.data["both"][io_type] - test.data["fio"][io_type]
                test.data["percent"][io_type] = 100 * test.data["delta"][io_type] / test.data["fio"][io_type]

            # check against the limit

            test.data["max latency increase"] = max(
                test.data["percent"]["write slow"], test.data["percent"]["read slow"]
            )
            rqmts.smart_latency_increase(
                step, test.data["max latency increase"], SMART_IO_LATENCY_INCREASE_LIMIT, ADMIN_LOG2_SAMPLE
            )
