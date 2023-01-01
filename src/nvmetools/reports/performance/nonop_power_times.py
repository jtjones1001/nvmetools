import os

from nvmetools.support.conversions import US_IN_MS, as_int
from nvmetools.support.info import Info


def report(report, test_result):

    test_dir = os.path.join(report._results_directory, test_result["directory name"])
    info_file = os.path.join(test_dir, "1_test_start_info", "nvme.info.json")
    parameters = Info(nvme=None, from_file=info_file).parameters

    report.add_description(
        """ This test reports the entry timeout and exit latency for non-operational power
        states.  Exit latency is determined by measuring the latency of the first IO
        read after an idle period long enough that the drive transitions to a lower
        power state.  Several samples are taken and the outliers are removed
        to avoid unrelated latency changes from OS interupts or drive accesses that take the
        drive out of idle.
        <br/><br/>

        The entry timeout is the idle time required for the drive to transition to a lower
        power state.  The entry timeout is an OS setting that can be adjusted by the end
        user.  Some systems, such as Windows
        laptops, typically have different values for battery and AC power.
        The test determines the entry timeout by increasing the idle time until the resulting
        IO read latency increases indicating a lower power state was entered.
        <br/><br/>

        If Autonomous Power State Transition (APST) is enabled, the drive will automatically
        transition to a non-operational power state.  The value of Idle Time Prior to
        Transition (ITPT) defines the idle time required before transitioning.  The Idle
        Transition Power State (ITPS) defines the state to transition to.  Each Power State
        can have it's own ITPT and ITPS value.
        <br/><br/>

        If APST is disabled, the host OS will transition the drive to the lower power states.
        This appears to be the case for the inbox Windows driver.  The Windows driver uses
        four parameters to determine the timeout and which state to transition to.  The
        Primary and Secondary NVMe Idle Timeouts work the same as ITPT above.  The Primary and
        Secondary NVMe Power State Transition Latency Tolerance define the state to transition
        to.  The driver transitions to the lowest state where the sum of the entry and exit
        latency is less than the NVMe Power State Transition Latency Tolerance."""
    )

    report.add_results(test_result)

    if "Autonomous Power State Transition Enable (APSTE)" in parameters:
        apst_enabled = parameters["Autonomous Power State Transition Enable (APSTE)"] == "Enabled"
    else:
        apst_enabled = False

    if apst_enabled:
        report.add_paragraph(
            """Autonomous Power State Transition (APST) is enabled.  The drive is changing
            power states without host interaction based on the values of ITPT and ITPS.
            <br/><br/>

            In the table below a blank cell indicates the value is not reported or doesn't
            apply.  Typically, latency values are not reported for operational power states. """
        )
        table_rows = [["POWER STATE", "NOP", "ENTRY LATENCY", "EXIT LATENCY", "ITPT", "ITPS"]]
    else:
        report.add_paragraph(
            """Autonomous Power State Transition (APST) is disabled.  The host OS is changing
            power states.
            <br/><br/>

            In the table below a blank cell indicates the value is not reported or doesn't
            apply.  Typically, latency values are not reported for operational power states. """
        )

        table_rows = [["POWER STATE", "NOP", "ENTRY LATENCY", "EXIT LATENCY", "TOTAL LATENCY"]]

    exlats_ms = {}
    timeouts_ms = {}

    for index in range(int(parameters["Number of Power States Support (NPSS)"])):
        enlat = parameters[f"Power State {index} Entry Latency (ENLAT)"]
        exlat = parameters[f"Power State {index} Exit Latency (EXLAT)"]
        nops = parameters[f"Power State {index} Non-Operational State (NOPS)"]

        if enlat == "Not Reported":
            enlat = ""
        else:
            enlat_ms = as_int(enlat.split("(")[0].strip()) / US_IN_MS
            enlat = f"{enlat_ms} mS"

        if exlat == "Not Reported":
            exlat = ""
        else:
            exlat_ms = as_int(exlat.split("(")[0].strip()) / US_IN_MS
            exlats_ms[f"PS{index} EXLAT"] = exlat_ms
            exlat = f"{exlat_ms} mS"

        if exlat != "" and enlat != "":
            total_latency = f"{enlat_ms+exlat_ms} mS"
        else:
            total_latency = ""

        if apst_enabled:
            itpt = parameters[f"Power State {index} Idle Time Prior to Transition (ITPT)"]
            if itpt != "Disabled":
                itpt_ms = as_int(itpt)
                itpt_values = list(timeouts_ms.values())
                if itpt_ms not in itpt_values:
                    timeouts_ms[f"PS{index} ITPT"] = itpt_ms

                itps = parameters[f"Power State {index} Idle Transition Power State (ITPS)"]
            else:
                itps = ""

            table_rows.append([str(index), nops, enlat, exlat, itpt, itps])
        else:
            table_rows.append([str(index), nops, enlat, exlat, total_latency])

    if apst_enabled:
        report.add_table(table_rows, [120, 70, 100, 100, 70, 70])
    else:
        report.add_table(table_rows, [120, 70, 100, 100, 100])

    report.add_paragraph(
        """The latency in the plot below is for the first read after the idle time.  This should be
        less than or equal to the power state exit latency."""
    )
    report.add_power_timing_plot(os.path.join(test_dir, "results.csv"), timeouts_ms, exlats_ms)

    if not apst_enabled and test_result["data"]["os power plan"] != "N/A":
        report.add_paragraph("""<br/><br/> The table below lists the Windows OS power plan settings.""")

        plan = test_result["data"]["os power plan"]
        table_rows = [
            ["PARAMETER", "AC POWER", "DC POWER"],
            ["ASPM", plan["ac aspm"], plan["dc aspm"]],
            ["NOPPME", plan["ac noppme"], plan["dc noppme"]],
            ["Primary Latency", f"{plan['ac primary latency']} mS", f"{plan['dc primary latency']} mS"],
            ["Primary Timeout", f"{plan['ac primary timeout']} mS", f"{plan['dc primary timeout']} mS"],
            [
                "Secondary Latency",
                f"{plan['ac secondary latency']} mS",
                f"{plan['dc secondary latency']} mS",
            ],
            [
                "Secondary Timeout",
                f"{plan['ac secondary timeout']} mS",
                f"{plan['dc secondary timeout']} mS",
            ],
        ]
        report.add_table(table_rows, [150, 150, 150])

    report.add_verifications(test_result)
