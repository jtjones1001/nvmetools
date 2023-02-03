# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os

from nvmetools import TestCase, TestStep, fio, log, rqmts, steps


def read_disturb_stress(suite):
    """Verify read disturb mitigations.

    The test verifies the drive has mitigations for the read disturb effect.  It
    attempts to read the same page in several blocks several million times.  This
    will shift the threshold of the pages which are not read unless mitigation is
    in place.

    After the same page has been read several million times all of the pages are
    read and verified.

     Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Read disturb stress", read_disturb_stress.__doc__) as test:

        test.data["read size"] = READ_SIZE = 4096
        test.data["page size"] = PAGE_SIZE = 4096 * 4
        test.data["block size"] = BLOCK_SIZE = 256 * PAGE_SIZE
        test.data["address increment"] = ADDRESS_INCREMENT = BLOCK_SIZE * 16
        test.data["file size"] = FILE_SIZE = 1024 * 1024 * 1024
        test.data["reads per page"] = READS_PER_PAGE = 100000

        # -----------------------------------------------------------------------------------------
        # Before test, read NVMe info and verify no critical warnings, get fio file, wait for idle
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)
        fio_file = steps.get_fio_small_file(test)
        steps.idle_wait(test)

        # -----------------------------------------------------------------------------------------
        # Write the file to use.  Write and verify the target file. Write 2x the file size so that
        # the final data in the file will, hopefully, be created using "new" blocks where all the
        # pages in the new blocks are mapped to sequentially to the LBA
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_info_samples(test)

        with TestStep(test, "Write verify file") as step:

            args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                "--allow_file_create=0",
                f"--filesize={fio_file.file_size}",
                f"--filename={fio_file.filepath}",
                "--rw=write",
                "--iodepth=16",
                "--bs=128k",
                f"--verify_interval={READ_SIZE}",
                f"--size={FILE_SIZE}",
                f"--io_size={2*FILE_SIZE}",
                "--verify=crc32c",
                "--verify_dump=1",
                "--verify_state_save=0",
                "--verify_async=2",
                "--continue_on_error=verify",
                f"--output={os.path.join(step.directory,'fio.json')}",
                "--output-format=json",
                "--name=fio",
            ]
            fio_write = fio.RunFio(args, step.directory, suite.volume)
            rqmts.no_io_errors(step, fio_write)
            rqmts.no_data_corruption(step, fio_write)

        # -----------------------------------------------------------------------------------------
        # Read one page every block (hopefully). Read one page every block size offset in the file.
        # If NPDG available use this for block size, else use default.  Note that reading a value
        # smaller than page size still results in the entire page being read from the flash.
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Read pages") as step:

            pages_in_file = FILE_SIZE / ADDRESS_INCREMENT
            test.data["read size"] = READ_SIZE
            test.data["pages per file"] = pages_in_file
            test.data["file size gb"] = FILE_SIZE / 1024 / 1024 / 1024

            args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                "--allow_file_create=0",
                f"--filesize={fio_file.file_size}",
                f"--filename={fio_file.filepath}",
                f"--rw=read:{ADDRESS_INCREMENT}",
                "--iodepth=16",
                f"--bs={READ_SIZE}",
                f"--size={FILE_SIZE}",
                "--io_size=900g",
                "--verify=crc32c",
                "--verify_dump=1",
                "--verify_state_save=0",
                "--verify_async=2",
                "--continue_on_error=verify",
                f"--output={os.path.join(step.directory,'fio.json')}",
                "--output-format=json",
                f"--number_ios={int(pages_in_file*READS_PER_PAGE)}",
                "--name=fio",
            ]
            fio_result = fio.RunFio(args, step.directory, suite.volume)
            rqmts.no_io_errors(step, fio_result)
            rqmts.no_data_corruption(step, fio_result)

            test.data["total reads"] = fio_result.read_ios
            test.data["reads per page"] = test.data["total reads"] / pages_in_file

            log.debug(f"    Read Latency (ms)      : {fio_result.read_mean_latency_ms:0.3f}")
            log.debug(f"    Total Reads            : {test.data['total reads'] :,.0f}")
            log.debug(f"    Total Reads Per Offset : {test.data['reads per page']:,.0f}")
            log.debug("")

        # -----------------------------------------------------------------------------------------
        #  Read every page in the file to determine if a page was corrupted by read disturb
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Read all pages") as step:

            args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                "--allow_file_create=0",
                f"--filesize={fio_file.file_size}",
                f"--filename={fio_file.filepath}",
                "--rw=read",
                "--iodepth=16",
                "--bs=128k",
                f"--verify_interval={READ_SIZE}",
                "--verify=crc32c",
                "--verify_dump=1",
                "--verify_state_save=0",
                "--verify_async=2",
                "--continue_on_error=verify",
                f"--size={FILE_SIZE}",
                f"--output={os.path.join(step.directory,'fio.json')}",
                "--output-format=json",
                "--name=fio",
            ]
            fio_verify = fio.RunFio(args, step.directory, suite.volume)
            rqmts.no_io_errors(step, fio_verify)
            rqmts.no_data_corruption(step, fio_verify)

        steps.stop_info_samples(test, info_samples)

        # -----------------------------------------------------------------------------------------
        # After test, read NVMe info and compare against the starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
