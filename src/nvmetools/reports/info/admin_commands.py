# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import csv
import os
from collections import defaultdict


def report(report, test_result):
    report.add_description(
        """ This test verifies the reliability and performance of Admin Commands that provide
        information about the drive: Identify Controller, Identify Namespace, Get Log Page, and Get
        Feature. Each Admin Command is run several thousand times with no interval between the
        commands.  This quickly builds a large sample to assess reliability and performance.
        <br/><br/>

        The test verifies the Admin Command average and maximum latencies.  Admin command latency is
        dependent on multiple factors including OS interrupts, power states, concurrent drive activity,
        and others. This test measures latencies without concurrent IO and only in the active power
        state.  The latencies reported by the test serve as a standard reference but are likely not the
        worst case values.
        <br/><br/>

        Each command is verified to complete without error.  The information returned by each command
        is compared against the initial reading to verify no unexpected changes occurred. Static
        parameters, such as Model Number, were verified not to change. SMART counters, such as Data
        Read, were verified not to decrement.  Dynamic parameters, such as Timestamp, are expected to
        change and are not verified.
        """
    )
    report.add_results(test_result)

    data = test_result["data"]
    report.add_paragraph(
        f""" A total of {data['commands run']:,} Admin Commands were completed with
        {data['commands failed']:,} reported errors.  Each of the {data['command types']} command
        types was run {data['sample size']:,} times.  The latency was measured for each command and
        the average and maximum is reported in the table below."""
    )
    each_command = defaultdict(list)
    cmd_times = []

    csv_file = os.path.join(
        report._results_directory, test_result["directory name"], "1_run_commands", "admin_command_times.csv"
    )
    with open(csv_file, "r") as filename:
        file = csv.DictReader(filename)
        for col in file:
            cmd_times.append(float(col["Time(mS)"]))
            each_command[col["Command"]].append(float(col["Time(mS)"]))

    table_rows = [
        ["PARAMETER", "VALUE", "LIMIT"],
        [
            "Average Latency (All Commands)",
            f"{(sum(cmd_times)/len(cmd_times)):.1f} mS",
            f"{data['Average Admin Cmd Limit mS']} mS",
        ],
        [
            "Maxmimum Latency (All Commands)",
            f"{max(cmd_times):.1f} mS",
            f"{data['Maximum Admin Cmd Limit mS']} mS",
        ],
    ]
    report.add_table(table_rows, [240, 75, 75])

    report.add_paragraph(
        "<br/><br/>This histogram shows the distribution of Admin Command latencies for all command types."
    )
    report.add_histogram(cmd_times)
    report.add_pagebreak()
    report.add_paragraph(
        "<br/>This histogram shows the distribution above on a log scale to better show outliers."
    )
    report.add_histogram(cmd_times, log=True)

    labels = []
    avg_values = []
    max_values = []

    for command in reversed(each_command):
        labels.append(command)
        avg_values.append(sum(each_command[command]) / len(each_command[command]))
        max_values.append(max(each_command[command]))

    report.add_paragraph("<br/>This bar chart shows the average Admin Command latencies for each command type.")
    report.add_admin_bar_chart(labels, avg_values)
    report.add_pagebreak()
    report.add_paragraph("<br/>This bar chart shows the maximum Admin Command latencies for each command type.")
    report.add_admin_bar_chart(labels, max_values)

    report.add_verifications(test_result)
