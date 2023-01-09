# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os

from nvmetools.support.conversions import US_IN_MS, as_int
from nvmetools.support.info import Info


def report(report, test_result):

    report.add_description(
        """ This test measures the time to enter and exit power states.  Power state timing is
        determined by reading the latency of the first IO read after an idle period that is long
        enough to enter a lower power state.  When a lower power state is entered, the time to exit
        the power state is added to the normal IO read latency.  The time to enter a power state is
        measured by increasing the idle period until a change in read latency is observed.
        <br/><br/>

        The first part of this test measures read latency for small idle periods up to 1mS.  These
        small idle periods activate low-level hardware power features such as PCIe ASPM and processor
        power states. The second part measures read latency for idle periods up to several seconds.
        These longer idle periods activate the NVMe power states in addition to the low-level power
        states.
        <br/><br/>

        Systems with NVMe drives typically have multiple power saving features that can interact.
        These features have several settings that can be configured in the BIOS or Operating System
        (OS).  Therefore it is important to run this test with the same settings as the end-user.
        <br/><br/>

        NVMe power states are controlled by either the OS or the NVMe drive itself.
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
    report.add_paragraph(
        """Short idle periods can activate low-level hardware features, such as PCIe ASPM, that
        autonomously transition to power saving states.  These low-level power states typically have
        very small enter and exit times that typically have no significant effect on IO performance.
        For reference, this test plots IO read latency for short idle periods of 0 to 1mS to
        determine if anything unexpected is occuring.
        <br/><br/>

        In the plot below, verify the latency behaves as expected. For details see <u>Analyze idle
        latency plots with fio</u> [9] """
    )
    test_dir = os.path.join(report._results_directory, test_result["directory name"])
    info_file = os.path.join(test_dir, "1_test_start_info", "nvme.info.json")
    start_info = Info(nvme=None, from_file=info_file)
    parameters = start_info.parameters

    step_result_file = os.path.join(test_dir, "3_short_idle", "results.csv")
    report.add_idle_latency_plot(step_result_file, unit="uS")

    report.add_subheading2("NVMe Power States")

    if "Autonomous Power State Transition Enable (APSTE)" in parameters:
        apst_enabled = parameters["Autonomous Power State Transition Enable (APSTE)"] == "Enabled"
    else:
        apst_enabled = False

    if apst_enabled:
        report.add_paragraph(
            """Autonomous Power State Transition (APST) is enabled therefore the NVMe drive is
            changing power states without host interaction based on the values of ITPT and ITPS."""
        )
        table_rows = [["POWER STATE", "NOP", "ENTRY LATENCY", "EXIT LATENCY", "ITPT", "ITPS"]]
    else:
        report.add_paragraph(
            """Autonomous Power State Transition (APST) is disabled therefore the host OS is changing
            power states."""
        )
        if "powerplan" in start_info.info["_metadata"]["system"]:
            report.add_paragraph("""The table below lists the Windows OS power plan settings.""")

            plan = start_info.info["_metadata"]["system"]["powerplan"]
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

        table_rows = [["POWER STATE", "NOP", "ENTRY LATENCY", "EXIT LATENCY", "TOTAL LATENCY"]]

    report.add_paragraph("""The table below lists the NVMe power states.""")

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
        report.add_table(table_rows, [100, 50, 100, 100, 70, 70])
    else:
        report.add_table(table_rows, [100, 50, 100, 100, 100])

    report.add_paragraph(
        """In the plot below, verify the power state entry and exit latencies match those defined
        above."""
    )
    step_result_file = os.path.join(test_dir, "4_long_idle", "results.csv")
    report.add_power_state_plot(step_result_file, timeouts_ms, exlats_ms)
    report.add_pagebreak()
    report.add_verifications(test_result)
