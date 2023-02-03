# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os
import time

from nvmetools import TestCase, TestStep, fio, log, rqmts, steps


def temperature_cycle_stress(suite, cycles=2):
    """Verify drive reliability under temperature cycle IO stress.

    The test verifies drive reliability under IO stress designed to temperature cycle the drive.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Temperature cycle stress", temperature_cycle_stress.__doc__) as test:

        test.data["io runtime"] = READ_TIME_SEC = 150
        test.data["idle time"] = IDLE_TIME_SEC = 210
        test.data["cycles"] = cycles
        test.data["queue depth"] = QUEUE_DEPTH = 32
        test.data["block size"] = BLOCK_SIZE_KIB = 128

        # -----------------------------------------------------------------------------------------
        # Before test, read NVMe info and verify no critical warnings, get fio file, wait for idle
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)
        fio_file = steps.get_fio_stress_file(test, float(start_info.parameters["Size"]))
        steps.idle_wait(test)

        # -----------------------------------------------------------------------------------------
        #  Run cycles of IO and idle
        # -----------------------------------------------------------------------------------------
        # Use fio to run cycles of IO and idle.  The IO is configured to cause the fastest
        # temperature rise possible, 100% reads, QD32, and block size 128kib.  Data integrity is
        # checked during the IO but is done using asynchronous threads to avoid slowing down the IO
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_info_samples(test)

        with TestStep(test, "IO stress", "Run bursts of IO reads to cycle temperature") as step:
            fio_io_errors = 0
            fio_corruption_errors = 0

            for index in range(cycles):
                log.debug(f"Running IO for {READ_TIME_SEC} seconds")
                fio_args = [
                    "--direct=1",
                    "--thread",
                    "--numjobs=1",
                    "--allow_file_create=0",
                    f"--filesize={fio_file.file_size}",
                    f"--filename={fio_file.filepath}",
                    "--rw=read",
                    f"--iodepth={QUEUE_DEPTH}",
                    f"--bs={BLOCK_SIZE_KIB}k",
                    "--verify_interval=4096",
                    "--verify=crc32c",
                    "--verify_dump=1",
                    "--verify_state_save=0",
                    "--verify_async=2",
                    "--continue_on_error=verify",
                    "--verify_backlog=1",
                    f"--output={os.path.join(step.directory,f'fio_{index}.json')}",
                    "--output-format=json",
                    "--time_based",
                    f"--runtime={READ_TIME_SEC}",
                    "--name=io_temp_cycle",
                ]
                fio_result = fio.RunFio(fio_args, step.directory, suite.volume, file=f"fio_{index}")
                fio_io_errors += fio_result.io_errors
                fio_corruption_errors += fio_result.corruption_errors

                rqmts.no_io_errors(step, fio_io_errors)
                rqmts.no_data_corruption(step, fio_corruption_errors)

                log.debug(f"Waiting {IDLE_TIME_SEC} seconds for drive to cool down")
                time.sleep(IDLE_TIME_SEC)

        steps.stop_info_samples(test, info_samples)

        test.data["min temp"] = info_samples.min_temp
        test.data["max temp"] = info_samples.max_temp
        test.data["time throttled"] = info_samples.time_throttled
        test.data["read"] = info_samples.data_read
        test.data["written"] = info_samples.data_written

        # -----------------------------------------------------------------------------------------
        # After test, read NVMe info and compare against the starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
