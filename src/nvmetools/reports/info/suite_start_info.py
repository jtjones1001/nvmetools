# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Report for verifying the starting information."""

from nvmetools.support.conversions import as_float, as_int


def report(report, test_result):
    report.add_description(
        f"""This test reads the NVMe drive information at the start of a test suite. If the drive is
        unhealthy or worn out the test suite is stopped.  At the end of the suite, this start
        information is compared with the suite end information to verify no unexpected changes
        occurred during the testing.
        <br/><br/>

        This test defines worn out as Percentage Used exceeding
        {test_result["data"]["Wear Percent Limit"]}% or the Available Spare Percentage being lower
        than the Available Spare Threshold. These values are SMART attributes found in the
        SMART/Health log.
        <br/><br/>

        A drive is defined as unhealthy if 1) any prior self-test results failed or 2) has critical
        errors or 3) has operated above the critical temperature or 4) has had an excessive amount
        of thermal throttling.   The self-test results are read from Log Page 6 and the SMART
        attributes from Log Page 2.
        <br/><br/>

        The information is read using the <u>nvmecmd utility</u> [2].  This utility uses NVMe Admin
        Commands Identify Controller, Identify Namespace, Get Log Page, and Get Feature to get most
        of the information.  A small anount of information is read from the Operating System, such
        as the driver verison and PCIe parameters.
        <br/><br/>

        For additional details see <u>Read and compare NVMe information with nvmecmd</u> [4].
        """
    )
    report.add_results(test_result)

    commands = test_result["data"]["commands"]
    parameters = test_result["data"]["parameters"]

    report.add_paragraph(
        """The table below lists the NVMe Admin Commands completed.  The nvmecmd utility only
        supports Namespace 1 and a subset of the log pages and features."""
    )
    table_rows = [["Admin Command", "Time (ms)", "Return Bytes", "Return Code"]]
    for command in commands:
        table_rows.append(
            [
                command["admin command"],
                f"{command['time in ms']:0.3f}",
                command["bytes returned"],
                command["return code"],
            ]
        )
    report.add_table(table_rows, [260, 80, 80, 80])

    report.add_subheading2("Drive Health: Self-Test Results")
    report.add_paragraph(
        """The most recent 20 self-test results, short and extended, were read
        from Log Page 6. The drive is considered unhealthy if any prior results are failures."""
    )

    table_rows = [
        ["PARAMETER", "VALUE", "NOTE"],
        ["Prior self-test results", parameters["Current Number Of Self-Tests"], "Logs up to 20"],
        ["Prior self-test failures", parameters["Number Of Failed Self-Tests"], ""],
    ]
    report.add_table(table_rows, widths=[225, 100, 175])

    report.add_subheading2("Drive Health: Errors and Warnings")
    report.add_paragraph(
        """The drive is considered unhealthy if the SMART attributes contain critical warnings
        or media and integrity errors.
        """
    )
    table_rows = [
        ["PARAMETER", "VALUE", "NOTE"],
        ["Media and Integrity Errors", parameters["Media and Data Integrity Errors"], ""],
        ["NVM Subsystem Unreliable", parameters["NVM Subsystem Unreliable"], ""],
        ["Media in Read-only", parameters["Media in Read-only"], ""],
        ["Volatile Memory Backup Failed", parameters["Volatile Memory Backup Failed"], ""],
    ]
    if "Persistent Memory Unreliable" in parameters:
        table_rows.append(
            ["Persistent Memory Unreliable", parameters["Persistent Memory Unreliable"], ""],
        )
    report.add_table(table_rows, widths=[225, 100, 175])

    report.add_subheading2("Drive Health: Temperature Throttling")
    report.add_paragraph(
        f"""The drive is considered unhealthy if it has operated above the critical temperature or
        the percentage throttled is above {test_result["data"]["Throttle Percent Limit"]}%.
        <br/><br/>

        Percentage Throttled is defined as 100 * (Hours Throttled / Power On Hours) where Hours
        Throttled is the cumulative time of all throttle states.
        """
    )
    table_rows = [
        ["PARAMETER", "VALUE", "NOTE"],
        [
            "Percentage Throttled",
            f"{as_float(parameters['Percent Throttled']):.1f}% ",
            "",
        ],
        [
            "Thermal Management Temperature 1 Time",
            f"{as_int(parameters['Thermal Management Temperature 1 Time']):,} sec",
            f"{(as_int(parameters['Thermal Management Temperature 1 Time'])/3600):,.2f} Hours",
        ],
        [
            "Thermal Management Temperature 2 Time",
            f"{as_int(parameters['Thermal Management Temperature 2 Time']):,} sec",
            f"{(as_int(parameters['Thermal Management Temperature 2 Time'])/3600):,.2f} Hours",
        ],
        [
            "Warning Composite Temperature Time",
            f"{as_int(parameters['Warning Composite Temperature Time']):,} min",
            f"{(as_int(parameters['Warning Composite Temperature Time'])/60):,.2f} Hours",
        ],
        [
            "Critical Composite Temperature Time",
            f"{as_int(parameters['Critical Composite Temperature Time']):,} min",
            f"{(as_int(parameters['Critical Composite Temperature Time'])/60):,.2f} Hours",
        ],
    ]
    report.add_table(table_rows, widths=[225, 100, 175])

    report.add_subheading2("Drive Wear")
    report.add_paragraph(
        """The Percentage Used, Available Spare, and Available Spare Threshold are the primary SMART
        attributes that determine drive wear.

        If the Percentage Used is greater than 100% or the Available Spare is less then the threshold
        the drive is considered worn out and should not be tested.
        <br/><br/>"""
    )
    table_rows = [
        ["PARAMETER", "VALUE", "NOTE"],
        ["Percentage Used", f"{as_int(parameters['Percentage Used'])}%", "SMART attribute"],
        ["Available Spare", f"{as_int(parameters['Available Spare'])}%", "SMART attribute"],
        ["Available Spare Threshold", f"{as_int(parameters['Available Spare Threshold'])}%", "SMART attribute"],
    ]

    report.add_table(rows=table_rows, widths=[225, 100, 175])

    report.add_verifications(test_result)
