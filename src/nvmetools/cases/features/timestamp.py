# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os
import time

from nvmetools import Info, TestCase, TestStep, fio, log, rqmts, steps
from nvmetools.support.conversions import MS_IN_HR, MS_IN_SEC, as_int, as_linear


def timestamp(suite):
    """Verify the timestamp feature.

    If the drive supports the optional Timestamp (Feature Identifier 0Eh), this test
    verifies the drive timestamp matches the host timestamp, within a specified error
    tolerance.

    The host and drive timestamps are sampled every second for 5 minutes of IO reads
    and writes and another 5 minutes of idle.  The change in timestamps must be within
    the specified tolerance.

    Windows and Linux drivers are expected to update the timestamp, therefore the test
    verifies the host is the origin.  The test also verifies the sync flag is not set
    as this indicates the timestamp is not valid.

    If the timestamp feature is not supported the test passes since this is an
    optional feature.

    Args:
        suite:  Parent TestSuite instance

    """
    with TestCase(suite, "Timestamp", timestamp.__doc__) as test:

        test.data["idle time"] = TIMESTAMP_IDLE_TIME = 150
        test.data["io time"] = TIMESTAMP_RUNTIME = 300
        test.data["Timestamp Absolute Hours"] = suite.device["Timestamp Absolute Hours"]
        test.data["Timestamp Relative Percent"] = suite.device["Timestamp Relative Percent"]

        # -----------------------------------------------------------------------------------------
        #  Read NVMe info and verify no critical warnings and timestamp supported
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Test start info", "Read NVMe information using nvmecmd") as step:

            start_info = Info(nvme=suite.nvme, directory=step.directory)

            test.data["timestamp supported"] = "Timestamp Feature" in start_info.parameters

            if not test.data["timestamp supported"]:
                test.skip("Timestamp feature is not supported.")

            start_drive_timestamp_ms = as_int(start_info.parameters["Timestamp"])
            host_drive_timestamp_ms = as_int(start_info.parameters["Host Timestamp"])

            test.data["start stopped"] = start_info.parameters["Timestamp Stopped"]
            test.data["start drive timestamp"] = start_drive_timestamp_ms
            test.data["start host timestamp"] = host_drive_timestamp_ms
            test.data["start delta ms"] = abs(host_drive_timestamp_ms - start_drive_timestamp_ms)
            test.data["start delta hrs"] = test.data["start delta ms"] / MS_IN_HR

            # stop test if drive in error state

            step.stop_on_fail = True
            rqmts.no_critical_warnings(step, start_info)
            step.stop_on_fail = False

            # Verify the absolute accuracy of the timestamp compared to the host clock, the drive
            # timestamp should be set by the OS at startup.  This accuracy may depend on how long
            # ago the host started.

            rqmts.timestamp_absolute_accuracy(
                step, test.data["start delta hrs"], test.data["Timestamp Absolute Hours"]
            )

        # -----------------------------------------------------------------------------------------
        # Step: Get the file for fio to read and write
        # -----------------------------------------------------------------------------------------
        fio_file = steps.get_fio_small_file(test)

        # -----------------------------------------------------------------------------------------
        #  Start sampling SMART and Power State
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_info_samples(test, cmd_file="timestamp")

        # -----------------------------------------------------------------------------------------
        # Step: Run IO and then wait for idle period
        # -----------------------------------------------------------------------------------------
        # Wait several minutes for drive to enter low power state, run continuous IO for several
        # minutes so drive is in power state 0, then wait again for drive to enter low power state.
        # This ensures the timestamp accuracy can be checked across multiple power states because
        # some drives don't run the timestamp in low power states,
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Wait and IO", "Wait then run IO then wait again.") as step:

            log.debug(" ")
            log.debug(f"Waiting {TIMESTAMP_IDLE_TIME-2} seconds before starting IO")
            log.debug(" ")

            time.sleep(TIMESTAMP_IDLE_TIME - 2)

            args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                "--allow_file_create=0",
                f"--filesize={fio_file.file_size}",
                f"--filename={fio_file.filepath}",
                "--rw=rw",
                "--iodepth=8",
                "--bs=4096",
                f"--size={fio_file.file_size}",
                f"--output={os.path.join(step.directory,'fio.json')}",
                "--output-format=json",
                "--verify=crc32c",
                "--verify_dump=1",
                "--verify_state_save=0",
                "--verify_async=2",
                "--continue_on_error=verify",
                "--time_based",
                f"--runtime={TIMESTAMP_RUNTIME}",
                "--name=fio",
            ]
            fio_result = fio.RunFio(args, step.directory, suite.volume)
            rqmts.no_io_errors(step, fio_result)
            rqmts.no_data_corruption(step, fio_result)

            log.debug(" ")
            log.debug(f"Waiting {TIMESTAMP_IDLE_TIME} seconds before stopping sampling")
            log.debug(" ")
            time.sleep(TIMESTAMP_IDLE_TIME)

        # -----------------------------------------------------------------------------------------
        # Stop reading SMART and Power State information that was started above
        # -----------------------------------------------------------------------------------------
        info_samples.stop()

        rqmts.admin_commands_pass(step, info_samples)
        rqmts.no_static_parameter_changes(step, info_samples)
        rqmts.no_counter_parameter_decrements(step, info_samples)

        # -----------------------------------------------------------------------------------------
        #  Read NVMe info and compare against starting info
        # -----------------------------------------------------------------------------------------
        end_info = steps.test_end_info(test, start_info)

        # -----------------------------------------------------------------------------------------
        # Step: Verify the timestamp requirements
        # -----------------------------------------------------------------------------------------
        # Verify the timestamp change matches the host time change and changes linearily, also
        # make sure it hasn't stopped
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Verify timestamp") as step:

            test.data["end stopped"] = end_info.parameters["Timestamp Stopped"]

            drive_change = as_int(end_info.parameters["Timestamp"]) - start_drive_timestamp_ms
            host_change = as_int(end_info.parameters["Host Timestamp"]) - host_drive_timestamp_ms

            test.data["drive change"] = drive_change
            test.data["host change"] = host_change
            test.data["percentage error"] = 100 * (host_change - drive_change) / host_change

            # create the data series to plot and check linearity on

            details = info_samples.summary["read details"]["sample"]

            test.data["host"] = [0]  # first sample has status 0 but want to start at 0,0
            test.data["drive"] = [0]

            drive_start = as_int(details[0]["Drive Timestamp"])
            host_start = as_int(details[0]["Host Timestamp"])
            test.data["power states"] = [as_int(details[0]["Current Power State"])]

            for sample in details:
                test.data["drive"].append((as_int(sample["Drive Timestamp"]) - drive_start) / MS_IN_SEC)
                test.data["host"].append((as_int(sample["Host Timestamp"]) - host_start) / MS_IN_SEC)
                test.data["power states"].append(int(sample["Current Power State"]))

            test.data["linearity"] = as_linear(test.data["host"], test.data["drive"])

            # Verify the timestamp changes linearily and matches the host time change.  Also
            # check if the timestamp has stopped but if so don't know when in the past it stopped.

            rqmts.timestamp_did_not_stop(step, end_info)
            rqmts.timestamp_linearity(step, test.data["linearity"])
            rqmts.timestamp_relative_accuracy(
                step, test.data["percentage error"], test.data["Timestamp Relative Percent"]
            )
