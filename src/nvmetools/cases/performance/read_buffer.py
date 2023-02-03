# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os
import random

from nvmetools import TestCase, TestStep, fio, log, rqmts, steps

DELAYED_LATENCY_IOS = 16


def read_buffer(suite):
    """Measure performance of sequential reads to same address.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Read buffer", read_buffer.__doc__) as test:

        # -----------------------------------------------------------------------------------------
        # Before test, read NVMe info and verify no critical warnings, get fio file, wait for idle
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)
        fio_file = steps.get_fio_performance_file(test)
        steps.idle_wait(test)

        # -----------------------------------------------------------------------------------------
        # Create and run the IO trace file
        # -----------------------------------------------------------------------------------------
        # This file is created for fio to do the subsequent reads to the same addresses.  Multiple
        # block sizes are run to get an idea of how big the buffer is.
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "IO", "Run IO trace file using fio") as step:

            # Create the IO trace file for fio

            offsets = random.sample(range(255), 250)
            trace_file = os.path.join(step.directory, "trace1.log")
            with open(trace_file, "w") as file_object:
                file_object.write("fio version 2 iolog\n")
                file_object.write(f"{fio_file.os_filepath} add\n")
                file_object.write(f"{fio_file.os_filepath} open\n")

                # Get to P0 power state before starting the reads

                for _index in range(DELAYED_LATENCY_IOS):
                    file_object.write(f"{fio_file.os_filepath} read 0 4096\n")

                # Now read the same address twice for different block sizes

                for size in range(1, 129, 1):
                    block_size = 4096 * size

                    for offset in offsets:
                        offset = 4096 * 1024 * offset
                        file_object.write(f"{fio_file.os_filepath} read {offset} {block_size}\n")
                        file_object.write(f"{fio_file.os_filepath} read {offset} {block_size}\n")

                file_object.write(f"{fio_file.os_filepath} close\n")

            # Now run the IO trace file

            fio_args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                "--allow_file_create=0",
                f"--filesize={fio_file.file_size}",
                f"--filename={fio_file.filepath}",
                "--read_iolog=trace1.log",
                "--iodepth=1",
                f"--output={os.path.join(step.directory,'fio.json')}",
                "--output-format=json",
                "--disable_clat=1",
                "--disable_slat=1",
                "--write_lat_log=raw",
                "--log_offset=1",
                "--name=fio_trace1",
            ]
            fio_result = fio.RunFio(fio_args, step.directory, suite.volume)
            rqmts.no_io_errors(step, fio_result)

        # -----------------------------------------------------------------------------------------
        # After test, read NVMe info and compare against the starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
