# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os
import time

from nvmetools import TestCase, TestStep, fio, log, rqmts, steps
from nvmetools.support.conversions import BYTES_IN_GIB, BYTES_IN_KIB


def _get_repeats(filepath, length):
    repeats = 0
    with open(filepath, "rb") as file_object:
        initial_kib = file_object.read(length)
        while block := file_object.read(length):
            for index, byte in enumerate(block):
                if byte != initial_kib[index]:
                    break
                if index == (length - 1):
                    repeats += 1
    return repeats


def data_deduplication(suite):
    """Measure performance difference between duplicate and non-duplicate data.

    Measures the average latency for writes using unique data (different random data for
    every block) and repeating data (same random data for every block).  Drives that implement
    data deduplication will have lower latency on duplicate data.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Data deduplication", data_deduplication.__doc__) as test:

        test.data["wait after io sec"] = WAIT_AFTER_IO_SEC = 20
        test.data["io size gib"] = IO_SIZE_GIB = 2
        test.data["block sizes"] = BLOCK_SIZES_KIB = [4, 8, 32, 128]

        # -----------------------------------------------------------------------------------------
        # Before test, read NVMe info and verify no critical warnings, get fio file, wait for idle
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)
        fio_file = steps.get_fio_performance_file(test)
        steps.wait_for_idle(test)

        # -----------------------------------------------------------------------------------------
        # Run IO with unique and duplicate data
        # -----------------------------------------------------------------------------------------
        # This step writes IO patterns with unique data (all random) and 100 percent duplicate data.
        # The performance is compared to determine if the drive uses any techniques to reduce
        # duplicate data.  This is a performance test so no data integrity checking is done.
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_info_samples(test)

        for data_type in ["unique", "duplicate"]:
            for block_size_kib in BLOCK_SIZES_KIB:

                title = f"{block_size_kib}K {data_type} writes"
                description = f"Writing {data_type} patterns with block size of {block_size_kib}K."

                with TestStep(test, title, description) as step:

                    args = [
                        "--direct=1",
                        "--thread",
                        "--numjobs=1",
                        "--allow_file_create=0",
                        f"--filesize={fio_file.file_size}",
                        f"--filename={fio_file.filepath}",
                        "--rw=write",
                        "--iodepth=1",
                        f"--bs={block_size_kib*BYTES_IN_KIB}",
                        f"--size={IO_SIZE_GIB*BYTES_IN_GIB}",
                        f"--output={os.path.join(step.directory,'fio.json')}",
                        "--output-format=json",
                        "--disable_clat=1",
                        "--disable_slat=1",
                        "--write_lat_log=raw",
                        "--refill_buffers",
                        "--name=fio",
                    ]
                    if data_type == "duplicate":
                        args.append("--dedupe_percentage=100")

                    fio_result = fio.RunFio(args, step.directory, suite.volume)
                    rqmts.no_io_errors(step, fio_result)

                    latency = fio_result.delayed_mean_write_latency_us
                    test.data[f"Sequential Write, {block_size_kib} KiB, QD1 {data_type}"] = latency

                    # Verify the io file created has the correct data type (unique or repeating)

                    if data_type == "duplicate":

                        # On duplicate data the data repeats for every block, for example in an 8K
                        # file with 4K block size there should be one repeat.

                        repeats = _get_repeats(fio_file.os_filepath, block_size_kib * BYTES_IN_KIB)
                        expected_repeats = fio_file.file_size / (block_size_kib * BYTES_IN_KIB) - 1

                        if repeats != expected_repeats:
                            raise Exception(f"""Found {repeats} when expected {expected_repeats}""")

                    else:

                        # There should be no repeats in the random data, check for any repeats on
                        # 1K size

                        repeats = _get_repeats(fio_file.os_filepath, 1 * BYTES_IN_KIB)

                        if repeats > 0:
                            log.error(f"Found {repeats} repeats when not expected")
                            raise Exception(f"Found {repeats} data repeats in random data.")

                log.debug(f"Waiting {WAIT_AFTER_IO_SEC} seconds to ensure drive is idle.")
                time.sleep(WAIT_AFTER_IO_SEC)

        steps.stop_info_samples(test, info_samples)

        # -----------------------------------------------------------------------------------------
        # After test, read NVMe info and compare against the starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
