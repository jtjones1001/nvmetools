# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------


def report(report, test_result):
    data = test_result["data"]

    report.add_description(
        f"""This test verifies the accuracy of the Data Read and Data Written SMART attributes.
        The SMART attributes are compared against the disk counters reported
        by the python psutil package.  To ensure a large enough sample for comparison,
        IO read and writes are run for three minutes in a high bandwidth configuration.
        <br/><br/>

        The SMART attribute resolution is {data['smart data lsb']:,} bytes according to the <u>NVMe
        Specification</u> [1].  The current test limit has been set to the resolution of the
        SMART attributes."""
    )
    report.add_results(test_result)

    table_rows = [
        ["PARAMETER", "VALUE", "DELTA", "LIMIT"],
        [
            "Bytes written from psutil counter",
            f"{data['write']['counter']:,}",
            "",
            "",
        ],
        [
            "Bytes written reported by SMART",
            f"{data['write']['smart']:,}",
            f"{data['write']['delta']['smart']:,}",
            f"{data['smart data lsb']:,}",
        ],
        [
            "Bytes read reported by psutil counter",
            f"{data['read']['counter']:,}",
            "",
            "",
        ],
        [
            "Bytes read reported by SMART",
            f"{data['read']['smart']:,}",
            f"{data['read']['delta']['smart']:,}",
            f"{data['smart data lsb']:,}",
        ],
    ]
    report.add_table(table_rows, [225, 100, 100, 75])

    report.add_paragraph(
        """ The tables below include fio reported data to determine if anything other
        than fio was reading or writing the drive during the test.  If the drive under
        test is the OS drive than additional read and writes are likely. """
    )
    table_rows = [
        ["PARAMETER", "VALUE", "DELTA"],
        [
            "Bytes read reported by fio",
            f"{data['read']['fio']:,}",
            f"{data['read']['delta']['fio']:,}",
        ],
        [
            "Bytes written reported by fio",
            f"{data['write']['fio']:,}",
            f"{data['write']['delta']['fio']:,}",
        ],
    ]
    report.add_table(table_rows, [225, 100, 100])

    report.add_verifications(test_result)
