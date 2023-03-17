# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import csv
import json
import os


def _add_row(name, io_type, data):
    return [
        name,
        f"{data['fio'][io_type]:.2f} mS",
        f"{data['both'][io_type]:.2f} mS",
        f"{data['delta'][io_type]:.2f} mS   ({data['percent'][io_type]:.1f}%)",
    ]


def _get_smart_row(name, baseline, concurrent):
    if name == "Average Get Log Page 2 Latency":
        base = sum(baseline) / len(baseline)
        both = sum(concurrent) / len(concurrent)
    else:
        base = max(baseline)
        both = max(concurrent)
    delta = both - base

    return [
        name,
        f"{base:.2f} mS",
        f"{both:.2f} mS",
        f"{delta:.2f} mS",
    ]


def report(report, test_result):

    data = test_result["data"]
    report.add_description(
        f"""This test verifies reading SMART attributes during normal operation has no adverse
        effects on IO read and writes.  Adverse effects are defined as functional errors, data integrity
        loss, or an unacceptable increase in IO latency.  A typical Enterprise Use Case [10]
        reads SMART attributes regularly to identify issues that may predict drive failures.  Suspect
        drives can then be replaced prior to actually failing.
        <br/><br/>

        This test runs a total of 1,825 Get Log Page 2 commands to simulate one read per day for 5
        years.  The Get Log Page 2 commands are run at intervals of
        {data['interval ms']}mS to ensure significant idle time between commands which is closer to
        the actual use case.
        <br/><br/>

        The concurrent IO workload is a 50/50 mix of reads and writes, random addressing, 4 KiB
        block size, and queue depth 2.  This workload ensures an IO is always in flight but should
        not swamp the controller."""
    )
    report.add_results(test_result)

    data_directory = os.path.join(report._results_directory, test_result["directory name"])

    fio_file = os.path.join(data_directory, "4_io_baseline", "fio.json")
    with open(fio_file, "r") as file_object:
        baseline_fio = json.load(file_object)

    fio_file = os.path.join(data_directory, "6_smart_and_io", "fio.json")
    with open(fio_file, "r") as file_object:
        concurrent_fio = json.load(file_object)

    baseline_lp2 = []
    concurrent_lp2 = []
    lp2_failures = 0

    csv_file = os.path.join(data_directory, "3_smart_baseline", "admin_command_times.csv")
    with open(csv_file, "r") as filename:
        file = csv.DictReader(filename)
        for col in file:
            if col["Command"] == "Get Log Page 0x02":
                baseline_lp2.append(float(col["Time(mS)"]))
                if int(col["ReturnCode"]) != 0:
                    lp2_failures += 1

    csv_file = os.path.join(data_directory, "6_smart_and_io", "admin_command_times.csv")
    with open(csv_file, "r") as filename:
        file = csv.DictReader(filename)
        for col in file:
            if col["Command"] == "Get Log Page 0x02":
                concurrent_lp2.append(float(col["Time(mS)"]))
                if int(col["ReturnCode"]) != 0:
                    lp2_failures += 1

    total_lp2_commands = len(baseline_lp2) + len(concurrent_lp2)

    report.add_paragraph(
        f""" A total of {total_lp2_commands:,} Get Log Page 2 Commands were completed with
        {lp2_failures:,} reported errors. Get Log Page 2 latency was measured on
        {len(baseline_lp2):,} commands run standalone and another {len(concurrent_lp2):,}
        commands run concurrent with IO reads and writes."""
    )
    table_rows = [
        ["PARAMETER", "STANDALONE", "CONCURRENT", "DELTA"],
        _get_smart_row("Average Get Log Page 2 Latency", baseline_lp2, concurrent_lp2),
        _get_smart_row("Maxmimum Get Log Page 2 Latency", baseline_lp2, concurrent_lp2),
    ]
    report.add_table(table_rows, [200, 90, 90, 90])

    report.add_paragraph(
        f""" A total of {baseline_fio["jobs"][0]["error"]} errors occured running IO standalone
        and  {baseline_fio["jobs"][0]["error"]} errors running concurrent. """
    )
    report.add_paragraph(
        f""" A total of {baseline_fio["jobs"][0]["read"]["total_ios"]:,} reads were completed
        standalone. Another {concurrent_fio["jobs"][0]["read"]["total_ios"]:,} reads
        were completed concurrent with Log Page 2.  In the tables and charts below the slowest IO
        are defined as the slowest {len(baseline_lp2):,} IO. """
    )
    table_rows = [
        ["PARAMETER", "STANDALONE", "CONCURRENT", "DELTA"],
        _add_row("Read Average Latency", "read avg", data),
        _add_row("Read Average Commit Latency Slowest IO", "read slow", data),
        _add_row("Read Maximum Latency", "read max", data),
    ]
    report.add_table(table_rows, [210, 80, 80, 130])

    report.add_paragraph(
        f""" A total of {baseline_fio["jobs"][0]["write"]["total_ios"]:,} writes were completed
        standalone. Another {concurrent_fio["jobs"][0]["write"]["total_ios"]:,} writes
        were completed concurrent with Log Page 2."""
    )
    table_rows = [
        ["PARAMETER", "STANDALONE", "CONCURRENT", "DELTA"],
        _add_row("Write Average Latency", "write avg", data),
        _add_row("Write Average Commit Latency Slowest IO", "write slow", data),
        _add_row("Write Maximum Latency", "write max", data),
    ]
    report.add_table(table_rows, [210, 80, 80, 130])

    report.add_subheading2("Average IO Latency")
    report.add_latency_bar_charts(
        data["fio"]["read avg"],
        data["both"]["read avg"],
        data["fio"]["write avg"],
        data["both"]["write avg"],
    )
    report.add_subheading2("Slowest IO Latency")
    report.add_latency_bar_charts(
        data["fio"]["read slow"],
        data["both"]["read slow"],
        data["fio"]["write slow"],
        data["both"]["write slow"],
    )
    report.add_subheading2("Maximum IO Latency")
    report.add_latency_bar_charts(
        data["fio"]["read max"],
        data["both"]["read max"],
        data["fio"]["write max"],
        data["both"]["write max"],
    )

    report.add_verifications(test_result)
