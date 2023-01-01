# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os
import time

from nvmetools import TestCase, TestStep, fio, log, rqmts, steps


def big_file_reads(suite):
    """Measure performance of IO reads to big file.

    Args:
        suite:  Parent TestSuite instance
    """

    with TestCase(suite, "Big file reads", big_file_reads.__doc__) as test:

        # -----------------------------------------------------------------------------------------
        # Step : Read NVMe info.  Stop test if critical warnings found.
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)

        # -----------------------------------------------------------------------------------------
        # Step: Get the file for fio to read and write
        # -----------------------------------------------------------------------------------------
        # This step will stop the test if cannot find or create the file.  The test will use the
        # big file eventhough the test does not check data integrity.
        # -----------------------------------------------------------------------------------------
        fio_file = steps.get_fio_big_file(test, disk_size=float(start_info.parameters["Size"]))

        # -----------------------------------------------------------------------------------------
        # Step : Start sampling SMART and Power State
        # -----------------------------------------------------------------------------------------
        # Start reading SMART and Power State info at a regular interval until stopped.  This data
        # can be used to plot temperature, bandwidth, power states, etc.  Only read SMART and Power
        # State feature to limit impact of reading info on the IO performance
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_state_samples(test)

        test.data["block size"] = block_size_kib = 128
        test.data["queue depth"] = queue_depth = 1
        test.data["file reads"] = file_reads = 2
        test.data["io size"] = int(file_reads * test.data["file size"])
        test.data["disk size"] = float(start_info.parameters["Size"])
        test.data["file size"] = fio_file.file_size
        test.data["file ratio"] = float(fio_file.file_size / float(start_info.parameters["Size"])) * 100.0
        test.data["sample delay sec"] = 30

        # -----------------------------------------------------------------------------------------
        # Step : Read big filer with sequential reads
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Sequential reads", "Read fio big file several times using sequential reads.") as step:

            log.debug(f"Waiting {test.data['sample delay sec']} seconds to start IO")
            time.sleep(test.data["sample delay sec"])

            fio_args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                f"--filename={fio_file.filepath}",
                f"--filesize={fio_file.file_size}",
                "--allow_file_create=0",
                "--rw=read",
                f"--iodepth={queue_depth}",
                f"--bs={block_size_kib*1024}",
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

        # -----------------------------------------------------------------------------------------
        # Step : Stop reading SMART and Power State information that was started above
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Verify samples", "Stop sampling and verify no sample errors") as step:
            info_samples.stop()
            rqmts.no_counter_parameter_decrements(step, info_samples)
            rqmts.no_errorcount_change(step, info_samples)

        # -----------------------------------------------------------------------------------------
        # Step : Start sampling SMART and Power State (random reads)
        # -----------------------------------------------------------------------------------------
        info_samples = steps.start_state_samples(test)

        # -----------------------------------------------------------------------------------------
        # Step : Random reads
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Random reads", "Read fio big file several times using random reads.") as step:

            log.debug(f"Waiting {test.data['sample delay sec']} seconds to start IO")
            time.sleep(test.data["sample delay sec"])

            fio_args = [
                "--direct=1",
                "--thread",
                "--numjobs=1",
                "--allow_file_create=0",
                f"--filename={fio_file.filepath}",
                f"--filesize={fio_file.file_size}",
                "--rw=randread",
                f"--iodepth={queue_depth}",
                f"--bs={block_size_kib*1024}",
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

            log.debug(f"Waiting {test.data['sample delay sec']} seconds for drive to cool down")
            time.sleep(test.data["sample delay sec"])

        # -----------------------------------------------------------------------------------------
        # Step : Stop reading SMART and Power State information that was started above
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Verify samples", "Stop sampling and verify no sample errors") as step:
            info_samples.stop()
            rqmts.no_counter_parameter_decrements(step, info_samples)
            rqmts.no_errorcount_change(step, info_samples)

        # -----------------------------------------------------------------------------------------
        # Step : Read NVMe info and compare against starting info
        # -----------------------------------------------------------------------------------------
        # This test reads the full information and verifies no counter decrements, static parameter
        # changes, no critical warnings, and no error count increases.
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
