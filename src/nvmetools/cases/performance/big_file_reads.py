# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os

from nvmetools import TestCase, TestStep, fio, log, rqmts, steps


def big_file_reads(suite):
    """Measure performance of IO reads to big file.

    Measure the average bandwidth to read a big file twice.  The file size is 90% of the disk size.
    The bandwidth is measured for both sequential reads and random reads.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Big file reads", big_file_reads.__doc__) as test:

        test.data["block size"] = BLOCK_SIZE_KIB = 128
        test.data["queue depth"] = QUEUE_DEPTH = 1
        test.data["file reads"] = FILE_READS = 2

        # -----------------------------------------------------------------------------------------
        # Before test, read NVMe info and verify no critical warnings, get fio file, wait for idle
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)
        fio_file = steps.get_fio_big_file(test, disk_size=float(start_info.parameters["Size"]))
        steps.wait_for_idle(test)

        test.data["io size"] = int(FILE_READS * fio_file.file_size)
        test.data["disk size"] = float(start_info.parameters["Size"])

        # -----------------------------------------------------------------------------------------
        # Read big file with sequential reads
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_info_samples(test)

        with TestStep(test, "Sequential reads", "Read big file several times using sequential reads.") as step:
            fio_args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                f"--filename={fio_file.filepath}",
                f"--filesize={fio_file.file_size}",
                "--allow_file_create=0",
                "--rw=read",
                f"--iodepth={QUEUE_DEPTH}",
                f"--bs={BLOCK_SIZE_KIB*1024}",
                f"--output={os.path.join(step.directory,'fio.json')}",
                "--output-format=json",
                "--disable_clat=1",
                "--disable_slat=1",
                "--write_lat_log=raw",
                f"--io_size={test.data['io size']}",
                "--name=fio_seq_read",
            ]
            fio_result = fio.RunFio(fio_args, step.directory, suite.volume)
            rqmts.no_io_errors(step, fio_result)
            rqmts.no_data_corruption(step, fio_result)

        steps.stop_info_samples(test, info_samples)

        # -----------------------------------------------------------------------------------------
        # Read big file with random reads
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_info_samples(test)

        with TestStep(test, "Random reads", "Read fio big file several times using random reads.") as step:
            fio_args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                "--allow_file_create=0",
                f"--filename={fio_file.filepath}",
                f"--filesize={fio_file.file_size}",
                "--rw=randread",
                f"--iodepth={QUEUE_DEPTH}",
                f"--bs={BLOCK_SIZE_KIB*1024}",
                f"--output={os.path.join(step.directory,'fio.json')}",
                "--output-format=json",
                "--disable_clat=1",
                "--disable_slat=1",
                "--write_lat_log=raw",
                f"--io_size={test.data['io size']}",
                "--name=fio_random_reads",
            ]
            fio_result = fio.RunFio(fio_args, step.directory, suite.volume)
            rqmts.no_io_errors(step, fio_result)
            rqmts.no_data_corruption(step, fio_result)

        steps.stop_info_samples(test, info_samples)

        # -----------------------------------------------------------------------------------------
        # After test, read NVMe info and compare against the starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
