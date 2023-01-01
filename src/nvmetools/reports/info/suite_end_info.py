# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os

from nvmetools.support.conversions import as_datetime


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

    data = test_result["data"]
    start_date = as_datetime(data["start_info"]["metadata"]["date"])
    end_date = as_datetime(data["end_info"]["metadata"]["date"])
    delta_time = str(end_date - start_date)[:-3]

    report.add_paragraph(
        f"""The host reported a time difference of {delta_time} and the change in Power
        On Hours was {data["end_info"]["compare"]["deltas"]["Power On Hours"]["delta"]}."""
    )

    if len(data["end_info"]["compare"]["static_mismatches"]) == 0:
        this_paragraph = f"""A total of {data["end_info"]["compare"]['static_parameters']} static parameters
        were verified not to change.  """
    else:
        this_paragraph = f"""A total of {data["end_info"]["compare"]['static_parameters']} static parameters
        were verified with {len(data["end_info"]["compare"]['static_mismatches'])} unexpected changes.  """

    if len(data["end_info"]["compare"]["counter_decrements"]) == 0:
        this_paragraph += f"""A total of {data["end_info"]["compare"]['counter_parameters']} counter parameters
        were verified not to decrement."""
    else:
        this_paragraph += f"""A total of {data["end_info"]["compare"]['counter_parameters']} counter parameters
        were verified with {len(data["end_info"]["compare"]['counter_decrements'])} unexpected decrements."""
    report.add_paragraph(this_paragraph)

    table_rows = [["PARAMETER", "START", "END"]]
    for parameter_name in data["end_info"]["compare"]["static_mismatches"]:
        parameter = data["end_info"]["compare"]["static_mismatches"][parameter_name]
        table_rows.append([parameter_name, parameter[0], parameter[1]])

    for parameter_name in data["end_info"]["compare"]["counter_decrements"]:
        parameter = data["end_info"]["compare"]["counter_decrements"][parameter_name]
        table_rows.append([parameter_name, parameter[0], parameter[1]])

    report.add_verifications(test_result)
