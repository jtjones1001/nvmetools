import glob
import os


DELTA_TEMP_LIMIT = 5  # limit for start/end temperature delta in Celsius


def report(report, test_result):
    """Create pages for pdf test report provided."""

    report.add_description(
        """This test is the same as Long Burst Performance test except the drive capacity
        is 90% at the start.  Full drives may have lower performance than empty drives
        because of a lower number of erased blocks available for writes and a smaller
        dynamic cache.
        <br/><br/>
        For additional details refer to the Long Burst Performance test.
        """
    )
    report.add_results(test_result)
    report.add_paragraph(
        """This table shows the bandwidth for several common datasheet and IO benchmark
        queue depths and block sizes."""
    )
    report.add_bandwidth_performance_table(test_result, random_qd32=False)

    data = test_result["data"]
    test_dir = os.path.join(report._results_directory, test_result["directory name"])

    if len(glob.glob(os.path.join(report._results_directory, "*_long_burst_performance"))) == 1:
        ref_directory = glob.glob(os.path.join(report._results_directory, "*_long_burst_performance"))[0]

    else:
        ref_directory = None
        ref_data_directory = None

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
    data_directory = os.path.join(test_dir, "4_random_write", "sample_info")
    bandwidth_file = os.path.join(test_dir, "4_random_write", "bandwidth_write.csv")

    if ref_directory is not None:
        ref_data_directory = os.path.join(ref_directory, "4_random_write", "sample_info")

    report.add_subheading2("Temperature (Including Idle)")
    report.add_temperature_plot(data_directory)
    report.add_subheading2("IO Write Bandwidth (Including Idle)")
    report.add_bandwidth_plot(data_directory, ref_data_directory, read=False, write=True)
    report.add_subheading2("IO Write Bandwidth (Excluding Idle)")
    report.add_fio_bandwidth_plot(bandwidth_file)

    report.add_pagebreak()
    report.add_subheading("RANDOM READS")
    report.add_paragraph(
        """These plots are for reads using random addressing, block size of 4 KiB, and queue
        depth of 1."""
    )
    data_directory = os.path.join(test_dir, "5_random_read", "sample_info")
    bandwidth_file = os.path.join(test_dir, "5_random_read", "bandwidth_read.csv")

    if ref_directory is not None:
        ref_data_directory = os.path.join(ref_directory, "5_random_read", "sample_info")

    report.add_subheading2("Temperature (Including Idle)")
    report.add_temperature_plot(data_directory)
    report.add_subheading2("IO Read Bandwidth (Including Idle)")
    report.add_bandwidth_plot(data_directory, ref_data_directory, read=True, write=False)
    report.add_subheading2("IO Read Bandwidth (Excluding Idle)")
    report.add_fio_bandwidth_plot(bandwidth_file)

    report.add_pagebreak()
    report.add_subheading("SEQUENTIAL WRITES")
    report.add_paragraph(
        """These plots are for writes using sequential addressing, block size of 128 KiB, and
        queue depth of 32."""
    )
    data_directory = os.path.join(test_dir, "6_sequential_write", "sample_info")
    bandwidth_file = os.path.join(test_dir, "6_sequential_write", "bandwidth_write.csv")
    if ref_directory is not None:
        ref_data_directory = os.path.join(ref_directory, "6_sequential_write", "sample_info")

    report.add_subheading2("Temperature (Including Idle)")
    report.add_temperature_plot(data_directory)
    report.add_subheading2("IO Write Bandwidth (Including Idle)")
    report.add_bandwidth_plot(data_directory, ref_data_directory, read=False, write=True)
    report.add_subheading2("IO Write Bandwidth (Excluding Idle)")
    report.add_fio_bandwidth_plot(bandwidth_file)

    report.add_pagebreak()
    report.add_subheading("SEQUENTIAL READS")
    report.add_paragraph(
        """These plots are for reads using sequential addressing, block size of 128 KiB, and
        queue depth of 32."""
    )
    data_directory = os.path.join(test_dir, "7_sequential_read", "sample_info")
    bandwidth_file = os.path.join(test_dir, "7_sequential_read", "bandwidth_read.csv")

    if ref_directory is not None:
        ref_data_directory = os.path.join(ref_directory, "7_sequential_read", "sample_info")

    report.add_subheading2("Temperature (Including Idle)")
    report.add_temperature_plot(data_directory)
    report.add_subheading2("IO Read Bandwidth (Including Idle)")
    report.add_bandwidth_plot(data_directory, ref_data_directory, read=True, write=False)
    report.add_subheading2("IO Read Bandwidth (Excluding Idle)")
    report.add_fio_bandwidth_plot(bandwidth_file)

    report.add_verifications(test_result)
