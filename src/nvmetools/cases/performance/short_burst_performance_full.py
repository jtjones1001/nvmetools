# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os
import time

from nvmetools import TestCase, TestStep, fio, rqmts, steps
from nvmetools.support.conversions import KIB_TO_GB


def short_burst_performance_full(suite):
    """Measure performance of short bursts of IO reads and writes.

    This test reports the bandwidth for short bursts of IO reads and writes.  This test is
    helpful in understanding drive performance across a variety of block sizes, queue depths,
    and IO patterns.   The four common IO patterns  are measured: sequential reads, sequential
    writes, random reads, and random writes.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Short Burst Performance Full Drive", short_burst_performance_full.__doc__) as test:

        test.data["limits"] = suite.device["Short Burst Bandwidth (GB/s)"]
        test.data["ramp time sec"] = RAMP_TIME_SEC = 0.5
        test.data["io runtime sec"] = IO_RUN_TIME_SEC = 2
        test.data["runtime sec"] = RAMP_TIME_SEC + IO_RUN_TIME_SEC
        test.data["time after write sec"] = WAIT_AFTER_WRITE_SEC = IO_RUN_TIME_SEC * 3
        test.data["time after read sec"] = WAIT_AFTER_READ_SEC = IO_RUN_TIME_SEC
        test.data["io size"] = IO_SIZE = 1024 * 1024 * 1024
        test.data["queue depths"] = QUEUE_DEPTHS = [1, 2, 8, 16, 32]
        test.data["block sizes"] = BLOCK_SIZES = [4096 * 2**x for x in range(9)]

        # -----------------------------------------------------------------------------------------
        # Before test, read NVMe info and verify no critical warnings, get fio file, wait for idle
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)
        fio_file = steps.get_fio_performance_file(test)

        steps.verify_full_drive(test, suite.volume, start_info)
        steps.idle_wait(test)

        # -----------------------------------------------------------------------------------------
        # Run short bursts of the four different IO patterns at different block sizes and queue depths
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_info_samples(test)

        for io_pattern in ["sequential write", "sequential read", "random write", "random read"]:
            io_pattern_name = io_pattern.replace(" ", "_")

            step_title = f"{io_pattern.title()}"
            step_description = f"Measure performance of short burst of {io_pattern}s."

            with TestStep(test, step_title, step_description) as step:

                fio_io_errors = 0

                test.data[io_pattern] = {"results": {}, "maximum": 0, "minimum": 99999}
                if io_pattern in ["sequential write", "random write"]:
                    io_type = "write"
                    rw = "randwrite" if io_pattern == "random write" else "write"
                else:
                    io_type = "read"
                    rw = "randread" if io_pattern == "random read" else "read"

                for depth in QUEUE_DEPTHS:
                    test.data[io_pattern]["results"][f"{depth}"] = {}
                    for block_size in BLOCK_SIZES:

                        filename = f"fio_{io_pattern_name}_{block_size}_{depth}"

                        args = [
                            "--direct=1",
                            "--thread",
                            "--numjobs=1",
                            f"--filesize={fio_file.file_size}",
                            f"--filename={fio_file.filepath}",
                            f"--rw={rw}",
                            f"--iodepth={depth}",
                            f"--bs={block_size}",
                            f"--size={IO_SIZE}",
                            "--allow_file_create=0",
                            f"--ramp_time={RAMP_TIME_SEC}",
                            f"--output={os.path.join(step.directory,f'{filename}.json')}",
                            "--output-format=json",
                            "--time_based",
                            f"--runtime={IO_RUN_TIME_SEC}",
                            "--name=fio",
                        ]
                        fio_result = fio.RunFio(args, step.directory, suite.volume, file=filename)
                        fio_io_errors += fio_result.io_errors

                        if io_type == "read":
                            bw = fio_result.read_bw_kib * KIB_TO_GB
                            lat = fio_result.read_mean_latency_ms

                            test.data[io_pattern]["results"][f"{depth}"][f"{block_size}"] = {
                                "lat": lat,
                                "bw": bw,
                                "iops": bw / block_size,
                            }
                            test.data[io_pattern]["maximum"] = max(bw, test.data[io_pattern]["maximum"])
                            test.data[io_pattern]["minimum"] = min(bw, test.data[io_pattern]["minimum"])
                            time.sleep(WAIT_AFTER_READ_SEC)

                        else:
                            bw = fio_result.write_bw_kib * KIB_TO_GB
                            lat = fio_result.write_mean_latency_ms

                            test.data[io_pattern]["results"][f"{depth}"][f"{block_size}"] = {
                                "lat": lat,
                                "bw": bw,
                                "iops": bw / block_size,
                            }
                            test.data[io_pattern]["maximum"] = max(bw, test.data[io_pattern]["maximum"])
                            test.data[io_pattern]["minimum"] = min(bw, test.data[io_pattern]["minimum"])
                            time.sleep(WAIT_AFTER_WRITE_SEC)

                rqmts.no_io_errors(step, fio_io_errors)

        steps.stop_info_samples(test, info_samples)

        # -----------------------------------------------------------------------------------------
        #  Verify performance within limits
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Verify performance", "Verify short burst performance.") as step:

            rqmts.random_read_4k_qd1_bandwidth(step, test.data)
            rqmts.random_write_4k_qd1_bandwidth(step, test.data)
            rqmts.sequential_read_128k_qd32_bandwidth(step, test.data)
            rqmts.sequential_write_128k_qd32_bandwidth(step, test.data)
            rqmts.review_io_bandwidth(step)

        # -----------------------------------------------------------------------------------------
        # After test, read NVMe info and compare against the starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
