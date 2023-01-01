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
        test.data["block sizes"] = BLOCK_SIZES = [
            4096,
            8192,
            4 * 4096,
            8 * 4096,
            16 * 4096,
            32 * 4096,
            64 * 4096,
            128 * 4096,
            256 * 4096,
        ]

        # -----------------------------------------------------------------------------------------
        # Step : Read NVMe info.  Stop test if critical warnings found.
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)

        # -----------------------------------------------------------------------------------------
        # Step: Get the file for fio to read and write
        # -----------------------------------------------------------------------------------------
        # This step will stop the test if cannot find or create the file.  The test requires the
        # big file. Since this is a stress test it must check the data integrity so the file will
        # be created with verify=True.  Note big files always have verify=True
        # -----------------------------------------------------------------------------------------
        fio_file = steps.get_fio_performance_file(test)

        # -----------------------------------------------------------------------------------------
        # Step : Start sampling SMART and Power State
        # -----------------------------------------------------------------------------------------
        # Start reading SMART and Power State info at a regular interval until stopped.  This data
        # can be used to plot temperature, bandwidth, power states, etc.  Only read SMART and Power
        # State feature to limit impact of reading info on the IO performance
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_state_samples(test)

        # -----------------------------------------------------------------------------------------
        # Step : Run short burst of IO reads and writes
        # -----------------------------------------------------------------------------------------
        # Run short bursts of the four different IO patterns at different block sizes and queue depths
        # -----------------------------------------------------------------------------------------
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

        # -----------------------------------------------------------------------------------------
        # Step : Stop reading SMART and Power State information that was started above
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Verify samples", "Stop sampling and verify no sample errors") as step:
            time.sleep(2)
            info_samples.stop()

            rqmts.no_counter_parameter_decrements(step, info_samples)
            rqmts.no_errorcount_change(step, info_samples)

        # -----------------------------------------------------------------------------------------
        # Step : Verify performance within limits
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Verify performance", "Verify short burst performance.") as step:

            rqmts.random_read_4k_qd1_bandwidth(step, test.data)
            rqmts.random_write_4k_qd1_bandwidth(step, test.data)
            rqmts.sequential_read_128k_qd32_bandwidth(step, test.data)
            rqmts.sequential_write_128k_qd32_bandwidth(step, test.data)
            rqmts.bandwidth_vs_qd_bs(step)

        # -----------------------------------------------------------------------------------------
        # Step : Read NVMe info and compare against starting info
        # -----------------------------------------------------------------------------------------
        # This test reads the full information and verifies no counter decrements, static parameter
        # changes, no critical warnings, and no error count increases.
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
