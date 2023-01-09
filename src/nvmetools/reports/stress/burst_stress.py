# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os


def report(report, test_result):
    """Create pages for pdf test report provided."""

    data = test_result["data"]
    test_dir = os.path.join(report._results_directory, test_result["directory name"])
    samples_dir = os.path.join(test_dir, "4_sample_info")

    report.add_description(
        """This test verifies drive reliability running short bursts of IO stress.  The short
        bursts of reads and writes are followed by an idle period. This stresses  the power
        management subsystem by constantly transitioning power states. A variety of burst
        lengths, idle times, queue depths, and block sizes are run with a 50/50 mix of reads and
        writes.
        <br/><br/>

        Drive reliability is defined as completing all reads and writes without error or data
        corruption.  Data verification is performed on all reads and writes to ensure no data
        corruption.
        """
    )
    report.add_results(test_result)
    report.add_paragraph(
        f"""The below bursts were completed.  Each burst runs {data['run time sec']} seconds and
        consists of an idle time followed by read/write of size blocks."""
    )
    table_rows = [["BURST", "IDLE TIME", "DEPTH", "# BLOCKS", "BLOCK SIZE"]]

    for index, burst in enumerate(data["bursts"]):
        table_rows.append(
            [
                index,
                f"{burst['wait time ms']} mS",
                burst["queue depth"],
                f"{burst['number blocks']}",
                burst["block size"],
            ]
        )
    report.add_table(table_rows, [50, 100, 100, 100, 100])

    report.add_paragraph(
        f"""This temperature plot includes a {data['sample delay sec'] } second idle time
        before and after the IO stress.  Review the plot and verify the temperature behaves as
        expected.  For details see <u>Analyze temperature and bandwidth plots with nvmecmd</u> [5]"""
    )
    report.add_temperature_plot(samples_dir, ymin=20)

    report.add_paragraph(
        """<br/><br/>
        The plots below shows the read and write bandwidth during the test including the idle time
        before and after the IO stress.  Review the plots and verify the bandwidth behaves as
        expected.  For details see <u>Analyze temperature and bandwidth plots with nvmecmd</u> [5]"""
    )
    report.add_bandwidth_plot(samples_dir, read=False)
    report.add_bandwidth_plot(samples_dir, write=False)

    report.add_verifications(test_result)
