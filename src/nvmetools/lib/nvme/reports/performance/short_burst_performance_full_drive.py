# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
def report(report, test_result):
    """Create pages for pdf test report provided."""

    report.add_description(
        """
        This test is the same as Short Burst Performance test except the drive capacity
        is almost full at the start.  Full drives may have lower performance than empty drives
        because of a lower number of erased blocks available for writes and a smaller
        dynamic cache.
        <br/><br/>
        For additional details refer to the Short Burst Performance test. """
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
