# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import csv
import os
import platform
import time

from nvmetools import TestCase, TestStep, fio, rqmts, steps
from nvmetools.support.conversions import NS_IN_MS


def aspm_latency(suite):
    """Measure IO latency with ASPM enabled and disabled.

    Args:
        suite:  Parent TestSuite instance
    """

    with TestCase(suite, "ASPM latency", aspm_latency.__doc__) as test:

        # -----------------------------------------------------------------------------------------
        # Step : Read NVMe info and rqmts no critical warnings, stop test on fail
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)

        if "Windows" == platform.system():
            test.data["os power plan"] = start_info.info["_metadata"]["system"]["powerplan"]
        else:
            test.data["os power plan"] = "N/A"

        # -----------------------------------------------------------------------------------------
        # Step : Create a performance data file for fio to use, stop test on fail
        # -----------------------------------------------------------------------------------------
        fio_file = steps.get_fio_performance_file(test)

        # -----------------------------------------------------------------------------------------
        # Multiple Steps : Run IO with different think times
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "IO", "Use fio to run IO reads with different idle times") as step:
            total_time = []
            total_latency = []
            fio_io_errors = 0

            nonop_ps_ops = 81
            nonop_ps_trims_ios = 15
            nonop_ps_idle_times = [0, 1, 5, 10, 15, 20, 25, 30, 40, 60, 80]

            for thinktime in nonop_ps_idle_times:
                args = [
                    "--direct=1",
                    "--thread",
                    "--numjobs=1",
                    f"--filesize={fio_file.file_size}",
                    f"--filename={fio_file.filepath}",
                    "--allow_file_create=0",
                    "--rw=read",
                    "--iodepth=1",
                    "--bs=8192",
                    f"--thinktime={thinktime}us",
                    f"--number_ios={nonop_ps_ops}",
                    "--disable_clat=1",
                    "--disable_slat=1",
                    f"--write_lat_log=raw_{thinktime}",
                    f"--size={fio_file.file_size}",
                    f"--output={os.path.join(step.directory,f'fio_{thinktime}.json')}",
                    "--output-format=json",
                    "--name=fio",
                ]

                fio_read_idle = fio.RunFio(
                    args,
                    step.directory,
                    volume=suite.volume,
                    file=f"fio_{thinktime}",
                )
                fio_io_errors += fio_read_idle.io_errors

                # Read in latencies and remove first one because idle time was undefined

                latency_data = []
                with open(os.path.join(step.directory, f"raw_{thinktime}_lat.1.log")) as file_object:
                    rows = csv.reader(file_object)
                    next(rows)
                    for row in rows:
                        latency_data.append(int(row[1]) / NS_IN_MS)

                # remove the top value to strip out any OS interrupt related slow downs

                latency_data.sort()
                truncated_data = latency_data[nonop_ps_trims_ios:-nonop_ps_trims_ios]

                # append to total times

                total_time.append(thinktime)
                total_latency.append(sum(truncated_data) / len(truncated_data))
                time.sleep(5)

            rqmts.no_io_errors(step, fio_io_errors)

            # Create a csv file with the results that is easy to plot

            with open(os.path.join(test.directory, "results.csv"), "w", newline="") as file_object:
                rows = csv.writer(file_object)
                for index, _value in enumerate(total_time):
                    rows.writerow([str(total_time[index]), str(total_latency[index])])

        # -----------------------------------------------------------------------------------------
        # Step : Read NVMe info and compare against starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
