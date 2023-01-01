# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os
import random
import time

from nvmetools import InfoSamples, TestCase, TestStep, fio, log, rqmts, steps
from nvmetools.support.conversions import BYTES_IN_GB, BYTES_IN_GIB, BYTES_IN_KIB, MS_IN_SEC


def big_file_writes(suite):
    """Measure performance of IO writes to big file."""

    with TestCase(suite, "Big file writes", big_file_writes.__doc__) as test:

        test.data["file writes"] = FILE_WRITES = 2.5
        test.data["block size kib"] = BLOCK_SIZE_KIB = 128
        test.data["queue depth"] = QUEUE_DEPTH = 16
        test.data["burst io size"] = BURST_IO_SIZE = 2 * BYTES_IN_GIB

        test.data["burst delay sec"] = BURST_DELAY_SEC = [16, 8, 4, 2, 1]
        test.data["inter burst delay sec"] = INTER_BURST_DELAY_SEC = 30
        test.data["burst offsets"] = NUMBER_OF_BURST_OFFSETS = 6

        test.data["wait for idle sec"] = WAIT_FOR_IDLE_SEC = 180

        INFO_SAMPLE_DELAY_SEC = 5

        # -----------------------------------------------------------------------------------------
        # Step : Read NVMe info.  Stop test if critical warnings found.
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)

        test.data["disk size"] = float(start_info.parameters["Size"])
        # -----------------------------------------------------------------------------------------
        # Step: Get the file for fio to read and write
        # -----------------------------------------------------------------------------------------
        fio_file = steps.get_fio_big_file(test, disk_size=float(start_info.parameters["Size"]))

        test.data["io size"] = int(FILE_WRITES * test.data["file size"])
        # -----------------------------------------------------------------------------------------
        # Step : Run continuous sequential writes
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Continuous writes") as step:

            log.debug(f"Waiting {WAIT_FOR_IDLE_SEC} seconds to ensure drive is idle.")
            time.sleep(WAIT_FOR_IDLE_SEC)

            info_samples = InfoSamples(
                suite.nvme,
                directory=step.directory,
                wait=False,
                samples=100000,
                interval=1000,
                cmd_file="state",
            )
            log.debug(f"Waiting {INFO_SAMPLE_DELAY_SEC} seconds to start IO")
            time.sleep(INFO_SAMPLE_DELAY_SEC)

            # Use fio utility to generate the high BW sequential writes

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

            fio_result = fio.RunFio(fio_args, step.directory, suite.volume)
            rqmts.no_io_errors(step, fio_result)

            test.data["bw"] = {}
            test.data["bw"]["continuous"] = fio_result.write_bw_kib * BYTES_IN_KIB

            log.debug(f"Continuous bandwidth : {test.data['bw']['continuous'] }")

            log.debug(f"Waiting {INFO_SAMPLE_DELAY_SEC} seconds to stop sampling")
            time.sleep(INFO_SAMPLE_DELAY_SEC)

            info_samples.stop()
            rqmts.no_counter_parameter_decrements(step, info_samples)
            rqmts.no_static_parameter_changes(step, info_samples)
            rqmts.no_errorcount_change(step, info_samples)

        # -----------------------------------------------------------------------------------------
        # Step : Run IO write bursts at random offsets
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Burst writes") as step:

            log.debug(f"Waiting {WAIT_FOR_IDLE_SEC} seconds to ensure drive is idle.")
            time.sleep(WAIT_FOR_IDLE_SEC)

            info_samples = InfoSamples(
                suite.nvme,
                directory=step.directory,
                wait=False,
                samples=100000,
                interval=1000,
                cmd_file="state",
            )
            log.debug(f"Waiting {INFO_SAMPLE_DELAY_SEC} seconds to start IO")
            time.sleep(INFO_SAMPLE_DELAY_SEC)

            # Use fio to run IO bursts at random offsets in the big file aligned on GiB boundaries

            gib_range = int((test.data["file size"] - BURST_IO_SIZE) / BYTES_IN_GIB)
            test.data["bw"]["bursts"] = {}
            test.data["bw"]["group bursts"] = {}

            offsets_gib = []
            random.seed(7)
            for _index in range(NUMBER_OF_BURST_OFFSETS):
                offsets_gib.append(random.randint(0, gib_range))

            fio_io_errors = 0

            for delay in BURST_DELAY_SEC:
                test.data["bw"]["bursts"][delay] = {}
                group_io_bytes = 0
                group_runtime = 0
                for offset in offsets_gib:

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
                        f"--offset={offset*BYTES_IN_GIB}",
                        f"--output={os.path.join(step.directory,f'fio_{delay}s_{offset}.json')}",
                        "--output-format=json",
                        f"--write_bw_log={delay}s_{offset}",
                        "--log_offset=1",
                        f"--io_size={BURST_IO_SIZE}",
                        "--verify_interval=4096",
                        "--verify=crc32c",
                        "--do_verify=0",
                        "--name=fio_burst_writes",
                    ]
                    fio_result = fio.RunFio(fio_args, step.directory, suite.volume, file=f"fio_{delay}s_{offset}")
                    fio_io_errors += fio_result.io_errors

                    io_bytes = fio_result.logfile["jobs"][0]["write"]["io_bytes"]
                    runtime = fio_result.logfile["jobs"][0]["write"]["runtime"] / MS_IN_SEC

                    group_io_bytes += io_bytes
                    group_runtime += runtime

                    test.data["bw"]["bursts"][delay][offset] = fio_result.write_bw_kib * BYTES_IN_KIB

                    log.debug(
                        f"Burst bandwidth : {test.data['bw']['bursts'][delay][offset]} : {delay} sec {offset} GiB"
                    )

                    time.sleep(delay)
                    test.data["bw"]["group bursts"][delay] = group_io_bytes / group_runtime / BYTES_IN_GB
                time.sleep(INTER_BURST_DELAY_SEC)

            rqmts.no_io_errors(step, fio_io_errors)

            log.debug(f"Waiting {INFO_SAMPLE_DELAY_SEC} seconds to stop sampling")
            time.sleep(INFO_SAMPLE_DELAY_SEC)

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
        steps.test_end_info(test, start_info)
