# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os
import time

from nvmetools import TestCase, TestStep, fio, log, rqmts, steps
from nvmetools.support.conversions import BYTES_IN_GIB, BYTES_IN_KIB


def data_compression(suite):
    """Measure performance difference between compressible and incompressible data.

    The test measures the average latency for reads and writes using incompressible
    data (random data) and compressible data (all zeros).  Drives that implement
    data compression will have lower latency on compressible data.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Data compression", data_compression.__doc__) as test:

        test.data["wait after io sec"] = WAIT_AFTER_IO_SEC = 20
        test.data["io size gib"] = IO_SIZE_GIB = 2

        # -----------------------------------------------------------------------------------------
        # Before test, read NVMe info and verify no critical warnings, get fio file, wait for idle
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)
        fio_file = steps.get_fio_big_file(test, disk_size=float(start_info.parameters["Size"]))
        steps.wait_for_idle(test)

        # -----------------------------------------------------------------------------------------
        #  Run IO with compressible and incompressible data
        # -----------------------------------------------------------------------------------------
        # This section runs IO patterns with compressible data (all zeros) and incompressible data
        # (random).  The 4 patterns are sequential read/write and random read/write.  Because this
        # is a performance test no data integrity is checked.
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_info_samples(test)

        for data_type in ["random", "zero"]:
            for io_type in ["write", "read", "randwrite", "randread"]:

                if io_type in ["read", "write"]:
                    block_size_kib = 128
                    io_pattern = f"Sequential {io_type.capitalize()}, 128 KiB, QD1"
                    io_short = f"{io_type} 128K"

                else:
                    block_size_kib = 8
                    if io_type == "randread":
                        io_pattern = "Random Read, 8 KiB, QD1"
                        io_short = "random read 8K"
                    else:
                        io_pattern = "Random Write, 8 KiB, QD1"
                        io_short = "random write 8K"

                if data_type == "random":
                    title = f"Random data {io_short}"
                    description = f"{io_pattern} with incompressible data."
                else:
                    title = f"Zero data {io_short}"
                    description = f"{io_pattern} with compressible data."

                with TestStep(test, title, description) as step:

                    args = [
                        "--direct=1",
                        "--thread",
                        "--numjobs=1",
                        "--allow_file_create=0",
                        f"--filesize={fio_file.file_size}",
                        f"--filename={fio_file.filepath}",
                        f"--rw={io_type}",
                        "--iodepth=1",
                        f"--bs={block_size_kib*BYTES_IN_KIB}",
                        f"--size={IO_SIZE_GIB*BYTES_IN_GIB}",
                        f"--output={os.path.join(step.directory,'fio.json')}",
                        "--output-format=json",
                        "--disable_clat=1",
                        "--disable_slat=1",
                        "--write_lat_log=raw",
                        "--name=fio",
                    ]
                    if data_type == "zero":
                        args.append("--zero_buffers")

                    fio_result = fio.RunFio(args, step.directory, suite.volume)
                    rqmts.no_io_errors(step, fio_result)

                    if io_type == "randread" or io_type == "read":
                        test.data[f"{io_pattern} {data_type}"] = fio_result.delayed_mean_read_latency_us
                    else:
                        test.data[f"{io_pattern} {data_type}"] = fio_result.delayed_mean_write_latency_us

                if io_type in ["write", "randwrite"]:
                    log.debug(f"Waiting {WAIT_AFTER_IO_SEC} seconds to ensure drive is idle.")
                    time.sleep(WAIT_AFTER_IO_SEC)

        steps.stop_info_samples(test, info_samples)

        # -----------------------------------------------------------------------------------------
        # After test, read NVMe info and compare against the starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
