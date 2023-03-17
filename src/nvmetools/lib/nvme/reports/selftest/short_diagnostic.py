# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Test and report for running the short self-test diagnostic.

This module runs the short self-test diagnostic.
"""

from nvmetools.support.conversions import as_datetime, as_int

# ---------------------------------------------------------------------------------------------------
# Define settings for this test
# ---------------------------------------------------------------------------------------------------
LINEAR_LIMIT = 0.9  # Limit for linearity of self-test progress reported.


def report(report, test_result):

    data = test_result["data"]

    report.add_description(
        """The short Self-test is a diagnostic testing sequence that tests the integrity
        and functionality of the controller and may include testing of the media
        associated with namespaces.   The run time is 2 minutes or less. The results are
        reported in Log Page 6 during and after the self-test."""
    )
    report.add_results(test_result)

    if "logfile" not in data:
        if data["return code"] == 30:
            report.add_paragraph(" The diagnostic failed to run because the device does not support self-test.")
        elif data["return code"] == 31:
            report.add_paragraph(
                """ The diagnostics failed to start.  This could be a known issue with the
                Windows driver where a minimum of 10 minutes is required between self-tests.
                Recommend waiting 10 minutesand running test again."""
            )
        elif data["return code"] == 32:
            report.add_paragraph(
                """ The diagnostics failed to run because the device does not support
                extended self-test."""
            )
        else:
            report.add_paragraph(
                """ The diagnostics failed to run for unknown reason.
                Check the logs for details."""
            )
    else:
        if data["return code"] == 0:
            report.add_paragraph(
                f""" The diagnostics passed and completed within the expected 2 minute run
                time. The progress reported was monotonic and roughly linear (having a
                Pearson product-moment correlation coefficient greater than
                {LINEAR_LIMIT}). """
            )
        else:
            report.add_paragraph(""" The diagnostic failed. Refer to the logs and table below for details.""")

        table_rows = [
            ["PARAMETER", "VALUE", "NOTE"],
            ["Run Time", f"{data['runtime']:.3f} Min", "Must be less than 2 minutes"],
            ["Monotonicity", data["monotonic"], "Must be monotonic"],
            [
                "Linearity",
                f"{data['linear']:.3f}",
                f"Must be greater than {LINEAR_LIMIT}",
            ],
        ]
        report.add_table(table_rows, [225, 100, 175])

        diag_time = []
        diag_temp = []
        diag_progress = []
        diag_progress_time = []
        start_time = as_datetime(data["logfile"]["selftest details"]["status"][0]["timestamp"])

        for sample in data["logfile"]["selftest details"]["status"]:
            sample_time = as_datetime(sample["timestamp"])
            diag_temp.append(as_int(sample["Composite Temperature"]))
            diag_time.append((sample_time - start_time).total_seconds() / 60.00)
            if sample["status"] != 0:
                diag_progress.append(as_int(sample["percent complete"]))
                diag_progress_time.append((sample_time - start_time).total_seconds() / 60.00)

        report.add_paragraph(
            """This plot shows the progress reported in Log Page 6 during the diagnostic.
            <br/><br/>"""
        )
        report.add_diagnostic_progress_plot(diag_progress_time, diag_progress)
        report.add_pagebreak()
        report.add_paragraph(
            """This plot shows the NVMe composite temperature during the diagnostic.
            The horizontal red lines are the throttle temperature limits for reference.
            <br/><br/>"""
        )
        report.add_diagnostic_temperature_plot(diag_time, diag_temp)
    report.add_verifications(test_result)
