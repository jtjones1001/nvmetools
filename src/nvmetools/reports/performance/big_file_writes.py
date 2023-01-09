import os

from nvmetools.support.conversions import BYTES_IN_GB


BURST_DELAY_SEC = [16, 8, 4, 2, 1]
INTER_BURST_DELAY_SEC = 30
NUMBER_OF_BURST_OFFSETS = 6
WAIT_FOR_IDLE_SEC = 180


def report(report, test_result):

    data = test_result["data"]
    test_dir = os.path.join(report._results_directory, test_result["directory name"])

    report.add_description(
        f"""This test writes a big file using continuous, large block, high queue depth, sequential
        writes. The file size is {data['file ratio']:0.0f}% of the disk size.  The total amount of
        continuous writes completed is {data['file writes']} times the file size.  A large amount of
        continuous writes can identify performance variation from several issues such as thermal
        throttling, slow garbage collection, and write cache limitations.
        <br/><br/>

        After the continous writes have completed, the test waits {WAIT_FOR_IDLE_SEC}
        seconds for background garbage collection to complete.  The test then runs several bursts bursts of
        large block, high queue depth, writes with varying amounts of idle time between them.   The different
        idle times can identify performance behavior of a write buffer or write cache."""
    )

    report.add_results(test_result)
    report.add_subheading2("Continuous Writes")
    step_directory = os.path.join(test_dir, "4_sample_info")
    report.add_paragraph(
        f""" The file size tested was {data['file size']/BYTES_IN_GB:0.1f} GB which is
        {data['file ratio']:0.0f}% of the disk size of {data['disk size']/BYTES_IN_GB:0.1f} GB.
        A total of {data['io size']/BYTES_IN_GB:0.1f} GB were written to the file during at an
        average bandwidth of {data['bw']['continuous']/BYTES_IN_GB:0.2f} GB. The plot below shows the
        composite temperature of the drive during the test along with the thermal
        throttle limits.<br/><br/>"""
    )
    report.add_temperature_plot(step_directory)
    report.add_paragraph(
        f"""<br/><br/>
        The plot below shows the write bandwidth during the continuous writes. The file was written a
        total of {data['file writes']} times.  The vertical red lines indicate each time a new file
        write begins.<br/><br/>"""
    )
    report.add_bigfile_write_plot(step_directory, data["file size"])

    report.add_subheading2("Burst Writes")
    step_directory = os.path.join(test_dir, "7_sample_info")
    report.add_paragraph(
        f"""A total of {len(BURST_DELAY_SEC)} groups of bursts were completed. Each burst group has
        different idle times between bursts.  For devices with write buffers, the bandwidth may decrease
        as the idle time reduces. <br/><br/> """
    )
    table_data = [["Burst Group", "Number of Bursts", "Idle Delay", "Average Bandwidth"]]
    for index, delay in enumerate(BURST_DELAY_SEC):
        table_data.append(
            [
                f"{index}",
                NUMBER_OF_BURST_OFFSETS,
                f"{delay} sec",
                f"{data['bw']['group bursts'][f'{delay}']:0.3f} GB/s",
            ]
        )

    report.add_table(table_data, [100, 100, 125, 150])
    report.add_paragraph(
        """The plot below shows the composite temperature of the drive during the burst writes to the
        device. The burst workload should not result in thermal throttling."""
    )
    report.add_temperature_plot(step_directory)
    report.add_paragraph("""<br/><br/>The plot below shows the bandwidth during burst writes to the big file.""")
    report.add_bigfile_write_plot(step_directory)

    report.add_verifications(test_result)
