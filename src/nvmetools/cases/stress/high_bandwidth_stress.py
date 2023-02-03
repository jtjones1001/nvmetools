# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os

from nvmetools import TestCase, TestStep, fio, log, rqmts, steps


def high_bandwidth_stress(suite, run_time_sec=180):
    """Verify drive reliability under high bandwidth IO stress.

    The test verifies drive reliability under high bandwidth IO stress.  High bandwidth is obtained
    doing reads and writes with a large block size and queue depth.  The goal of this test is to
    maximize the data being read and written and verify the drive is reliable.  During this test
    the drive temperature should be high and throttling may occur.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "High bandwidth stress", high_bandwidth_stress.__doc__) as test:

        test.data["block size kib"] = BLOCK_SIZE_KB = 128
        test.data["queue depth"] = QUEUE_DEPTH = 32
        test.data["run time sec"] = run_time_sec
        test.data["runtime"] = f"{run_time_sec/60:0.2f} min"

        # -----------------------------------------------------------------------------------------
        # Before test, read NVMe info and verify no critical warnings, get fio file, wait for idle
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)
        fio_file = steps.get_fio_stress_file(test, float(start_info.parameters["Size"]))
        steps.idle_wait(test)

        # -----------------------------------------------------------------------------------------
        #  Run high bandwidth IO. High bandwidth is achieved using sequential addressing, high
        #  queue depth, and a large  block size.  The fio utility is used to run the IO.
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_info_samples(test)

        with TestStep(test, "IO stress", "Run high bandwidth IO stress with fio") as step:

            fio_args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                f"--filesize={fio_file.file_size}",
                f"--filename={fio_file.filepath}",
                "--rw=readwrite",
                f"--iodepth={QUEUE_DEPTH}",
                f"--bs={BLOCK_SIZE_KB}k",
                "--verify_interval=4096",
                "--verify=crc32c",
                "--verify_dump=1",
                "--verify_state_save=0",
                "--verify_async=2",
                "--continue_on_error=verify",
                "--verify_backlog=1",
                f"--output={os.path.join(step.directory,'fio.json')}",
                "--output-format=json",
                "--time_based",
                f"--runtime={run_time_sec}",
                "--name=fio",
            ]
            fio_result = fio.RunFio(fio_args, step.directory, suite.volume)

            rqmts.no_io_errors(step, fio_result)
            rqmts.no_data_corruption(step, fio_result)

            test.data["read"] = f"{fio_result.data_read_gb:0.1f} GB"
            test.data["read bandwidth"] = f"{fio_result.read_bw_gb:0.3f} GB/s"

            test.data["written"] = f"{fio_result.data_write_gb:0.1f} GB"
            test.data["write bandwidth"] = f"{fio_result.write_bw_gb:0.3f} GB/s"

        steps.stop_info_samples(test, info_samples)
        test.data["min temp"] = info_samples.min_temp
        test.data["max temp"] = info_samples.max_temp
        test.data["time throttled"] = info_samples.time_throttled
        # -----------------------------------------------------------------------------------------
        # After test, read NVMe info and compare against the starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
