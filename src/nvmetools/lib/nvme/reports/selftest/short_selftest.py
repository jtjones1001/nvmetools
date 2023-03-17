# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Test and report for running the short self-test diagnostic.

This module runs the short self-test diagnostic.
"""
import json
import os

from nvmetools.support.conversions import NS_IN_MS, as_datetime, as_int


def report(report, test_result):

    data = test_result["data"]

    report.add_description(
        """Self-test is a diagnostic testing sequence that tests the integrity and functionality of
        the controller and may include testing of the media associated with namespaces.  The
        self-test is run using the Device Self-Test Admin Command.  There is a short self-test and
        an extended self-test. This test verifies the short self-test.
        <br/><br/>

        The self-test diagnostic is run standalone and concurrent with a light IO workload.  In
        both cases the diagnostic must pass, complete within 2 minutes as specified in
        the <u>NVMe specification</u> [1], and report progress in Log Page 6 that is monotonic and
        roughly linear.
        <br/><br/>

        The NVMe specification states the IO performance can be degraded during the self-test but
        does not specify any limits.  The performance difference between standalone and concurrent
        operation is reported to help determine if running the diagnostic during normal operation is
        practical.
        """
    )
    report.add_results(test_result)

    test_dir = os.path.join(report._results_directory, test_result["directory name"])
    fio_baseline = os.path.join(test_dir, "4_io_standalone", "fio.json")
    with open(fio_baseline, "r") as file_object:
        fio_base = json.load(file_object)

    fio_both_file = os.path.join(test_dir, "5_selftest_and_io", "fio.json")
    with open(fio_both_file, "r") as file_object:
        fio_both = json.load(file_object)

    sa_file = os.path.join(test_dir, "3_selftest_standalone", "selftest.summary.json")

    with open(sa_file, "r") as file_object:
        info = json.load(file_object)

    sa_time = []
    sa_temp = []
    sa_diag_progress = []
    sa_diag_progress_time = []

    start_time = as_datetime(info["selftest details"]["status"][0]["timestamp"])

    for sample in info["selftest details"]["status"]:
        sample_time = as_datetime(sample["timestamp"])
        sa_time.append((sample_time - start_time).total_seconds() / 60.00)
        sa_temp.append(as_int(sample["Composite Temperature"]))
        if sample["status"] != 0:
            sa_diag_progress.append(as_int(sample["percent complete"]))
            sa_diag_progress_time.append((sample_time - start_time).total_seconds() / 60.00)

    bg_file = os.path.join(test_dir, "5_selftest_and_io", "selftest.summary.json")

    with open(bg_file, "r") as file_object:
        info = json.load(file_object)

    bg_time = []
    bg_temp = []
    bg_diag_progress = []
    bg_diag_progress_time = []

    start_time = as_datetime(info["selftest details"]["status"][0]["timestamp"])

    for sample in info["selftest details"]["status"]:
        sample_time = as_datetime(sample["timestamp"])
        bg_time.append((sample_time - start_time).total_seconds() / 60.00)
        bg_temp.append(as_int(sample["Composite Temperature"]))
        if sample["status"] != 0:
            bg_diag_progress.append(as_int(sample["percent complete"]))
            bg_diag_progress_time.append((sample_time - start_time).total_seconds() / 60.00)

    table_rows = [
        ["PARAMETER", "STANDALONE", "CONCURRENT", "LIMIT"],
        [
            "Run Time",
            f"{data['standalone']['runtime']:.3f} Min",
            f"{data['concurrent']['runtime']:.3f} Min",
            f"{data['runtime limit']} Min",
        ],
        [
            "Progress Monotonocity",
            data["standalone"]["monotonic"],
            data["concurrent"]["monotonic"],
            "Monotonic",
        ],
        [
            "Progress Linearity",
            f"{data['standalone']['linear']:.3f}",
            f"{data['concurrent']['linear']:.3f}",
            f"> {data['linearity limit']}",
        ],
    ]
    report.add_table(table_rows, [200, 100, 100, 100])

    report.add_paragraph(
        """This plot shows the self-test progress reported in Log Page 6 which should be monotonic and
        roughly linear."""
    )
    report.add_diagnostic_progress_plot(
        sa_diag_progress_time, sa_diag_progress, bg_diag_progress_time, bg_diag_progress
    )
    report.add_paragraph("<br/>")
    report.add_paragraph(
        """These bar charts show the difference in IO latency between stand-alone and concurrent operation.
        The tester must determine if the latency difference is acceptable since the NVMe specification
        does not define any limits."""
    )
    report.add_subheading2("Average IO Latency")

    report.add_latency_bar_charts(
        fio_base["jobs"][0]["read"]["lat_ns"]["mean"] / NS_IN_MS,
        fio_both["jobs"][0]["read"]["lat_ns"]["mean"] / NS_IN_MS,
        fio_base["jobs"][0]["write"]["lat_ns"]["mean"] / NS_IN_MS,
        fio_both["jobs"][0]["write"]["lat_ns"]["mean"] / NS_IN_MS,
    )
    report.add_subheading2("Maximum IO Latency")
    report.add_latency_bar_charts(
        fio_base["jobs"][0]["read"]["lat_ns"]["max"] / NS_IN_MS,
        fio_both["jobs"][0]["read"]["lat_ns"]["max"] / NS_IN_MS,
        fio_base["jobs"][0]["write"]["lat_ns"]["max"] / NS_IN_MS,
        fio_both["jobs"][0]["write"]["lat_ns"]["max"] / NS_IN_MS,
    )
    report.add_subheading("COMPOSITE TEMPERATURE")
    report.add_paragraph(
        """This plot shows the drive's composite temperature during the self-test to determine if
        over-heating is a concern.  Thermal throttle limits are shown as red horizontal
        lines."""
    )
    report.add_diagnostic_temperature_plot(sa_time, sa_temp, bg_time, bg_temp)

    report.add_verifications(test_result)
