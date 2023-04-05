# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""This module provides classes to create PDF reports for NVMe tests and information.

The InfoReport class creates a PDF report for the NVMe information collected with the readnvme console
command.  The NvmeReport class creates the PDF report for the test results from the checknvme console
command.

This module uses the reportlab package to create the PDF files and matplotlib to create the charts within
the PDF file.  More details here:

    `ReportLab site  <https://docs.reportlab.com/>`_

    `matplotlib site <https://matplotlib.org/>`_
"""
import base64
import json
import os
import webbrowser

from nvmetools import RESOURCE_DIRECTORY, RESULTS_FILE
from nvmetools.support.log import log


SKIPPED = "SKIPPED"
PASSED = "PASSED"
FAILED = "FAILED"
ABORTED = "ABORTED"
STARTED = "STARTED"


def create_dashboard(results_directory, nvme_uid=None, all_nvme_info=None, show_dashboard=True):

    if all_nvme_info is None:
        test_view = True
        dashboard_file = os.path.join(results_directory, "testnvme.html")
    else:
        test_view = False
        dashboard_file = os.path.join(results_directory, "viewnvme.html")

    with open(os.path.join(RESOURCE_DIRECTORY, "html", "template.html"), "r") as file_object:

        lines = file_object.readlines()

        write_lines = []
        for line in lines:

            if line.find("./data.js") != -1:
                all_nvme = {}
                write_lines.append("<script>\n")

                view_filter_file = os.path.join(RESOURCE_DIRECTORY, "html", "filter.json")
                with open(view_filter_file, "r") as file_object:
                    filters = json.load(file_object)
                    mystring = f"const filters = {json.dumps(filters, sort_keys=False, indent=4)};\n"
                    mystring += 'var globalParameterView = "summary"\n'
                    mystring += 'var globalSelectedSection = "summary"\n'

                if test_view:
                    mystring += "const testView = true;\n\n"
                    mystring += "var globalSelectedTest = 1\n"
                    mystring += "var globalSelectedTest = 1\n"
                    mystring += "var globalSelectedRequirement = 0\n"

                    json_result_file = os.path.join(results_directory, RESULTS_FILE)
                    with open(json_result_file, "r") as file_object:
                        data = json.load(file_object)

                        start_parameters = data["data"]["start_info"]["full_parameters"]
                        nvme_uid = start_parameters["Unique Description"]["value"]
                        if "end_info" in data:
                            report_info = data["data"]["end_info"]
                        else:
                            report_info = data["data"]["start_info"]

                        all_nvme[nvme_uid] = {
                            "parameters": report_info["full_parameters"],
                            "system": report_info["metadata"]["system"],
                            "command log": report_info["command log"],
                            "error log": report_info["error log"],
                            "event log": report_info["event log"],
                            "self-test log": report_info["self-test log"],
                        }

                        rqmts = []
                        for index, rqmt in enumerate(data["rqmts"]):
                            rqmts.append(
                                {
                                    "number": index + 1,
                                    "title": rqmt,
                                    "pass": data["rqmts"][rqmt]["pass"],
                                    "fail": data["rqmts"][rqmt]["fail"],
                                }
                            )
                        mystring += f"const rqmtListData = {json.dumps(rqmts, sort_keys=False, indent=4)};\n\n"
                        mystring += (
                            f"const testListData = {json.dumps(data['tests'], sort_keys=False, indent=4)};\n\n"
                        )

                        for index, _ver in enumerate(data["verifications"]):
                            data["verifications"][index]["value"] = str(data["verifications"][index]["value"])

                        mystring += "const verificationListData = "
                        mystring += f"{json.dumps(data['verifications'], sort_keys=False, indent=4)};\n\n"

                        mystring += f"\n const info = {json.dumps(data, sort_keys=False, indent=4)};\n\n"

                else:
                    mystring += "const testView = false;\n\n"
                    all_nvme = {}
                    for uid in all_nvme_info:
                        if "Device Tree" in all_nvme_info[uid].metadata["system"]:
                            all_nvme_info[uid].metadata["system"].pop("Device Tree")
                        all_nvme[uid] = {
                            "parameters": all_nvme_info[uid].info["nvme"]["parameters"],
                            "system": all_nvme_info[uid].metadata["system"],
                            "command log": [],
                            "error log": [],
                            "event log": [],
                            "self-test log": [],
                            "health": {},
                        }

                        if "self-test log" in all_nvme_info[uid].info["nvme"]:
                            all_nvme[uid]["self-test log"] = all_nvme_info[uid].info["nvme"]["self-test log"]

                        if "command log" in all_nvme_info[uid].info["nvme"]:
                            all_nvme[uid]["command log"] = all_nvme_info[uid].info["nvme"]["command log"]

                        if "error log" in all_nvme_info[uid].info["nvme"]:
                            all_nvme[uid]["error log"] = all_nvme_info[uid].info["nvme"]["error log"]

                        if "event log" in all_nvme_info[uid].info["nvme"]:
                            all_nvme[uid]["event log"] = all_nvme_info[uid].info["nvme"]["event log"]

                        add_health_info(all_nvme[uid])

                mystring += "const compareParameters = null;"

                mystring += "const compareInfo = null;"
                mystring += "const compareSystemData = null;\n\n"

                mystring += f'var activeNvme = "{nvme_uid}";\n\n'
                mystring += f"const allData = {json.dumps(all_nvme, sort_keys=False, indent=4)};\n\n"

                for string_line in mystring.split("\n"):
                    write_lines.extend(string_line + "\n")
                write_lines.append("</script>\n")

            elif line.find("./template.css") != -1:
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "template.css")
                write_lines.append("<style>")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</style>")
            elif line.find("./template.js") != -1:
                write_lines.append("<script>")
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "template.js")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</script>")

            elif line.find("./viewFunctions.js") != -1:
                write_lines.append("<script>")
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "viewFunctions.js")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</script>")

            elif line.find("./updateFunctions.js") != -1:
                write_lines.append("<script>")
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "updateFunctions.js")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</script>")

            elif line.find("./dropdown.js") != -1:
                write_lines.append("<script>")
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "dropdown.js")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</script>")

            elif line.find("./chart.min.js") != -1:
                if test_view:
                    write_lines.append("<script>")
                    html_input = os.path.join(RESOURCE_DIRECTORY, "html", "chart.min.js")
                    with open(html_input, "r") as file_object:
                        write_lines.extend(file_object.readlines())
                    write_lines.append("</script>")
            else:
                write_lines.append(line)

    with open(dashboard_file, "w") as file_object:
        file_object.writelines(write_lines)

    if show_dashboard:
        webbrowser.open(dashboard_file, new=2)

    log.info(f"Saving HTML page      {dashboard_file}", indent=False)


def create_reports(results_directory, title="N/A", description="N/A", show_dashboard=True):

    log.info("")
    # Only load when needed because it's slow
    from nvmetools.lib.nvme.pdf_reporter import NvmeReport

    pdf = NvmeReport(results_directory=results_directory, title=title, description=description)
    log.info(f"Saving PDF report     {os.path.join(results_directory,'report.pdf')}", indent=False)

    pdf.save()
    create_dashboard(results_directory, None, None, show_dashboard)


def _encode_png_icon(icon_file):
    """Function to encode image for inclusion in standalone html file."""
    with open(icon_file, "rb") as binary_file:
        binary_file_data = binary_file.read()
        base64_encoded_data = base64.b64encode(binary_file_data)
        base64_message = base64_encoded_data.decode("utf-8")
        print(base64_message)


def update_health(current, new):
    if new == "Critical":
        return new
    elif new == "Suspect":
        if current == "Critical":
            return current
        else:
            return new
    else:
        return current


def add_health_info(info):

    GOOD = "good"
    CRITICAL = "critical"
    SUSPECT = "suspect"
    MISSING = "missing"

    p = info["parameters"]

    # Get diagnostic health

    if len(info["self-test log"]) == 0:

        info["health"]["dt-fails"] = {"state": GOOD, "group": "DIAGNOSTIC SELF-TEST"}
        info["health"]["dt-last"] = {"state": GOOD, "group": "DIAGNOSTIC SELF-TEST"}

        info["parameters"]["Last Self-test"] = {
            "name": "Last Self-test",
            "value": " ",
            "description": "Last self-test diagnostic result",
        }

    else:

        last = info["self-test log"][0]

        info["parameters"]["Last Self-test"] = {
            "name": "Last Self-test",
            "value": f"{last['Result']}<br>{last['Type']}<br>Ran @ hr {last['Power On Hours']}",
            "description": "Last self-test diagnostic result",
        }

        if p["Number Of Failed Self-Tests"]["value"] == "0":
            info["health"]["dt-fails"] = {"state": GOOD, "group": "DIAGNOSTIC SELF-TEST"}
        else:
            info["health"]["dt-fails"] = {"state": CRITICAL, "group": "DIAGNOSTIC SELF-TEST"}

        if last["Result"] == "Failed":
            info["health"]["dt-last"] = {"state": CRITICAL, "group": "DIAGNOSTIC SELF-TEST"}
        else:
            info["health"]["dt-last"] = {"state": GOOD, "group": "DIAGNOSTIC SELF-TEST"}

    # Usage health

    data_written_gb = float(p["Data Written"]["value"].replace(",", "").split()[0])
    poh = int(p["Power On Hours"]["value"].replace(",", "").split()[0])
    drive_size = float(p["Size in GB"]["value"].split()[0])
    drive_writes = data_written_gb / drive_size
    drive_writes_per_hr = poh / drive_writes

    info["parameters"]["Drive Writes"] = {
        "name": "Drive Writes",
        "value": f"{drive_writes:0.1f}<br>{drive_writes_per_hr:0.1f} hr/write",
        "description": "Data written divided by drive size",
    }
    info["parameters"]["Drive Writes Per Hour"] = {
        "name": "Drive Writes Per Hour",
        "value": f"{drive_writes_per_hr:0.1f}<br>{drive_writes_per_hr:0.1f} hrs/write",
        "description": "Hours to complete a drive write on average",
    }

    # Usage Tile

    if int(p["Percentage Used"]["value"].split()[0]) < 100:
        info["health"]["usage-used"] = {"state": GOOD, "group": "USAGE"}
    else:
        info["health"]["usage-used"] = {"state": SUSPECT, "group": "USAGE"}

    if int(p["Available Spare"]["value"].split()[0]) < int(p["Available Spare Threshold"]["value"].split()[0]):
        info["health"]["usage-used"] = {"state": CRITICAL, "group": "USAGE"}
    else:
        info["health"]["usage-used"] = {"state": GOOD, "group": "USAGE"}

    # Temperature Tile

    info["health"]["temp-comp"] = {"state": "Good", "group": "TEMPERATURE"}

    # Throttle Tile

    if float(p["Percent Throttled"]["value"].split()[0]) < 1.0:
        info["health"]["thr-total"] = {"state": GOOD, "group": "TIME THROTTLED"}
    elif float(p["Percent Throttled"]["value"].split()[0]) < 10.0:
        info["health"]["thr-total"] = {"state": SUSPECT, "group": "TIME THROTTLED"}
    else:
        info["health"]["thr-total"] = {"state": CRITICAL, "group": "TIME THROTTLED"}

    if int(p["Critical Composite Temperature Time"]["value"].split()[0]) == 0:
        info["health"]["thr-cctemp"] = {"state": GOOD, "group": "TIME THROTTLED"}
    elif int(p["Critical Composite Temperature Time"]["value"].split()[0]) < 5:
        info["health"]["thr-cctemp"] = {"state": SUSPECT, "group": "TIME THROTTLED"}
    else:
        info["health"]["thr-cctemp"] = {"state": CRITICAL, "group": "TIME THROTTLED"}

    info["health"]["thr-wctemp"] = {"state": GOOD, "group": "TIME THROTTLED"}

    if p["Host Controlled Thermal Management (HCTMA)"]["value"] == "Supported":
        info["health"]["thr-tmt1"] = {"state": GOOD, "group": "TIME THROTTLED"}
        info["health"]["thr-tmt2"] = {"state": GOOD, "group": "TIME THROTTLED"}

    # Persistent Tile

    if p["Persistent Event Log"]["value"] == "Supported":

        smart_errors = int(p["Volatile Backup Memory Failure Events"]["value"])
        if "Persistent Memory Unreliable Events" in p:
            smart_errors += int(p["Persistent Memory Unreliable Events"]["value"])
        smart_errors = int(p["NVM Subsystem Unreliable Events"]["value"])
        smart_errors = int(p["Media Read-only Events"]["value"])

        if smart_errors == 0:
            info["health"]["pe-tile-smart"] = {"state": GOOD, "group": "PERSISTENT EVENTS"}
        else:
            info["health"]["pe-tile-smart"] = {"state": CRITICAL, "group": "PERSISTENT EVENTS"}

        info["parameters"]["SMART Errors"] = {
            "name": "SMART Errors",
            "value": f"{smart_errors}",
            "description": "SMART errors events in Log Page D",
        }

        pci_errors = int(p["PCIe Link Inactive Events"]["value"])
        pci_errors += int(p["PCIe Link Status Change Events"]["value"])
        pci_errors += int(p["PCIe Uncorrectable Fatal Errors"]["value"])
        pci_errors += int(p["PCIe Uncorrectable Non-fatal Errors"]["value"])

        pci_correctable = int(p["PCIe Correctable Errors"]["value"])

        info["health"]["pe-tile-pci"] = {"state": GOOD, "group": "PERSISTENT EVENTS"}
        if pci_correctable > 0:
            info["health"]["pe-tile-pci"] = {"state": SUSPECT, "group": "PERSISTENT EVENTS"}
        if pci_errors > 0:
            info["health"]["pe-tile-pci"] = {"state": CRITICAL, "group": "PERSISTENT EVENTS"}

        info["parameters"]["PCIe Errors"] = {
            "name": "PCIe Errors",
            "value": f"{pci_errors+pci_correctable}",
            "description": "PCIe errors events in Log Page D",
        }

        data_errors = int(p["Write Fault Errors"]["value"])
        data_errors += int(p["Unrecovered Read Errors"]["value"])
        data_errors += int(p["End-to-end Check Errors"]["value"])
        data_errors += int(p["Miscompare Errors"]["value"])

        info["parameters"]["Data Errors"] = {
            "name": "Data Errors",
            "value": f"{data_errors}",
            "description": "Data errors events in Log Page D",
        }

        if data_errors == 0:
            info["health"]["pe-tile-data"] = {"state": GOOD, "group": "PERSISTENT EVENTS"}
        else:
            info["health"]["pe-tile-data"] = {"state": CRITICAL, "group": "PERSISTENT EVENTS"}

        if p["Controller Fatal Events"]["value"] == "0":
            info["health"]["pe-tile-fatal"] = {"state": GOOD, "group": "PERSISTENT EVENTS"}
        else:
            info["health"]["pe-tile-fatal"] = {"state": CRITICAL, "group": "PERSISTENT EVENTS"}

    else:
        info["health"]["pe-tile-smart"] = {"state": MISSING, "group": "PERSISTENT EVENTS"}
        info["health"]["pe-tile-pci"] = {"state": MISSING, "group": "PERSISTENT EVENTS"}
        info["health"]["pe-tile-fatal"] = {"state": MISSING, "group": "PERSISTENT EVENTS"}
        info["health"]["pe-tile-data"] = {"state": MISSING, "group": "PERSISTENT EVENTS"}

    # PCI BW Tile

    if p["PCI Bandwidth"]["value"] == p["PCI Rated Bandwidth"]["value"]:
        info["health"]["pci-tile-bw"] = {"state": GOOD, "group": "PCI EXPRESS BANDWIDTH"}
    else:
        info["health"]["pci-tile-bw"] = {"state": SUSPECT, "group": "PCI EXPRESS BANDWIDTH"}

    if p["PCI Speed"]["value"] == p["PCI Rated Speed"]["value"]:
        info["health"]["pci-tile-speed"] = {"state": GOOD, "group": "PCI EXPRESS BANDWIDTH"}
    else:
        info["health"]["pci-tile-speed"] = {"state": SUSPECT, "group": "PCI EXPRESS BANDWIDTH"}

    if p["PCI Width"]["value"] == p["PCI Rated Width"]["value"]:
        info["health"]["pci-tile-width"] = {"state": GOOD, "group": "PCI EXPRESS BANDWIDTH"}
    else:
        info["health"]["pci-tile-width"] = {"state": SUSPECT, "group": "PCI EXPRESS BANDWIDTH"}

    # SMART Tile Health

    if p["NVM Subsystem Unreliable"]["value"] == "No":
        info["health"]["smart-tile-reliability"] = {"state": GOOD, "group": "SMART ERRORS"}
    else:
        info["health"]["smart-tile-reliability"] = {"state": CRITICAL, "group": "SMART ERRORS"}

    if "Persistent Memory Unreliable" in p:
        if p["Persistent Memory Unreliable"]["value"] == "No":
            info["health"]["smart-tile-pmr"] = {"state": GOOD, "group": "SMART ERRORS"}
        else:
            info["health"]["smart-tile-pmr"] = {"state": CRITICAL, "group": "SMART ERRORS"}

    if p["Media in Read-only"]["value"] == "No":
        info["health"]["smart-tile-readonly"] = {"state": GOOD, "group": "SMART ERRORS"}
    else:
        info["health"]["smart-tile-readonly"] = {"state": CRITICAL, "group": "SMART ERRORS"}

    if p["Volatile Memory Backup Failed"]["value"] == "No":
        info["health"]["smart-tile-volatile"] = {"state": GOOD, "group": "SMART ERRORS"}
    else:
        info["health"]["smart-tile-volatile"] = {"state": CRITICAL, "group": "SMART ERRORS"}

    if p["Media and Data Integrity Errors"]["value"] == "0":
        info["health"]["smart-tile-integrity"] = {"state": GOOD, "group": "SMART ERRORS"}
    else:
        info["health"]["smart-tile-integrity"] = {"state": CRITICAL, "group": "SMART ERRORS"}

    # OS and Capacity Tiles

    info["health"]["os-tile-timeouts"] = {"state": "Missing", "group": "OS ERRORS"}
    info["health"]["os-tile-disk"] = {"state": "Missing", "group": "OS ERRORS"}
    info["health"]["os-tile-pci"] = {"state": "Missing", "group": "OS ERRORS"}
    info["health"]["os-tile-root"] = {"state": "Missing", "group": "OS ERRORS"}

    info["health"]["cap-tile-total"] = {"state": "Missing", "group": "CAPACITY"}
    info["health"]["cap-tile-free"] = {"state": "Missing", "group": "CAPACITY"}
    info["health"]["cap-tile-used"] = {"state": "Missing", "group": "CAPACITY"}
