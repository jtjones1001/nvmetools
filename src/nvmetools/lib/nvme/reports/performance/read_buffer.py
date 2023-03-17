import csv
import os

DELAYED_LATENCY_IOS = 16


def report(report, test_result):

    test_dir = os.path.join(report._results_directory, test_result["directory name"])

    report.add_description(
        """This test attempts to determine if the drive implements a read buffer by reporting the
        difference in read latency for two subsequent reads to the same address.  Drives that have a read
        buffer should report much lower latency for the second read.  Since these are performance
        measurements no data verification is done. """
    )

    report.add_results(test_result)
    report.add_paragraph(
        """This plot shows the ratio of two reads to the same address at different block sizes.  Devices
        that buffer reads will have a faster second read.  A ratio of 0.5 indicates the second read was
        twice as fast as the first read."""
    )

    # Calculate and plot the first / second read ratio

    csv_file = os.path.join(test_dir, "4_io", "raw_lat.1.log")
    with open(csv_file, "r") as file_object:
        file_rows = csv.reader(file_object)
        for _index in range(DELAYED_LATENCY_IOS):
            next(file_rows)

        last_offset = 0
        first_reads = {}
        second_reads = {}

        for row in file_rows:
            block_size = row[3]
            if block_size not in first_reads:
                first_reads[block_size] = []
                second_reads[block_size] = []

            offset = row[4]
            if offset == last_offset:
                second_reads[block_size].append(row[1])
            else:
                first_reads[block_size].append(row[1])
            last_offset = offset

        y_data = []
        x_data = []
        for block_size in first_reads:
            x_data.append(f"{(int(block_size)/1024):0.0f}")

            total_sum = 0
            second_total = 0
            for item in first_reads[block_size]:
                total_sum += int(item)

            for item in second_reads[block_size]:
                second_total += int(item)

            total_sum = total_sum / 1000  # ns to us
            second_total = second_total / 1000  # ns to us

            first_avg = total_sum / len(first_reads[block_size])
            second_avg = second_total / len(second_reads[block_size])
            y_data.append(second_avg / first_avg)

        report.add_plot(
            x_data,
            "Block Size (KiB)",
            y_data,
            "Ratio (Second/First Read)",
            ymin=0,
            xmin=0,
            xticks=range(-1, 129, 16),
        )

    report.add_verifications(test_result)
