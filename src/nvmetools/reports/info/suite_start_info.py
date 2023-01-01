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

        This test defines worn out as Percentage Used, Percentage Data Written, or Percentage
        Warranty Used exceeding {test_result["data"]["Wear Percent Limit"]}%.  This provides a guard
        band so no wear percentage exceeds 100% during the test suite.  The percentages are determined
        from the SMART attributes Percentage Used, Data Written, and Power On Hours and the drive
        specifications TBW and Warranty Years.  If TBW and Warranty Years are not provided the
        Percentage Data Written and Percentage Warranty Used cannot be verified.
        <br/><br/>

        A drive is defined as unhealthy if 1) any prior self-test results failed or 2) has critical
        warnings or media and integrity errors or 3) has operated above the critical temperature or
        4) has had an excessive amount of thermal throttling.   The self-test results are read from
        Log Page 6 and the SMART attributes from Log Page 2.
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
        ["Critical Warnings", parameters["Critical Warnings"], ""],
        ["Media and Integrity Errors", parameters["Media and Data Integrity Errors"], ""],
    ]
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
        """The Percentage Used SMART attribute is the primary reference for drive wear.  If the drive
        Warranty and TBW are specified the Percentage Data Written and Percentage Warranty Used are
        calculated and verified.
        <br/><br/>

        Percentage Data Written is defined as 100 * (Data Written / TBW) where TBW (Terabytes
        Written) is the total amount of data that can be written to the drive during the warranty period.
        Data Written is the SMART attribute that reports the data written to the drive.
        <br/><br/>

        Percentage Warranty Used is defined as 100 * (Power On Hours / Warranty Hours) where warranty hours
        is the number of days in the warranty multiplied by 8 hours for client drives or 24 hours for
        enterprise drives."""
    )
    table_rows = [
        ["PARAMETER", "VALUE", "NOTE"],
        ["Percentage Used", f"{as_int(parameters['Percentage Used'])}%", "SMART attribute"],
        ["Data Written", f"{as_float(parameters['Data Written']):,.3f} GB", "SMART attribute"],
        ["Power On Hours", f"{as_int(parameters['Power On Hours']):,}", "SMART attribute"],
    ]
    if parameters["TBW"] == "NA":
        table_rows.extend(
            [
                ["Terabytes Written (TBW)", "NA", "User Input"],
                ["Percentage Data Written", "NA", "Calculated"],
            ]
        )
    else:
        table_rows.extend(
            [
                ["Terabytes Written (TBW)", f"{parameters['TBW']} TB", "User Input"],
                ["Percentage Data Written", f"{as_float(parameters['Data Used']):.1f}%", "Calculated"],
            ]
        )

    if parameters["Warranty Years"] == "NA":
        table_rows.extend(
            [
                ["Warranty Years", "NA", "User input"],
                ["Warranty Hours", "NA", "Calculated"],
                ["Percentage Warranty Used", "NA", "Calculated"],
            ]
        )
    else:
        table_rows.extend(
            [
                ["Warranty Years", f"{as_int(parameters['Warranty Years'])} years", "User input"],
                ["Warranty Hours", f"{as_int(parameters['Warranty Hours']):,}", "Calculated"],
                ["Percentage Warranty Used", f"{as_float(parameters['Warranty Used']):.1f}%", "Calculated"],
            ]
        )
    report.add_table(rows=table_rows, widths=[225, 100, 175])

    report.add_verifications(test_result)
