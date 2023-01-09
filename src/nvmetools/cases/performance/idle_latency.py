# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import csv
import os
import time

from nvmetools import TestCase, TestStep, fio, rqmts, steps
from nvmetools.support.conversions import NS_IN_MS


def _measure_latency_vs_idle(step, fio_file, idle_times, unit="ms"):
    """Measure latency and save in results.xls."""
    fio_io_errors = 0
    total_time = []
    total_latency = []

    if unit == "us":
        NUMBER_OF_IO = 161  # only count 100 IO (161 - 1 - 30 - 30 = 100)
        NUMBER_IO_TO_TRIM = 30  # trim out outliers
    else:
        NUMBER_OF_IO = 81  # only count 50 IO (81 - 1 - 15 -15 = 50)
        NUMBER_IO_TO_TRIM = 15  # trim out outliers

    for thinktime in idle_times:
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
            f"--thinktime={thinktime}{unit}",
            "--thinktime_blocks=1",
            f"--number_ios={NUMBER_OF_IO}",
            "--disable_clat=1",
            "--disable_slat=1",
            f"--write_lat_log=raw_{thinktime}",
            f"--size={fio_file.file_size}",
            f"--output={os.path.join(step.directory,f'fio_{thinktime}.json')}",
            "--output-format=json",
            "--name=fio",
        ]
        fio_read_idle = fio.RunFio(args, step.directory, volume=step.suite.volume, file=f"fio_{thinktime}")
        fio_io_errors += fio_read_idle.io_errors

        # Read in latencies and remove first one because idle time was undefined

        latency_data = []
        with open(os.path.join(step.directory, f"raw_{thinktime}_lat.1.log")) as file_object:
            rows = csv.reader(file_object)
            next(rows)
            for row in rows:
                latency_data.append(int(row[1]) / NS_IN_MS)

        # remove the outliers to strip out any OS interrupt related slow downs or other issues

        latency_data.sort()
        truncated_data = latency_data[NUMBER_IO_TO_TRIM:-NUMBER_IO_TO_TRIM]

        # append to total times

        total_time.append(thinktime)
        total_latency.append(sum(truncated_data) / len(truncated_data))
        time.sleep(5)

    rqmts.no_io_errors(step, fio_io_errors)

    # Create a csv file with the results that are easy to plot

    with open(os.path.join(step.directory, "results.csv"), "w", newline="") as file_object:
        rows = csv.writer(file_object)
        for index, _value in enumerate(total_time):
            rows.writerow([str(total_time[index]), str(total_latency[index])])


def idle_latency(suite):
    """Measure IO latency after periods of idle.

    This test measures the latency of IO reads after periods of idle to determine the effect of
    power state transitions.  The periods of idle cause the hardware or Operating System to enter
    lower power states.  Exiting the power states takes time and adds to the IO latency.  The longer
    the idle period the lower the power state are entered.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Idle latency", idle_latency.__doc__) as test:

        # -----------------------------------------------------------------------------------------
        # Before test, read NVMe info and verify no critical warnings, get fio file
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)
        fio_file = steps.get_fio_performance_file(test)

        # -----------------------------------------------------------------------------------------
        # Measure latency for single read after a short period of idle time.  Short idle times
        # are good for measuring the effect of low-level hardware power features such ASPM and
        # processor power states.
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Short idle", "Measure read latency after short idle periods.") as step:

            short_idle_times = [us for us in range(1000) if not us % 10]

            _measure_latency_vs_idle(step, fio_file, short_idle_times, unit="us")

            rqmts.review_short_power_exit_latency(step)

        # -----------------------------------------------------------------------------------------
        # Measure latency for single read after longer period of idle time with course
        # resolution.  Longer idle times are good for measuring the effect of NVMe power
        # states, specifically the non-operational power states.
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Long idle", "Measure read latency after long idle periods.") as step:

            long_idle_times = [ms for ms in range(100) if not ms % 10]
            long_idle_times.extend([ms for ms in range(100, 1000) if not ms % 50])
            long_idle_times.extend([ms for ms in range(1000, 3000) if not ms % 200])

            _measure_latency_vs_idle(step, fio_file, long_idle_times, unit="ms")

            rqmts.review_power_entry_timeout(step)
            rqmts.review_power_exit_latency(step)

        # -----------------------------------------------------------------------------------------
        # After test, read NVMe info and compare against the starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
