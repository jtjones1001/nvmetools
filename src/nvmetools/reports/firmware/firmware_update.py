# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os


def report(report, test_result):
    report.add_description(
        """This test updates the NVMe drive firmware.  The test downloads and activates the
        latest firmware version and verifies if does not effect IO traffic, no parameters change,
        firmware information is updated.  All firmware slots are tested.
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
