# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os


def report(report, test_result):
    report.add_description(
        """This test reads the NVMe drive information at the end of the test suite and verifies
        the drive is healthy, not worn out, and no unexpected changes occurred during the test suite.
        <br/><br/>

        The test verifies the following unexpected changes do not occur. Static parameters, such as
        Model and Serial Number, must not change.  SMART counters, such as Power-On Hours, must not
        decrement.  Error parameters, such as media and data integrity errors, must not increase.
        The change in Power On Hours must match the host computer time change.
        <br/><br/>

        For additional details see <u>Read and compare NVMe information with nvmecmd</u> [4].
        """
    )
    report.add_results(test_result)

    """
    data = test_result["data"]
    test_dir = os.path.join(report._results_directory, test_result["directory name"])
    """

    report.add_paragraph("""blah, blah, blah""")

    report.add_verifications(test_result)
