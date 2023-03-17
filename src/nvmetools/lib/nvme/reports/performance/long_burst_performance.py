import os


DELTA_TEMP_LIMIT = 5  # limit for start/end temperature delta in Celsius


def report(report, test_result):
    """Create pages for pdf test report provided."""

    report.add_description(
        """This test measures performance of long bursts of IO.
        There are four IO patterns: random writes, random reads, sequential writes, and
        sequential reads. The plots are useful for gaining insight into drive behavior such as
        write caching, thermal throttling, and background garbage collection. For example, if
        thermal throttling occurs the plot can tell the time and amount of data read or written
        before the throttling started. It can also tell the reduction in bandwidth for each level
        of throttling.
        <br/><br/>

        The test reports different bandwidths for each IO pattern.  The average bandwidth for the
        entire IO burst, first second, first 15 seconds, and last 120 seconds.  The initial bandwidth
        is more relevant for use cases that do not continuously access the drive, such as office
        computing.  The end bandwidth is more relevant for uses cases that continuously access the
        drive."""
    )
    report.add_results(test_result)
    report.add_paragraph(
        """This table shows the bandwidth for several common datasheet and IO benchmark
        queue depths and block sizes."""
    )
    report.add_bandwidth_performance_table(test_result, random_qd32=False)

    data = test_result["data"]
    test_dir = os.path.join(report._results_directory, test_result["directory name"])

    report.add_paragraph(
        """The table below provides the average and ending bandwidth.  The ending
        bandwidth could be significantly lower if thermal throttling or excessive
        garbage collection occurs."""
    )
    table_rows = [["IO PATTERN", "AVERAGE", "FIRST SEC", "FIRST 15 SEC", "LAST 120 SEC"]]
    for burst_type in data["bursts"]:
        table_rows.append(
            [
                burst_type,
                f"{data['bursts'][burst_type]['bandwidth']:.3f} GB/s",
                f"{data['bursts'][burst_type]['1 second bandwidth']:.3f} GB/s",
                f"{data['bursts'][burst_type]['15 second bandwidth']:.3f} GB/s",
                f"{data['bursts'][burst_type]['end bandwidth']:.3f} GB/s",
            ]
        )
    report.add_table(table_rows, [160, 85, 85, 85, 85])

    report.add_paragraph(
        """This table below reports the composite temperature during the IO burst.  The expectation
        is the end and start temperatures should be within the delta limit.  A higher temperature
        could indicate background operations are ongoing.
        <br/><br/>
        The table also includes the Throttle Time which is the sum for all throttle levels.  Note
        that the units for throttle levels WCTEMP and CCTEMP is in minutes.  Therefore, throttling for
        less than one minute may not be indicated for these levels."""
    )
    table_rows = [["IO PATTERN", "THROTTLE", "MAX", "START", "END", "DELTA", "LIMIT"]]
    for burst_type in data["bursts"]:
        table_rows.append(
            [
                burst_type,
                f"{data['bursts'][burst_type]['throttle time']} sec",
                data["bursts"][burst_type]["max temperature"],
                data["bursts"][burst_type]["io start temperature"],
                data["bursts"][burst_type]["end temperature"],
                data["bursts"][burst_type]["delta temperature"],
                f"{DELTA_TEMP_LIMIT} C",
            ]
        )
    report.add_table(table_rows, [160, 75, 50, 50, 50, 50, 50, 50])

    report.add_pagebreak()
    report.add_subheading("RANDOM WRITES")
    report.add_paragraph(
        """These plots are for writes using random addressing, block size of 4 KiB, and queue
        depth of 1."""
    )
    data_directory = os.path.join(test_dir, "5_random_write", "sample_info")
    bandwidth_file = os.path.join(test_dir, "5_random_write", "bandwidth_write.csv")
    report.add_subheading2("Temperature (Including Idle)")
    report.add_temperature_plot(data_directory)
    report.add_subheading2("IO Write Bandwidth (Including Idle)")
    report.add_bandwidth_plot(data_directory, read=False, write=True)
    report.add_subheading2("IO Write Bandwidth (Excluding Idle)")
    report.add_fio_bandwidth_plot(bandwidth_file)

    report.add_pagebreak()
    report.add_subheading("RANDOM READS")
    report.add_paragraph(
        """These plots are for reads using random addressing, block size of 4 KiB, and queue
        depth of 1."""
    )
    data_directory = os.path.join(test_dir, "6_random_read", "sample_info")
    bandwidth_file = os.path.join(test_dir, "6_random_read", "bandwidth_read.csv")
    report.add_subheading2("Temperature (Including Idle)")
    report.add_temperature_plot(data_directory)
    report.add_subheading2("IO Read Bandwidth (Including Idle)")
    report.add_bandwidth_plot(data_directory, read=True, write=False)
    report.add_subheading2("IO Read Bandwidth (Excluding Idle)")
    report.add_fio_bandwidth_plot(bandwidth_file)

    report.add_pagebreak()
    report.add_subheading("SEQUENTIAL WRITES")
    report.add_paragraph(
        """These plots are for writes using sequential addressing, block size of 128 KiB, and
        queue depth of 32."""
    )
    data_directory = os.path.join(test_dir, "7_sequential_write", "sample_info")
    bandwidth_file = os.path.join(test_dir, "7_sequential_write", "bandwidth_write.csv")
    report.add_subheading2("Temperature (Including Idle)")
    report.add_temperature_plot(data_directory)
    report.add_subheading2("IO Write Bandwidth (Including Idle)")
    report.add_bandwidth_plot(data_directory, read=False, write=True)
    report.add_subheading2("IO Write Bandwidth (Excluding Idle)")
    report.add_fio_bandwidth_plot(bandwidth_file)

    report.add_pagebreak()
    report.add_subheading("SEQUENTIAL READS")
    report.add_paragraph(
        """These plots are for reads using sequential addressing, block size of 128 KiB, and
        queue depth of 32."""
    )
    data_directory = os.path.join(test_dir, "8_sequential_read", "sample_info")
    bandwidth_file = os.path.join(test_dir, "8_sequential_read", "bandwidth_read.csv")
    report.add_subheading2("Temperature (Including Idle)")
    report.add_temperature_plot(data_directory)
    report.add_subheading2("IO Read Bandwidth (Including Idle)")
    report.add_bandwidth_plot(data_directory, read=True, write=False)
    report.add_subheading2("IO Read Bandwidth (Excluding Idle)")
    report.add_fio_bandwidth_plot(bandwidth_file)

    report.add_verifications(test_result)
