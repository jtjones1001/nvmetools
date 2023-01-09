# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os


def report(report, test_result):

    data = test_result["data"]
    test_dir = os.path.join(report._results_directory, test_result["directory name"])
    samples_dir = os.path.join(test_dir, "4_sample_info")

    report.add_description(
        f"""This test verifies drive reliability running high bandwidth IO stress.  High
        bandwidth stress maximizes the amount of data during reads and writes to stress specific
        drive subsystems. The high bandwidth is achieved with a
        50/50 mix of sequential reads and writes, block size of {data['block size kib']} KiB,
        and queue depth of {data['queue depth']}.
        <br/><br/>

        Drive reliability is defined as completing all reads and writes without error or data
        corruption.  Data verification is performed on all reads and writes to ensure no data
        corruption.
        """
    )
    report.add_results(test_result)
    report.add_paragraph(
        """Verify the temperatures and thermal throttling time, if any, in this table are
        within the expected range."""
    )
    table_rows = [
        ["STRESS TIME", "THROTTLE TIME", "MIN TEMP", "MAX TEMP"],
        [
            data["runtime"],
            data["time throttled"],
            data["min temp"],
            data["max temp"],
        ],
    ]
    report.add_table(table_rows, [125, 125, 125, 125])
    report.add_paragraph("""Verify the aggregate bandwidth is within expected range.""")
    table_rows = [
        ["DATA WRITTEN", "WRITE BANDWIDTH", "DATA READ", "READ BANDWIDTH"],
        [
            data["written"],
            data["write bandwidth"],
            data["read"],
            data["read bandwidth"],
        ],
    ]
    report.add_table(table_rows, [125, 125, 125, 125])

    report.add_paragraph(
        f"""This temperature plot includes idle time before and after the IO stress. In this plot,
        verify the temperature behaves as expected.  For details see <u>Analyze temperature and
        bandwidth plots with nvmecmd</u> [5]"""
    )
    report.add_temperature_plot(samples_dir, ymin=20)

    report.add_paragraph(
        """<br/><br/>
        The plots below shows the read and write bandwidth during the test including the idle time
        before and after the IO stress.  In these plots, verify the bandwidth behaves as
        expected.  For details see <u>Analyze temperature and bandwidth plots with nvmecmd</u> [5]"""
    )
    report.add_bandwidth_plot(samples_dir, read=False)
    report.add_bandwidth_plot(samples_dir, write=False)

    report.add_verifications(test_result)
