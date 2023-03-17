# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os


def report(report, test_result):
    report.add_description(
        """This test verifies the performance and reliability of firmware download.   Different
        firmware versions are downloaded to multiple slots.  While running a moderate IO stress
        workload the test continuously downloads firmware to different slots (versions).  The test
        completes 100 downloads.
        <br/><br/>

        Reliability is defined as no IO errors, data corruption, parameter changes,
        or failed firmware downloads.
        <br/><br/>

        Performance is defined as the download time and the maximum IO latency.
        <br/><br/>


        For additional details see <u>Update firmware with nvmecmd</u> [7].
        """
    )
    report.add_results(test_result)

    if test_result["result"] == "SKIPPED":

        report.add_paragraph(
            """The test was not completed because the firmware files needed for the update
            were not found."""
        )

        return

    report.add_verifications(test_result)
