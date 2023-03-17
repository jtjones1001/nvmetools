# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
def report(report, test_result):

    report.add_description(
        f"""This test reports the bandwidth for short bursts of IO reads and writes.   Short bursts
        avoid performance reducing behavior such as thermal throttling, excessive SLC write cache
        misses, and shortage of erased blocks for future writes.  Short IO bursts result in high
        bandwidth measurements ideal for datasheet comparisons and benchmarking applications such as
        spreadsheets and word processors that intermittently read and write small to medium files.
        <br/><br/>

        This test runs a variety of block sizes and queue depths across four common IO patterns:
        random writes, random reads, sequential writes and sequential reads. The bandwidth should
        increase as block size and queue depth increase until the bandwidth
        saturates.  This maximum bandwidth is expected to be different between reads and
        writes but not between random and sequential access types. There is no standard performance
        specification for drive datasheets so refer to the datasheet of the drive
        under test to determine the block size and queue depth to compare. No data integrity
        checking is done to avoid any effect the performance numbers.
        <br/><br/>

        Each burst lasts for {test_result['data']['runtime sec']} seconds and is followed
        by an idle period to allow the drive temperature and background activity to return to the
        initial state.   During the idle state the drive is likely to enter a non-operational power
        state.  The latency to exit the non-operational power state would effect
        the measured bandwidth.  To avoid the effects of exiting the power state, this
        test excludes the first {test_result['data']['ramp time sec']} seconds of the burst.
        <br/><br/>

        The test uses the standard OS software stack which may limit the maximum block size or queue
        depth. For example, some Linux versions limit the block size to 128KiB.
        <br/><br/>

        For additional details see <u>NVMe IO performance measurement with fio and nvmecmd</u> [8].
        """
    )
    report.add_results(test_result)
    report.add_paragraph(
        """This table shows the bandwidth for several common datasheet and IO benchmark
        queue depths and block sizes."""
    )
    report.add_bandwidth_performance_table(test_result)

    report.add_pagebreak()
    report.add_short_burst_plot(test_result)

    report.add_pagebreak()
    report.add_verifications(test_result)
