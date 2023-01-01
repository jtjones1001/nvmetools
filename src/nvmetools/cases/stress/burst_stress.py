# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os
import time

from nvmetools import TestCase, TestStep, fio, log, rqmts, steps


def burst_stress(suite, run_time_sec=5):
    """Verify drive reliability under burst IO.

    The test verifies drive reliability by running short bursts of IO stress for an extended time.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Burst stress", burst_stress.__doc__) as test:

        # -----------------------------------------------------------------------------------------
        # Step : Read NVMe info.  Stop test if critical warnings found.
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)

        # -----------------------------------------------------------------------------------------
        # Step: Get the file for fio to read and write
        # -----------------------------------------------------------------------------------------
        fio_file = steps.get_fio_stress_file(test, start_info.parameters["Size"])

        # -----------------------------------------------------------------------------------------
        # Step : Start sampling SMART and Power State
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_state_samples(test)

        # -----------------------------------------------------------------------------------------
        # Step : Run bursts of IO stress
        # -----------------------------------------------------------------------------------------
        # Run 50/50 mix of reads and writes with variety of burst lengths, queue depths, block sizes,
        # and idle times
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "IO stress", "Run bursts of IO stress with fio") as step:

            test.data["file path"] = fio_file.filepath
            test.data["fio errors"] = 0
            test.data["block sizes"] = block_sizes = [4096, 4096 * 32]
            test.data["queue depths"] = queue_depths = [1, 32]
            test.data["run time sec"] = run_time_sec = run_time_sec
            test.data["number blocks"] = number_blocks = [1, 100, 10000]
            test.data["think time"] = thinktime = [1000, 10000, 100000, 1000000, 5000000]
            test.data["sample delay sec"] = 10

            test.data["bursts"] = []

            number_runs = len(number_blocks) * len(thinktime) * len(queue_depths) * len(block_sizes)
            test.data["run time"] = run_time_sec * number_runs

            log.debug(f"Waiting {test.data['sample delay sec']} seconds to start IO")
            time.sleep(test.data["sample delay sec"])

            fio_io_errors = 0
            fio_corruption_errors = 0

            for wait_time in thinktime:
                for blocks in number_blocks:
                    for depth in queue_depths:
                        for block_size in block_sizes:

                            logfile = f"fio_{wait_time}_{number_blocks}_{depth}_{block_size}"

                            args = [
                                "--direct=1",
                                "--thread",
                                "--allow_file_create=0",
                                "--output-format=json",
                                f"--filesize={fio_file.file_size}",
                                f"--filename={fio_file.filepath}",
                                "--numjobs=1",
                                "--rw=randrw",
                                "--rwmixread=50",
                                f"--iodepth={depth}",
                                f"--bs={block_size}",
                                "--verify_interval=4096",
                                "--verify=crc32c",
                                "--verify_dump=1",
                                "--verify_state_save=0",
                                "--verify_async=1",
                                "--continue_on_error=verify",
                                f"--output={os.path.join(step.directory,f'{logfile}.json')}",
                                "--time_based",
                                f"--runtime={run_time_sec}",
                                f"--thinktime={wait_time}",
                                f"--thinktime_blocks={blocks}",
                                "--name=fio_burst_io",
                            ]
                            fio_result = fio.RunFio(args, step.directory, suite.volume, file=logfile)
                            fio_io_errors += fio_result.io_errors
                            fio_corruption_errors += fio_result.corruption_errors

                            test.data["bursts"].append(
                                {
                                    "wait time ms": wait_time,
                                    "number blocks": number_blocks,
                                    "queue depth": depth,
                                    "block size": block_size,
                                    "run time": run_time_sec,
                                    "read": f"{fio_result.data_read_gb:0.1f} GB",
                                    "read bandwidth": f"{fio_result.read_bw_gb:0.3f} GB/s",
                                    "written": f"{fio_result.data_write_gb:0.1f} GB",
                                    "write bandwidth": f"{fio_result.write_bw_gb:0.3f} GB/s",
                                }
                            )

            rqmts.no_io_errors(step, fio_io_errors)
            rqmts.no_data_corruption(step, fio_corruption_errors)

            log.debug(f"Waiting {test.data['sample delay sec']} seconds to stop sampling")
            time.sleep(test.data["sample delay sec"])

        # -----------------------------------------------------------------------------------------
        # Step : Stop reading SMART and Power State information that was started above
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Verify samples", "Stop sampling and verify no sample errors") as step:
            info_samples.stop()

            rqmts.no_counter_parameter_decrements(step, info_samples)
            rqmts.no_errorcount_change(step, info_samples)

            test.data["max temp"] = info_samples.max_temp
            test.data["time throttled"] = info_samples.time_throttled

        # -----------------------------------------------------------------------------------------
        # Step : Read NVMe info and compare against starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
