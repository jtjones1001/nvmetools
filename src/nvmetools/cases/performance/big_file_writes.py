# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import csv
import math
import os
import time

from nvmetools import TestCase, TestStep, fio, log, rqmts, steps
from nvmetools.support.conversions import BYTES_IN_GB, BYTES_IN_GIB, BYTES_IN_KIB, KIB_TO_GB, MS_IN_SEC


def _get_bigfile_cache_info(fio_bw_log, index, file_size, cache_limit=None):

    file_data = 0
    file_time = 0

    cache_data = 0
    cache_time = 0

    total_data = 0
    total_time = 0

    start = (index * file_size) / BYTES_IN_GB
    end = ((index + 1) * file_size) / BYTES_IN_GB

    with open(fio_bw_log, newline="") as file_object:
        rows = csv.reader(file_object)
        for row in rows:
            sample_time = int(row[0]) / MS_IN_SEC - total_time
            sample_data = int(row[1]) * KIB_TO_GB * sample_time
            total_data += sample_data
            total_time += sample_time

            if total_data >= start and total_data < end:
                file_data += sample_data
                file_time += sample_time
        if file_time == 0:
            average_bandwidth = 0
            average_cache_bandwidth = 0
        else:
            average_bandwidth = file_data / file_time
            if cache_limit is None:
                cache_limit = average_bandwidth * 2

            total_data = 0
            total_time = 0

            file_object.seek(0)
            rows = csv.reader(file_object)
            for row in rows:
                sample_time = int(row[0]) / MS_IN_SEC - total_time
                sample_data = int(row[1]) * KIB_TO_GB * sample_time
                total_data += sample_data
                total_time += sample_time

                if total_data >= start and total_data < end:
                    if int(row[1]) * KIB_TO_GB > cache_limit:
                        cache_data += sample_data
                        cache_time += sample_time

            if cache_time == 0:
                average_cache_bandwidth = 0
            else:
                average_cache_bandwidth = cache_data / cache_time

    return (file_data, average_bandwidth, cache_data, average_cache_bandwidth)


def big_file_writes(suite):
    """Measure performance of IO writes to big file.

    Measures the average bandwidth to continuously write a big file to identify behavior of write
    cache, thermal throttling, and logical-physical mapping.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Big file writes", big_file_writes.__doc__) as test:

        test.data["multiple file writes"] = FILE_WRITES = 3
        test.data["block size kib"] = BLOCK_SIZE_KIB = 128
        test.data["queue depth"] = QUEUE_DEPTH = 32
        test.data["burst delay sec"] = BURST_DELAY_SEC = [1, 2, 4, 8, 16, 32, 64, 0]
        test.data["file writes"] = []
        test.data["bursts"] = []
        # -----------------------------------------------------------------------------------------
        # Before test, read NVMe info and verify no critical warnings
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)

        test.data["disk size"] = disk_size = float(start_info.parameters["Size"])

        # -----------------------------------------------------------------------------------------
        # Get the information for the fio big file but don't create it.  The drive should be empty
        # at the start of this test so verify that.  Then wait for idle before starting the test.
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Get fio file", "Get big file info but don't create.") as step:
            fio_files = fio.FioFiles(step.directory, test.suite.volume)
            fio_file = fio_files.get(big=True, disk_size=disk_size)

        test.data["file size"] = fio_file.file_size
        test.data["io size"] = int(FILE_WRITES * test.data["file size"])

        test.data["file size gb"] = fio_file.file_size / BYTES_IN_GB
        test.data["fio filepath"] = fio_file.os_filepath
        test.data["file ratio"] = float(fio_file.file_size / float(disk_size)) * 100.0

        steps.verify_empty_drive(test, suite.volume, start_info)
        steps.idle_wait(test)

        # -----------------------------------------------------------------------------------------
        # Run continuous sequential writes for multiple times the file size
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_info_samples(test)

        with TestStep(test, "Multiple file writes", "Write big file multiple times.") as step:

            fio_args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                f"--filename={fio_file.filepath}",
                f"--filesize={fio_file.file_size}",
                "--rw=write",
                f"--iodepth={QUEUE_DEPTH}",
                f"--bs={BLOCK_SIZE_KIB*BYTES_IN_KIB}",
                f"--output={os.path.join(step.directory,'fio.json')}",
                "--output-format=json",
                "--write_bw_log=raw",
                "--log_offset=1",
                "--log_avg_ms=100",
                f"--io_size={test.data['io size']}",
                "--verify_interval=4096",
                "--verify=crc32c",
                "--do_verify=0",
                "--name=fio_cont_writes",
            ]
            bandwidth_file = os.path.join(step.directory, "raw_bw.1.log")
            fio_result = fio.RunFio(fio_args, step.directory, suite.volume)
            rqmts.no_io_errors(step, fio_result)

            test.data["bw"] = {"continuous": fio_result.write_bw_kib * BYTES_IN_KIB}

        steps.stop_info_samples(test, info_samples)

        for write in range(FILE_WRITES):
            write_data = _get_bigfile_cache_info(bandwidth_file, write, fio_file.file_size)
            test.data["file writes"].append(
                {
                    "number": write + 1,
                    "data": write_data[0],
                    "bw": write_data[1],
                    "cache data": write_data[2],
                    "cache bw": write_data[3],
                }
            )

        # -----------------------------------------------------------------------------------------
        # Wait for idle before starting bursts.  This should allow any SLC to catch up before the
        # bursts begin
        # -----------------------------------------------------------------------------------------
        steps.idle_wait(test)

        with TestStep(test, "Active wait", "Intermittent reads to avoid low power states.") as step:
            fio_args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                f"--filename={fio_file.filepath}",
                f"--filesize={fio_file.file_size}",
                "--rw=write",
                "--iodepth=1",
                f"--bs={4*BYTES_IN_KIB}",
                f"--output={os.path.join(step.directory,'fio.json')}",
                "--output-format=json",
                f"--io_size={test.data['file size']}",
                "--verify_interval=4096",
                "--verify=crc32c",
                "--do_verify=0",
                "--thinktime=1000",
                "--thinktime_blocks=1",
                "--time_based",
                "--runtime=60",
                "--name=read_waits",
            ]
            fio_result = fio.RunFio(fio_args, step.directory, suite.volume)
            rqmts.no_io_errors(step, fio_result)

        # -----------------------------------------------------------------------------------------
        # Run continuous sequential writes for one time the file size, start at the half way part
        # of the file
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_info_samples(test)

        with TestStep(test, "Half file write", "Write second half of big file.") as step:

            fio_args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                f"--filename={fio_file.filepath}",
                f"--filesize={fio_file.file_size}",
                "--rw=write",
                "--offset=50%",
                f"--iodepth={QUEUE_DEPTH}",
                f"--bs={BLOCK_SIZE_KIB*BYTES_IN_KIB}",
                f"--output={os.path.join(step.directory,'fio.json')}",
                "--output-format=json",
                "--write_bw_log=raw",
                "--log_offset=1",
                "--log_avg_ms=100",
                f"--io_size={int(test.data['file size']/2)}",
                "--verify_interval=4096",
                "--verify=crc32c",
                "--do_verify=0",
                "--name=fio_cont_writes",
            ]
            bandwidth_file = os.path.join(step.directory, "raw_bw.1.log")
            fio_result = fio.RunFio(fio_args, step.directory, suite.volume)
            rqmts.no_io_errors(step, fio_result)

            test.data["bw"] = {"continuous": fio_result.write_bw_kib * BYTES_IN_KIB}

        steps.stop_info_samples(test, info_samples)

        write_data = _get_bigfile_cache_info(bandwidth_file, 0, fio_file.file_size)
        test.data["file writes"].append(
            {
                "number": FILE_WRITES + 1,
                "data": write_data[0],
                "bw": write_data[1],
                "cache data": write_data[2],
                "cache bw": write_data[3],
            }
        )

        # Get size of write cache in last file write in case it is dynamically sized

        if write_data[2] == 0:
            cache_size_gb = 4
            cache_limit = None
        else:
            cache_size_gb = round(write_data[2], 1)
            cache_limit = write_data[1] * 2

        test.data["write cache limit"] = cache_limit
        test.data["write cache size"] = BURST_IO_SIZE = int(cache_size_gb * BYTES_IN_GB)

        # -----------------------------------------------------------------------------------------
        # Wait for idle before starting bursts.  This should allow any SLC to catch up before the
        # bursts begin
        # -----------------------------------------------------------------------------------------
        steps.idle_wait(test)

        # -----------------------------------------------------------------------------------------
        # Run IO write bursts at random offsets
        # Use fio to run IO bursts at random offsets in the big file aligned on GiB boundaries
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_info_samples(test)

        with TestStep(test, "Burst writes", "Write big file in several bursts.") as step:

            predelay = 180  # 180 idle and 60 active
            fio_io_errors = 0
            offset = 0

            for index, delay in enumerate(BURST_DELAY_SEC):
                burst_number = index + 1
                fio_args = [
                    "--direct=1",
                    "--thread",
                    "--numjobs=1",
                    f"--filename={fio_file.filepath}",
                    f"--filesize={fio_file.file_size}",
                    "--allow_file_create=0",
                    "--rw=write",
                    f"--iodepth={QUEUE_DEPTH}",
                    f"--bs={BLOCK_SIZE_KIB*BYTES_IN_KIB}",
                    f"--offset={offset}",
                    f"--output={os.path.join(step.directory,f'fio_burst_{delay}s_{burst_number}.json')}",
                    "--output-format=json",
                    f"--write_bw_log=burst_{delay}s_{burst_number}",
                    "--log_avg_ms=100",
                    f"--io_size={BURST_IO_SIZE}",
                    "--verify_interval=4096",
                    "--verify=crc32c",
                    "--do_verify=0",
                    "--name=fio_burst_writes",
                ]
                fio_result = fio.RunFio(
                    fio_args, step.directory, suite.volume, file=f"fio_burst_{delay}s_{burst_number}"
                )
                fio_io_errors += fio_result.io_errors

                bandwidth_file = os.path.join(step.directory, f"burst_{delay}s_{burst_number}_bw.1.log")
                write_data = _get_bigfile_cache_info(
                    bandwidth_file, 0, fio_file.file_size, cache_limit=cache_limit
                )
                test.data["bursts"].append(
                    {
                        "number": burst_number,
                        "delay": predelay,
                        "data": write_data[0],
                        "bw": write_data[1],
                        "cache data": write_data[2],
                        "cache bw": write_data[3],
                    }
                )
                offset =  math.ceil((offset + BURST_IO_SIZE) / BYTES_IN_GIB) * BYTES_IN_GIB
                if (offset + BURST_IO_SIZE) > fio_file.file_size:
                    offset = 0


                predelay = delay
                time.sleep(delay)

            rqmts.no_io_errors(step, fio_io_errors)

        steps.stop_info_samples(test, info_samples)

        rqmts.review_first_burst_bandwidth(step)

        # -----------------------------------------------------------------------------------------
        # After test, read NVMe info and compare against the starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
