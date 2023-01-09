# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os


def report(report, test_result):
    data = test_result["data"]

    report.add_description(
        f""" This test runs IO stress that alternates between periods of high bandwidth reads and
        idle.  This pattern causes the drive's composite temperature to alternate between low and
        high temperatures.  The drive heats up during the IO reads and cools down during the idle
        time.  The thermal expansion and contraction exerts mechanical stress on the drive.
        <br/><br/>

        The IO stress is 100% reads with queue depth {data["queue depth"] } and block size
        {data["block size"]} KiB.
        <br/><br/>

        This test is not meant to replace standard component qualification tests such as JESD22-A104
        or system environmental tests such as 4-corners. """
    )
    report.add_results(test_result)

    report.add_paragraph(
        """In this table, the Stress Time and Idle Time are for each cycle but the minimum and
        maximum temperatures are for all cycles."""
    )
    table_rows = [
        ["STRESS TIME", "IDLE TIME", "NUMBER CYCLES", "MIN TEMP", "MAX TEMP"],
        [
            f"{data['io runtime']} sec",
            f"{data['idle time']} sec",
            data["cycles"],
            data["min temp"],
            data["max temp"],
        ],
    ]
    report.add_table(table_rows, [100, 100, 100, 100, 100])

    test_dir = os.path.join(report._results_directory, test_result["directory name"])
    samples_dir = os.path.join(test_dir, "4_sample_info")

    report.add_subheading("Temperature and IO Bandwidth")
    report.add_paragraph(
        """Review this temperature plot to verify the temperature behaves as
    expected.  For details see <u>Analyze temperature and bandwidth plots with nvmecmd</u> [5]"""
    )
    report.add_temperature_plot(samples_dir, ymin=20)

    report.add_paragraph(
        """<br/><br/>
        Review this bandwidth plot to verify the read bandwidth behaves as expected.  For details see
        <u>Analyze temperature and bandwidth plots with nvmecmd</u> [5]."""
    )
    report.add_bandwidth_plot(samples_dir, write=False)

    report.add_verifications(test_result)
