# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import csv
import os

from nvmetools.support.conversions import BYTES_IN_GB, US_IN_MS


def report(report, test_result):

    test_dir = os.path.join(report._results_directory, test_result["directory name"])
    data = test_result["data"]

    report.add_description(
        f""" This test reports the bandwidth and distribution of continuous large block sequential and
        random reads to a big file. The big file is approximately {data['file ratio']:0.0f}% of the
        disk size.  The file is reads {data['file reads']} times for each addressing mode.  This allows
        comparison of the different addressing modes: sequential and random.   Since this test reports
        performance measurements no data verification is done."""
    )

    report.add_results(test_result)
    report.add_paragraph(
        f""" The file size tested was {data['file size']/BYTES_IN_GB:0.1f} GB which is
        {data['file ratio']:0.0f}% of the disk size of {data['disk size']/BYTES_IN_GB:0.1f} GB."""
    )

    report.add_subheading2("Sequential Reads")
    step_directory = os.path.join(test_dir, "4_sample_info")
    report.add_paragraph(
        """ The plot below shows the composite temperature of the drive during the test along with the
        thermal throttle limits.<br/><br/>"""
    )
    report.add_temperature_plot(step_directory, height=2)
    report.add_paragraph(""" <br/><br/>The plot below shows the read bandwidth during the sequential reads. """)
    report.add_bigfile_read_plot(step_directory, data["file size"])

    cmd_times = []

    csv_file = os.path.join(test_dir, "5_sequential_reads", "raw_lat.1.log")
    with open(csv_file, "r") as filename:
        filereader = csv.reader(filename)
        for _index in range(16):
            next(filereader)
        for row in filereader:
            cmd_times.append(float(row[1]) / US_IN_MS)

    report.add_paragraph(
        f"""This histogram shows the latency distribution for {len(cmd_times):,} sequential reads.  The
        reads have a block size of {data['block size']}  KiB and queue depth of {data['queue depth']}. """
    )
    report.add_histogram(cmd_times, xlabel="Latency (uS)", log=False)
    report.add_paragraph(
        """This histogram shows the same data as above except on a log scale to provide better
        visibility of outliers. """
    )
    report.add_histogram(cmd_times, xlabel="Latency (uS)", log=True)

    report.add_subheading2("Random Reads")
    step_directory = os.path.join(test_dir, "7_sample_info")
    report.add_paragraph(
        """The plot below shows the composite temperature of the drive during the test along with the
        thermal throttle limits.<br/><br/> """
    )
    report.add_temperature_plot(step_directory, height=2)
    report.add_paragraph("<br/><br/>The plot below shows the read bandwidth during the random reads.")
    report.add_bigfile_read_plot(step_directory, data["file size"])
    cmd_times = []

    csv_file = os.path.join(test_dir, "8_random_reads", "raw_lat.1.log")
    with open(csv_file, "r") as filename:
        filereader = csv.reader(filename)
        for _index in range(16):
            next(filereader)
        for row in filereader:
            cmd_times.append(float(row[1]) / US_IN_MS)

    report.add_paragraph(
        f"""This histogram shows the latency distribution for {len(cmd_times):,} random reads.  The
        reads have a block size of {data['block size']}  KiB and queue depth of {data['queue depth']}. """
    )
    report.add_histogram(cmd_times, xlabel="Latency (uS)", log=False)
    report.add_paragraph(
        """This histogram shows the same data as above except on a log scale to provide better
        visibility of outliers. """
    )
    report.add_histogram(cmd_times, xlabel="Latency (uS)", log=True)
    report.add_verifications(test_result)
