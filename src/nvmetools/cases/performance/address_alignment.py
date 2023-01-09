# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os

from nvmetools import TestCase, TestStep, fio, rqmts, steps


def address_alignment(suite):
    """Measure performance on multiple reads to the same address offsets.

    This test is only for reference.  It measures the latency of multiple reads to the same address
    offset. Queue a large number of reads at different random addresses but with the same offset.
    Several different offsets are measured.  This provides details on the architecture of the device
    interleaving.  This is a performance measurement so no data verification is done.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Address alignment", address_alignment.__doc__) as test:

        test.data["reported ios"] = 1024
        test.data["delayed ios"] = fio.RunFio.FIO_DELAY_IOS

        queue_depth = test.data["queue depth"] = 32
        block_size_kib = test.data["block size kib"] = 4
        total_ios = test.data["total ios"] = test.data["reported ios"] + test.data["delayed ios"]
        max_offset_4kib = test.data["max offset in 4kib"] = 257

        # -----------------------------------------------------------------------------------------
        #  Read NVMe info.  Stop test if critical warnings found.
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)

        # -----------------------------------------------------------------------------------------
        # Step: Get the file for fio to read and write
        # -----------------------------------------------------------------------------------------
        # This step will stop the test if cannot find or create the file.  The test requires the
        # big file. Since this is a stress test it must check the data integrity so the file will
        # be created with verify=True.  Note big files always have verify=True
        # -----------------------------------------------------------------------------------------
        fio_file = steps.get_fio_big_file(test, disk_size=float(start_info.parameters["Size"]))

        # -----------------------------------------------------------------------------------------
        #  Random reads at same offset
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Random IO reads", "Read IO at random address offsets") as step:

            test.data["read latency us"] = {}
            fio_io_errors = 0

            for offset_kib in range(4, 4 * max_offset_4kib, 4):
                filename = f"fio_{offset_kib}"
                fio_args = [
                    "--direct=1",
                    "--thread",
                    "--numjobs=1",
                    "--allow_file_create=0",
                    f"--filename={fio_file.filepath}",
                    f"--filesize={fio_file.file_size}",
                    "--rw=randread",
                    f"--iodepth={queue_depth}",
                    f"--bs={block_size_kib * 1024}",
                    f"--number_ios={total_ios}",
                    f"--blockalign={offset_kib * 1024}",
                    "--norandommap=1",
                    f"--output={os.path.join(step.directory,f'{filename}.json')}",
                    "--output-format=json",
                    "--disable_clat=1",
                    "--disable_slat=1",
                    f"--write_lat_log=raw_{offset_kib}",
                    "--log_offset=1",
                    "--name=fio_random_reads",
                ]
                fio_result = fio.RunFio(
                    fio_args,
                    step.directory,
                    suite.volume,
                    file=filename,
                    lat_file=f"raw_{offset_kib}",
                )
                fio_io_errors += fio_result.io_errors

                test.data["read latency us"][offset_kib] = fio_result.delayed_mean_read_latency_us

            rqmts.no_io_errors(step, fio_io_errors)

        # -----------------------------------------------------------------------------------------
        #  Read NVMe info and compare against starting info
        # -----------------------------------------------------------------------------------------
        # This test reads the full information and verifies no counter decrements, static parameter
        # changes, no critical warnings, and no error count increases.
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
