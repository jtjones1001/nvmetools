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
import copy
import csv
import datetime
import glob
import json
import os
import pathlib
import sys
import time
import traceback
import webbrowser

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

import numpy as np

import nvmetools.reports as pdf_reports
from nvmetools import RESOURCE_DIRECTORY, RESULTS_FILE, TEST_SUITE_DIRECTORY
from nvmetools.support.conversions import BYTES_IN_GB, KIB_TO_GB, MS_IN_SEC, as_float, as_int, as_io
from nvmetools.support.custom_reportlab import (
    FAIL_COLOR,
    FAIL_TABLE_TEXT_STYLE,
    HEADING_STYLE,
    Heading,
    LIMIT_COLOR,
    PASS_COLOR,
    SUBHEADING2_STYLE,
    SUBHEADING_STYLE,
    TABLE_ROW_GRAY_COLOR,
    TABLE_STYLE,
    TABLE_STYLE_NO_HEADER,
    TABLE_TEXT_STYLE,
    TEXT_STYLE,
    TestResult,
    TestTime,
    TitlePage,
    USABLE_WIDTH,
    convert_plot_to_image,
    save_reportlab_report,
)
from nvmetools.support.info import Info
from nvmetools.support.log import log

from reportlab.platypus import PageBreak, Paragraph, Table
from reportlab.platypus.tableofcontents import TableOfContents


SKIPPED = "SKIPPED"
PASSED = "PASSED"
FAILED = "FAILED"
ABORTED = "ABORTED"
STARTED = "STARTED"


class AbortedTestError(Exception):
    pass


class InfoReport:
    """Class to create PDF report file for NVMe information.

    This class uses the reportlab package to create a PDF file summarizing the information read from an
    NVMe device with the Info class.

    Example:
        Create a report object using an instance of the Info class and then save the report to a PDF file
        Note the Info class is defined in another module (info.py)::

            info = Info(nvme=0)   # refer to info.py module for details on this command

            report = InfoReport(info)
            report.save(filepath="./nvme_info.pdf")

    Attributes:
        filepath: Path to the PDF report file created.
    """

    __DEFAULT_REPORT_NAME = "readnvme.pdf"

    def __init__(self, info: Info):
        """Initialize the report but don't create the file.

        Args:
           info : The NVMe information to summarize in the PDF file.
        """
        self.filepath = os.path.join(".", InfoReport.__DEFAULT_REPORT_NAME)
        self._elements: list = []
        self._start_info = {"parameters": info.parameters, "full_parameters": info.full_parameters}

        self.add_info()

    def _get_value(self, parameter):
        """Get NVMe parameter from the ["nvme"]["parameters"] section."""
        if parameter in self._start_info["full_parameters"]:
            return self._start_info["full_parameters"][parameter]["value"]
        else:
            return " "

    def add_heading(self, text):
        """Add text in heading format with an underline.

        Args:
           text:  The text to add as a heading.
        """

        self._elements.append(Paragraph(f'<a name="{text}"/>' + text.upper(), style=HEADING_STYLE))
        self._elements.append(Heading(text))

    def add_info(self):
        """Add NVMe information summary table."""
        self.add_heading("NVMe Information")
        table_data = [
            ["VENDOR", "MODEL", "SIZE", "VERSION"],
            [
                self._get_value("Subsystem Vendor"),
                self._get_value("Model Number (MN)"),
                self._get_value("Size GB"),
                self._get_value("Version (VER)"),
            ],
        ]
        self.add_table(table_data, [100, 200, 100, 100])

        if self._get_value("Enable Host Memory (EHM)") == "Enabled":
            hmb_value = f"Enabled. Size = {self._get_value('Host Memory Buffer Size (HSIZE)')} pages"
        else:
            hmb_value = "Disabled"

        apst_value = (
            f"{self._get_value('Autonomous Power State Transition')} and "
            + f"{self._get_value('Autonomous Power State Transition Enable (APSTE)')}"
        )
        table_data = [
            ["PARAMETER", "VALUE"],
            ["Serial Number", self._get_value("Serial Number (SN)")],
            ["Number Of Namespaces", self._get_value("Number of Namespaces (NN)")],
            ["Namespace 1 EUI64", self._get_value("Namespace 1 IEEE Extended Unique Identifier (EUI64)")],
            ["Namespace 1 NGUID", self._get_value("Namespace 1 Globally Unique Identifier (NGUID)")],
            ["Namespace 1 Size", self._get_value("Namespace 1 Size")],
            ["Namespace 1 LBA Size", self._get_value("Namespace 1 Active LBA Size")],
            ["Firmware", self._get_value("Firmware Revision (FR)")],
            ["Firmware Slots", self._get_value("Firmware Slots")],
            ["Firmware Activation Without Reset", self._get_value("Firmware Activation Without Reset")],
            ["Host Memory Buffer", hmb_value],
            ["Autonomous Power State Transition", apst_value],
            ["Volatile Write Cache", self._get_value("Volatile Write Cache Enable (WCE)")],
            ["Host Throttle Threshold TMT1", self._get_value("Thermal Management Temperature 1 (TMT1)")],
            ["Host Throttle Threshold TMT2", self._get_value("Thermal Management Temperature 2 (TMT2)")],
            [
                "Drive Throttle Threshold WCTEMP",
                self._get_value("Warning Composite Temperature Threshold (WCTEMP)"),
            ],
            [
                "Drive Throttle Threshold CCTEMP",
                self._get_value("Critical Composite Temperature Threshold (CCTEMP)"),
            ],
        ]
        self.add_table(table_data, [250, 250])

        self.add_subheading("Power States")

        table_data = [["STATE", "NOP", "MAX POWER", "ENTRY LATENCY", "EXIT LATENCY"]]
        for index in range(int(self._get_value("Number of Power States Support (NPSS)"))):
            table_data.append(
                [
                    f"{index}",
                    self._get_value(f"Power State {index} Non-Operational State (NOPS)"),
                    self._get_value(f"Power State {index} Maximum Power (MP)"),
                    self._get_value(f"Power State {index} Entry Latency (ENLAT)"),
                    self._get_value(f"Power State {index} Exit Latency (EXLAT)"),
                ]
            )
        self.add_table(table_data, [60, 60, 100, 140, 140])

        self.add_subheading("PCIe")

        table_data = [
            ["PCI", "VENDOR", "VID", "DID", "WIDTH", "SPEED", "ADDRESS"],
            [
                "Endpoint",
                self._get_value("Subsystem Vendor"),
                self._get_value("PCI Vendor ID (VID)"),
                self._get_value("PCI Device ID"),
                self._get_value("PCI Width"),
                self._get_value("PCI Speed"),
                self._get_value("PCI Location"),
            ],
            [
                "Root",
                "",
                self._get_value("Root PCI Vendor ID"),
                self._get_value("Root PCI Device ID"),
                "",
                "",
                self._get_value("Root PCI Location"),
            ],
        ]
        self.add_table(table_data, [50, 90, 50, 50, 45, 75, 140])
        self.add_pagebreak()
        self.add_smart_attributes()

    def add_pagebreak(self):
        """Add a pagebreak."""
        self._elements.append(PageBreak())

    def add_paragraph(self, text):
        """Add paragraph of text in standard style.

        Args:
           text:  The text to add in paragraph style.
        """
        self._elements.append(Paragraph(text, style=TEXT_STYLE))

    def add_smart_attributes(self):
        """Add SMART attributes.

        Adds a table that includes the SMART attributes.  If start and end information exists then the
        table includes the attribute name, start value, end value, and delta values.  Otherwise the
        table includes the attribute name and value.
        """
        self.add_subheading("SMART Attributes")

        # if have start and end info then include both and their delta values

        if hasattr(self, "_end_info"):
            table_data = [["PARAMETER", "START", "END", "DELTA"]]
            for xcounter in self._end_info["compare"]["deltas"]:
                counter = self._end_info["compare"]["deltas"][xcounter]

                tmp = counter["delta"]
                if counter["delta"].split()[0] in ["0", "0.0"]:
                    tmp = ""

                table_data.append([counter["title"], counter["start"], counter["end"], tmp])
            self.add_table(table_data, [220, 100, 100, 80])
        else:
            table_data = [["PARAMETER", "VALUE"]]
            for parameter in self._start_info["full_parameters"]:
                if self._start_info["full_parameters"][parameter]["compare type"] == "counter":
                    table_data.append([parameter, self._get_value(parameter)])
            self.add_table(table_data, [300, 100])

    def add_subheading(self, text):
        """Add text in subheading format.

        Args:
           text:  The text to add as a subheading.
        """
        self._elements.append(Paragraph(text, style=SUBHEADING_STYLE))

    def add_subheading2(self, text):
        """Add text in subheading2 format.

        Args:
           text:  The text to add as a subheading2.
        """
        self._elements.append(Paragraph(text, style=SUBHEADING2_STYLE))

    def add_table(
        self,
        rows,
        widths,
        align="LEFT",
        start_row=0,
        bg_color=None,
        fail_fmt=False,
    ):
        """Add generic table.

        Args:
           rows:  First element is row 0, first element in row 0 is column 0 data.
           widths:  First element is column 0 width, next is column 1 width, etc.
           align:  String to align columns to left, center, or right
           start_row: If 0 then table has a header.
           bg_color: Background color for a row.
           fail_fmt:  Use fail formatting if True.
        """
        if len(rows) == 0:
            return

        # Create the table style based on header or not, fail formatting, and background color.

        if start_row == 0:
            table_style = copy.deepcopy(TABLE_STYLE)
            first_data_row = 1
        else:
            table_style = copy.deepcopy(TABLE_STYLE_NO_HEADER)
            first_data_row = 0

        for row_number, table_row in enumerate(rows):

            if row_number >= first_data_row and (row_number + start_row) % 2 == 0 and bg_color is None:
                table_style.add(
                    "BACKGROUND",
                    (0, row_number),
                    (-1, row_number),
                    TABLE_ROW_GRAY_COLOR,
                )
            elif bg_color == "GRAY":
                table_style.add(
                    "BACKGROUND",
                    (0, row_number),
                    (-1, row_number),
                    TABLE_ROW_GRAY_COLOR,
                )

            if row_number >= first_data_row and fail_fmt:
                if table_row[-1] == "PASS":
                    table_style.add("TEXTCOLOR", (-1, row_number), (-1, row_number), PASS_COLOR)
                elif table_row[-1] == "FAIL":
                    table_style.add("TEXTCOLOR", (-1, row_number), (-1, row_number), FAIL_COLOR)

                table_style.add("FONT", (-1, row_number), (-1, row_number), "Helvetica-Bold")

        table = Table(
            rows,
            colWidths=widths,
            style=table_style,
            hAlign=align,
            spaceBefore=12,
            spaceAfter=12,
        )
        self._elements.append(table)

    def save(self, filepath=None):
        """Save the report as a PDF file.

        Saves the report as a PDF file.

        Args:
           filepath: Optional path to the file to create.
        """
        if filepath is not None:
            self.filepath = filepath

        log.debug(f"Saving report: {filepath}")

        save_reportlab_report(self.filepath, self._elements, add_header_footer=False)


class NvmeReport(InfoReport):
    """Class to create PDF report file for NVMe test suite run."""

    _DEFAULT_REPORT_NAME = "report.pdf"
    _DEFAULT_TITLE = "NVMe Test Suite"
    _DEFAULT_DESCRIPTION = "Unknown test suite."
    _LABEL_X = -0.1

    def __init__(self, results_directory="", title="", description=""):
        """Class to create PDF report file for NVMe test suite results.

        Args:
           results_directory: Optional directory with results, if not provided uses latest results.
           title: Optional title for the report.
           description: Optional description for the report.

        This class uses the reportlab package to create a PDF file summarizing the test results from the
        NVMe health check.  The directory with the completed health check results must be provided.

        **Example**

        Create a report object using the results in the directory ./results/check_nvme and then save the report
        object to a PDF file.::

            report = NvmeReport(results_directory = "./results/check_nvme")
            report.save(filepath = "./results/check_nvme/health_summary.pdf")

        Attributes:
            filepath: Path to the PDF report file created.
        """

        # If no path given use the latest test run from the default directory

        if results_directory == "":
            list_of_files = glob.glob(f"{TEST_SUITE_DIRECTORY}/*")
            results_directory = max(list_of_files, key=os.path.getctime)
            if not os.path.isdir(results_directory):
                raise Exception(f"No Test Run results found at default path:{TEST_SUITE_DIRECTORY}")
        elif not os.path.isdir(results_directory):
            raise Exception(f"Results directory provided does not exist: {results_directory}")

        self.filepath = os.path.join(results_directory, self._DEFAULT_REPORT_NAME)

        # Setup vars

        if title == "":
            title = NvmeReport._DEFAULT_TITLE
        else:
            title = title + " Test Suite"
        if description == "":
            self.description = NvmeReport._DEFAULT_DESCRIPTION
        else:
            self.description = description

        log.debug(f" Creating PDF report at: {self.filepath}", indent=False)

        self._results_directory = results_directory
        self._elements = []
        self._testsuite_requirements = 0
        self._testsuite_pass = 0
        self._testsuite_fail = 0

        # Get the starting and ending info
        suite_results_file = os.path.join(results_directory, RESULTS_FILE)
        with open(suite_results_file, "r") as file_object:
            self.suite_results = json.load(file_object)

        if self.suite_results["result"] == ABORTED:
            raise Exception("Cannot create report when Test Suite was aborted")

        self.completed = self.suite_results["complete"]

        self._start_info = None

        if "start_info" in self.suite_results["data"]:
            self._start_info = self.suite_results["data"]["start_info"]
            self.drive_name = self.suite_results["data"]["start_info"]["parameters"]["Model"]

            if "end_info" in self.suite_results["data"]:
                self._end_info = self.suite_results["data"]["end_info"]
        else:
            raise Exception("Suite start information does not exist")

        # Read in the data from each test to get info needed for title and
        # summary pages then call custom flowable for title page and then build
        # summary page

        self._read_test_results()
        self._elements.append(TitlePage(self.drive_name, title, self.description, time.strftime("%B %d, %Y")))

        toc = TableOfContents()
        toc.levelStyles = [TEXT_STYLE]

        self.add_heading("Table of Contents")

        self._elements.append(toc)

        self._add_summary()

        # Display results for each test based on time they completed, first one
        # completed is displayed first and so on.  New tests must be added to
        # this for loop along with their matching function

        for time_key in self._start_times:
            test_data = self._all_results[time_key]  # for readability
            self._add_test_heading(test_data)
            self._get_test_report(test_data)

        # Add the appendices to the end of the report

        self._add_drive_parameters()
        self._add_references()

    def _add_bandwidth_plot(self, time_data, write_data, read_data, vlines=None, width=6.5, height=2.5):
        """Plot bandwidth from SMART attributes."""
        fig, ax = plt.subplots(figsize=(width, height))
        ax.set_xlabel("Time (Sec)")
        ax.set_ylabel("Bandwidth (GB/sec)")

        if vlines is not None:
            for line in vlines:
                plt.axvline(x=line, linewidth=1.25, color="#fd827e")

        if write_data is not None:
            ax.plot(time_data, write_data, label="Write BW", linewidth=2)
        if read_data is not None:
            ax.plot(time_data, read_data, label="Read BW", linewidth=2)

        ax.get_yaxis().set_label_coords(self._LABEL_X, 0.5)
        plt.legend(bbox_to_anchor=(1.05, 0.5), loc="center left")
        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

    def _add_bandwidth_plot2(
        self,
        time_data,
        write_data,
        read_data,
        time2_data,
        write2_data,
        read2_data,
        vlines=None,
        width=6.5,
        height=2.5,
    ):
        """Plot bandwidth from SMART attributes."""
        fig, ax = plt.subplots(figsize=(width, height))
        ax.set_xlabel("Time (Sec)")
        ax.set_ylabel("Bandwidth (GB/sec)")

        if vlines is not None:
            for line in vlines:
                plt.axvline(x=line, linewidth=1.25, color="#fd827e")

        if write_data is not None:
            ax.plot(time2_data, write2_data, label="Write BW", linewidth=2, color="#ff8f1e")
            ax.plot(time_data, write_data, label="Write BW (Full)", linewidth=1, color="#0f67a4")

        if read_data is not None:
            ax.plot(time2_data, read2_data, label="Read BW", linewidth=2, color="#ff8f1e")
            ax.plot(time_data, read_data, label="Read BW (Full)", linewidth=1, color="#0f67a4")

        ax.get_yaxis().set_label_coords(self._LABEL_X, 0.5)
        plt.legend(bbox_to_anchor=(1.05, 0.5), loc="center left")
        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

    def _add_debug_summary(self):
        review_file = os.path.join(self._results_directory, "review.txt")
        self.add_paragraph("")
        if os.path.exists(review_file):
            with open(review_file, "r") as file_object:
                review_text = file_object.read()
                self.add_paragraph(review_text)
        else:
            self.add_paragraph('<font color="red">Manual review of test results has not been completed.</font>')
        self.add_pagebreak()

    def _add_drive_parameters(self):
        self.add_pagebreak()
        self.add_heading("NVMe Parameters")
        param_table = [["TITLE", "DESCRIPTION", "VALUE"]]
        for param in self._start_info["full_parameters"]:
            param_table.append(
                [
                    Paragraph(param),
                    Paragraph(self._start_info["full_parameters"][param]["description"]),
                    Paragraph(str(self._start_info["full_parameters"][param]["value"])),
                ]
            )
        self.add_table(param_table, [100, 300, 100])

    def _add_performance_summary(self):

        found_performance_results = False

        if len(glob.glob(os.path.join(self._results_directory, "*_short_burst_performance"))) == 1:
            test_dir = glob.glob(os.path.join(self._results_directory, "*_short_burst_performance"))[0]
            short_burst_test_file = os.path.join(test_dir, "result.json")
            found_performance_results = True
        else:
            short_burst_test_file = ""

        if len(glob.glob(os.path.join(self._results_directory, "*_short_burst_performance_full_drive"))) == 1:
            test_dir = glob.glob(os.path.join(self._results_directory, "*_short_burst_performance_full_drive"))[0]
            short_burst_full_test_file = os.path.join(test_dir, "result.json")
            found_performance_results = True
        else:
            short_burst_full_test_file = ""

        if len(glob.glob(os.path.join(self._results_directory, "*_long_burst_performance"))) == 1:
            test_dir = glob.glob(os.path.join(self._results_directory, "*_long_burst_performance"))[0]
            long_burst_test_file = os.path.join(test_dir, "result.json")
            found_performance_results = True
        else:
            long_burst_test_file = ""

        if len(glob.glob(os.path.join(self._results_directory, "*_long_burst_performance_full_drive"))) == 1:
            test_dir = glob.glob(os.path.join(self._results_directory, "*_long_burst_performance_full_drive"))[0]
            long_burst_full_test_file = os.path.join(test_dir, "result.json")
            found_performance_results = True
        else:
            long_burst_full_test_file = ""

        if found_performance_results:
            self.add_pagebreak()
            self.add_heading("Performance Summary")
            short_burst_seconds = 0

            # if short burst empty or full results then display the table

            if os.path.exists(short_burst_test_file) or os.path.exists(short_burst_full_test_file):

                if os.path.exists(short_burst_test_file):
                    with open(short_burst_test_file, "r") as file_object:
                        json_data = json.load(file_object)
                        short_burst_seconds = json_data["data"]["io runtime sec"]
                        data = json_data["data"]
                        empty_seq_write = f"{data['sequential write']['results']['32']['131072']['bw']:0.3f} GB/s"
                        empty_seq_read = f"{data['sequential read']['results']['32']['131072']['bw']:0.3f} GB/s"
                        empty_rnd32_write = f"{data['random write']['results']['32']['4096']['bw']:0.3f} GB/s"
                        empty_rnd32_read = f"{data['random read']['results']['32']['4096']['bw']:0.3f} GB/s"
                        empty_rnd1_write = f"{data['random write']['results']['1']['4096']['bw']:0.3f} GB/s"
                        empty_rnd1_read = f"{data['random read']['results']['1']['4096']['bw']:0.3f} GB/s"

                        short_empty_rr = as_float(empty_rnd1_read)
                        short_empty_sr = as_float(empty_seq_read)
                        short_empty_rw = as_float(empty_rnd1_write)
                        short_empty_sw = as_float(empty_seq_write)
                else:
                    empty_seq_write = "N/A"
                    empty_seq_read = "N/A"
                    empty_rnd1_write = "N/A"
                    empty_rnd1_read = "N/A"
                    empty_rnd32_write = "N/A"
                    empty_rnd32_read = "N/A"

                    short_empty_rr = 0
                    short_empty_sr = 0
                    short_empty_rw = 0
                    short_empty_sw = 0

                if os.path.exists(short_burst_full_test_file):
                    with open(short_burst_full_test_file, "r") as file_object:
                        json_data = json.load(file_object)
                        short_burst_seconds = json_data["data"]["io runtime sec"]
                        data = json_data["data"]
                        full_seq_write = f"{data['sequential write']['results']['32']['131072']['bw']:0.3f} GB/s"
                        full_seq_read = f"{data['sequential read']['results']['32']['131072']['bw']:0.3f} GB/s"
                        full_rnd32_write = f"{data['random write']['results']['32']['4096']['bw']:0.3f} GB/s"
                        full_rnd32_read = f"{data['random read']['results']['32']['4096']['bw']:0.3f} GB/s"
                        full_rnd1_write = f"{data['random write']['results']['1']['4096']['bw']:0.3f} GB/s"
                        full_rnd1_read = f"{data['random read']['results']['1']['4096']['bw']:0.3f} GB/s"

                        short_full_rr = as_float(full_rnd1_read)
                        short_full_sr = as_float(full_seq_read)
                        short_full_rw = as_float(full_rnd1_write)
                        short_full_sw = as_float(full_seq_write)

                else:
                    full_seq_write = "N/A"
                    full_seq_read = "N/A"
                    full_rnd1_write = "N/A"
                    full_rnd1_read = "N/A"
                    full_rnd32_write = "N/A"
                    full_rnd32_read = "N/A"

                    short_full_rr = 0
                    short_full_sr = 0
                    short_full_rw = 0
                    short_full_sw = 0

                self.add_subheading2(f"Short Burst Performance ({short_burst_seconds} seconds)")
                table_data = [
                    ["IO PATTERN", "EMPTY DRIVE", "DRIVE 90% FULL"],
                    ["Random Write, QD1, 4KiB", f"{empty_rnd1_write}", f"{full_rnd1_write}"],
                    ["Random Read, QD1, 4KiB", f"{empty_rnd1_read}", f"{full_rnd1_read}"],
                    ["Random Write, QD32, 4KiB", f"{empty_rnd32_write}", f"{full_rnd32_write}"],
                    ["Random Read, QD32, 4KiB", f"{empty_rnd32_read}", f"{full_rnd32_read}"],
                    ["Sequential Write, QD32, 128KiB", f"{empty_seq_write}", f"{full_seq_write}"],
                    ["Sequential Read, QD32, 128KiB", f"{empty_seq_read}", f"{full_seq_read}"],
                ]
                self.add_table(table_data, widths=[160, 120, 120])

            if os.path.exists(long_burst_test_file) or os.path.exists(long_burst_full_test_file):
                if os.path.exists(long_burst_test_file):
                    with open(long_burst_test_file, "r") as file_object:
                        json_data = json.load(file_object)
                        data = json_data["data"]
                        long_burst_minutes = data["io runtime sec"] / 60
                        empty_seq_write = (
                            f"{data['bursts']['Sequential Write, QD32, 128KiB']['bandwidth']:0.3f} GB/s"
                        )
                        empty_seq_read = (
                            f"{data['bursts']['Sequential Read, QD32, 128KiB']['bandwidth']:0.3f} GB/s"
                        )
                        empty_rnd1_write = f"{data['bursts']['Random Write, QD1, 4KiB']['bandwidth']:0.3f} GB/s"
                        empty_rnd1_read = f"{data['bursts']['Random Read, QD1, 4KiB']['bandwidth']:0.3f} GB/s"

                        long_empty_rr = as_float(empty_rnd1_read)
                        long_empty_sr = as_float(empty_seq_read)
                        long_empty_rw = as_float(empty_rnd1_write)
                        long_empty_sw = as_float(empty_seq_write)
                else:
                    empty_seq_write = "N/A"
                    empty_seq_read = "N/A"
                    empty_rnd1_write = "N/A"
                    empty_rnd1_read = "N/A"

                    long_empty_rr = 0
                    long_empty_sr = 0
                    long_empty_rw = 0
                    long_empty_sw = 0

                if os.path.exists(long_burst_full_test_file):
                    with open(long_burst_full_test_file, "r") as file_object:
                        json_data = json.load(file_object)
                        data = json_data["data"]
                        long_burst_minutes = data["io runtime sec"] / 60
                        full_seq_write = (
                            f"{data['bursts']['Sequential Write, QD32, 128KiB']['bandwidth']:0.3f} GB/s"
                        )
                        full_seq_read = f"{data['bursts']['Sequential Read, QD32, 128KiB']['bandwidth']:0.3f} GB/s"
                        full_rnd1_write = f"{data['bursts']['Random Write, QD1, 4KiB']['bandwidth']:0.3f} GB/s"
                        full_rnd1_read = f"{data['bursts']['Random Read, QD1, 4KiB']['bandwidth']:0.3f} GB/s"

                        long_full_rr = as_float(full_rnd1_read)
                        long_full_sr = as_float(full_seq_read)
                        long_full_rw = as_float(full_rnd1_write)
                        long_full_sw = as_float(full_seq_write)
                else:
                    full_seq_write = "N/A"
                    full_seq_read = "N/A"
                    full_rnd1_write = "N/A"
                    full_rnd1_read = "N/A"

                    long_full_rr = 0
                    long_full_sr = 0
                    long_full_rw = 0
                    long_full_sw = 0

                table_data = [
                    ["IO PATTERN", "EMPTY DRIVE", "DRIVE 90% FULL"],
                    ["Random Write, QD1, 4KiB", f"{empty_rnd1_write}", f"{full_rnd1_write}"],
                    ["Random Read, QD1, 4KiB", f"{empty_rnd1_read}", f"{full_rnd1_read}"],
                    ["Sequential Write, QD32, 128KiB", f"{empty_seq_write}", f"{full_seq_write}"],
                    ["Sequential Read, QD32, 128KiB", f"{empty_seq_read}", f"{full_seq_read}"],
                ]
                self.add_subheading2(f"Long Burst Performance ({long_burst_minutes} minutes)")
                self.add_table(table_data, widths=[160, 120, 120])

                # add the bar charts

                self.add_paragraph("<br/><br/>")
                self.add_subheading2("Random Reads, QD1, 4KiB")
                self.add_performance_bar_charts([short_empty_rr, long_empty_rr], [short_full_rr, long_full_rr])

                self.add_paragraph("<br/><br/>")
                self.add_subheading2("Random Writes, QD1, 4KiB")
                self.add_performance_bar_charts([short_empty_rw, long_empty_rw], [short_full_rw, long_full_rw])

                self.add_pagebreak()
                self.add_subheading2("Sequential Reads, QD32, 128KiB")
                self.add_performance_bar_charts([short_empty_sr, long_empty_sr], [short_full_sr, long_full_sr])
                self.add_paragraph("<br/><br/>")

                self.add_subheading2("Sequential Writes, QD32, 128KiB")
                self.add_performance_bar_charts([short_empty_sw, long_empty_sw], [short_full_sw, long_full_sw])

    def _add_references(self):
        self.add_pagebreak()
        self.add_heading("References")
        self.add_paragraph(
            """
                1.  NVMe Specification, https://nvmexpress.org/developers/nvme-specification/
                <br/><br/>

                2.  fio, https://fio.readthedocs.io/en/latest/index.html
                <br/><br/>

                3.  nvmecmd,  https://www.epicutils.com
                <br/><br/>

                4.  Read and compare NVMe information with nvmecmd
                <br/><br/>

                5.  Analyze temperature and bandwidth plots with nvmecmd
                <br/><br/>

                6.  Analyze power state timing with latency plots and nvmecmd
                <br/><br/>

                7.  Update firmware with nvmecmd
                <br/><br/>

                8.  Measure IO performance with fio and nvmecmd
                <br/><br/>

                9.  Analyze idle latency plots with fio
                <br/><br/>

                10. What SMART Stats Tell Us About Hard Drives, Backblaze blog,<br/>
                 https://www.backblaze.com/blog/what-smart-stats-indicate-hard-drive-failures/
                <br/><br/>
                """
        )

    def _add_requirement_summary(self):
        self.add_subheading("Requirement Verification Summary")
        self.add_paragraph("""The table below lists the results for each attempt to verify a requirement.""")
        req_table = [["REQUIREMENT", "PASS", "FAIL"]]
        for req in sorted(self._requirements):
            pstyle = TABLE_TEXT_STYLE if self._requirements[req]["FAIL"] == 0 else FAIL_TABLE_TEXT_STYLE
            req_table.append(
                [
                    Paragraph(self._requirements[req]["title"], pstyle),
                    Paragraph(str(self._requirements[req]["PASS"]), pstyle),
                    Paragraph(str(self._requirements[req]["FAIL"]), pstyle),
                ]
            )
        self.add_table(req_table, [380, 60, 60])

    def _add_requirement_table(self, test_data):
        if test_data["result"] == SKIPPED or test_data["result"] == ABORTED:
            return

        table_data = [["REQUIREMENT", "RESULT"]]
        for requirement in sorted(test_data["rqmts"]):
            name = requirement
            if test_data["rqmts"][requirement]["fail"] == 0:
                result = "PASS"
            else:
                result = "FAIL"
            table_data.append([Paragraph(f"{name}", style=TABLE_TEXT_STYLE), result])
        self.add_table(table_data, [USABLE_WIDTH - 60, 60], fail_fmt=True)

    def _add_verification_table(self, test_data):

        if test_data["result"] == SKIPPED or test_data["result"] == ABORTED:
            return

        for index, step in enumerate(test_data["steps"]):

            if step["result"] == PASSED:
                self.add_subheading2(f"Step {index+1}: {step['title']}  :  <font color=\"green\">PASS</font>")
            else:
                self.add_subheading2(f"Step {index+1}: {step['title']}  :  <font color=\"red\">FAIL</font>")

            self.add_paragraph(step["description"])

            if len(step["verifications"]) > 0:
                table_data = [["REQUIREMENT", "VALUE", "RESULT"]]
                for verification in step["verifications"]:

                    name = verification["title"]
                    value = verification["value"]
                    _result = verification["result"]
                    if _result == PASSED:
                        result = "PASS"
                    else:
                        result = "FAIL"

                    table_data.append([Paragraph(f"{name}", style=TABLE_TEXT_STYLE), value, result])
                self.add_table(table_data, [USABLE_WIDTH - 175, 75, 50], fail_fmt=True)

    def _add_summary(self):
        self.add_pagebreak()
        self.add_heading("Summary")
        self.add_paragraph(f"""{self.overview}""")

        if not self.completed:
            self.add_paragraph(
                """<font color="red">The Test Suite did not complete, review the logs for details.</font>"""
            )
        self.add_paragraph("")

        self._elements.append(TestTime(self.suite_results))
        self.add_paragraph("<br/>")

        self._elements.append(TestResult(self.suite_results, data_type="tests"))

        self.add_paragraph(
            f"""<br/>A total of {self.suite_results['summary']['tests']['total']} tests completed
            {self.suite_results['summary']['verifications']['total']} verifications for
            {self.suite_results['summary']['rqmts']['total']} unique requirements."""
        )
        self._elements.append(TestResult(self.suite_results, data_type="requirements"))
        self._elements.append(TestResult(self.suite_results))

        self._add_debug_summary()

        self.add_subheading("Test Summary")
        table_data = [["TEST", "RESULT"]]
        table_row_start = 0

        for index, time_key in enumerate(self._start_times):

            test_data = self._all_results[time_key]  # for readability

            if test_data["result"] == PASSED:
                table_data.append([test_data["title"], "PASS"])
            elif test_data["result"] == SKIPPED:
                table_data.append([test_data["title"], "SKIP"])
            else:
                table_data.append([test_data["title"], "FAIL"])

                if len(test_data["rqmts"]) > 0:
                    self.add_table(table_data, [450, 50], start_row=table_row_start, fail_fmt=True)
                    table_row_start = index + 2
                    if index % 2 == 0:
                        bg = "WHITE"
                    else:
                        bg = "GRAY"
                    # if len(test_data["rqmts"]) > 0:
                    table_data = []

                    for req in test_data["rqmts"]:
                        if test_data["rqmts"][req]["fail"] != 0:
                            table_data.append([Paragraph(f"RQMT: {req}", TABLE_TEXT_STYLE), "FAIL"])

                    self.add_table(table_data, [350, 50], align="CENTER", start_row=1, bg_color=bg, fail_fmt=True)

                    table_data = []

        if len(table_data) != 0:
            self.add_table(table_data, [450, 50], start_row=table_row_start, fail_fmt=True)

        self._add_requirement_summary()

        self.add_pagebreak()
        self.add_info()
        self.add_paragraph("<br/><br/>")
        self.add_heading("System Information")
        self._add_system_info()
        self._add_performance_summary()

    def _add_system_info(self):
        if "system" in self._start_info["metadata"]:
            system = self._start_info["metadata"]["system"]
            table_data = [
                ["PARAMETER", "VALUE"],
                ["Supplier", system["manufacturer"]],
                ["Model", system["model"]],
                ["BIOS", system["bios version"]],
                ["Hostname", system["hostname"]],
                ["OS", system["os"]],
            ]
            self.add_table(table_data, [200, 200])

    def _add_test_heading(self, test_data):
        """Add text in test heading format."""
        self.add_pagebreak()
        self.add_heading(f"Test {test_data['number']}: {test_data['title']}")
        self._elements.append(TestResult(test_data))
        self._elements.append(TestTime(test_data))

    def _get_info_attributes(self, data_dir):
        """Get attributes from csv file."""
        time_data = []
        temp_data = []
        read_data = []
        write_data = []

        with open(os.path.join(data_dir, "nvme_attributes.csv"), newline="") as file_object:
            rows = csv.reader(file_object)
            next(rows)
            for row in rows:
                time_data.append(float(row[0]))
                temp_data.append(int(row[1]))
                write_data.append(float(row[4]))
                read_data.append(float(row[5]))
        return time_data, temp_data, write_data, read_data

    def _get_test_report(self, test_data):
        func_name = test_data["title"].replace(" ", "_").lower()

        start_exceptions = traceback.format_exception(*sys.exc_info())

        function_call = getattr(pdf_reports, func_name, None)

        if function_call is not None:

            try:
                function_call.report(self, test_data)

            except AbortedTestError:
                self.add_paragraph(
                    """<font color="red">Test was aborted and did not complete, refer to the test
                    logs for error details.</font>"""
                )
            except Exception:
                log.error("\n ----> PDF report module failed with an exception:\n")

                end_exceptions = traceback.format_exception(*sys.exc_info())

                display_line = False
                error_lines = ""
                for line in end_exceptions[len(start_exceptions) :]:
                    if "in _get_test_report" in line:
                        display_line = True
                    elif display_line:
                        for xline in line.split("\n"):
                            log.error("        " + xline)
                            error_lines += f"{xline} <br/<br/>"

                self.add_paragraph(
                    f"""<font color="red">
                    A fatal error occurred creating the report for this test.  Details:
                    <br/<br/><br/>

                    {error_lines}
                    </font>"""
                )
        else:
            self.add_description("This test has no pdf report module.")
            self.add_verifications(test_data)

    def _read_test_results(self):
        """Read individual test results."""

        if self._start_info is None:
            raise Exception("Could not find baseline device data")

        testrun_name = pathlib.Path(self._results_directory).name
        list_of_results = glob.glob(f"{self._results_directory}/*/{RESULTS_FILE}")

        log.debug("\n")
        log.debug(f"Testrun Name :    {testrun_name}")
        log.debug(f"Testrun location: {self._results_directory}")
        log.debug(f"Test Results      {len(list_of_results)}")
        log.debug("\n")

        self._start_times = []
        self._all_results = {}
        self._requirements = {}

        # for each test read in the results
        for result_file in list_of_results:
            try:
                with open(result_file, "r") as file_object:
                    json_info = json.load(file_object)

                for requirement in json_info["rqmts"]:
                    if requirement not in self._requirements:
                        self._requirements[requirement] = {
                            "PASS": json_info["rqmts"][requirement]["pass"],
                            "FAIL": json_info["rqmts"][requirement]["fail"],
                            "title": requirement,
                        }
                    else:
                        self._requirements[requirement]["PASS"] += json_info["rqmts"][requirement]["pass"]
                        self._requirements[requirement]["FAIL"] += json_info["rqmts"][requirement]["fail"]

                self._all_results[json_info["start time"]] = json_info
                self._start_times.append(json_info["start time"])

            except Exception:
                raise Exception(f"Could not open result file {result_file}")

        self._testsuite_requirements = len(self._requirements)
        for req in self._requirements:
            if self._requirements[req]["FAIL"] != 0:
                self._testsuite_fail += 1
            elif self._requirements[req]["PASS"] != 0:
                self._testsuite_pass += 1

        self._start_times.sort()
        self.testrun_end = self._all_results[self._start_times[-1]]["end time"]

        tmp_start = datetime.datetime.strptime(
            self._all_results[self._start_times[0]]["start time"], "%Y-%m-%d %H:%M:%S.%f"
        )
        tmp_end = datetime.datetime.strptime(
            self._all_results[self._start_times[-1]]["end time"], "%Y-%m-%d %H:%M:%S.%f"
        )
        delta = tmp_end - tmp_start
        self._testsuite_start = datetime.datetime.strftime(tmp_start, "%b %d, %Y - %H:%M:%S.%f")[0:-3]
        self._testsuite_end = datetime.datetime.strftime(tmp_end, "%b %d, %Y - %H:%M:%S.%f")[0:-3]
        self._testsuite_duration = str(delta)[0:-3]

        self.model = self._start_info["parameters"]["Model No Spaces"]

        drive_script = None

        if drive_script is None:
            self.specification = None
        else:
            self.specification = drive_script.DRIVE_SPECIFICATION

        if self.description == "":
            self.description = f"Report for {testrun_name} Test of above NVMe installed \
                in {self._start_info['metadata']['system']['manufacturer']} model \
                {self._start_info['metadata']['system']['model']}."

            self.overview = self.description + "."
        else:
            self.overview = self.description
            self.overview += f"  The NVMe tested was the {self.drive_name} with firmware \
                {self._start_info['parameters']['Firmware Revision (FR)']}.  The device was installed in a \
                {self._start_info['metadata']['system']['manufacturer']} system, model \
                {self._start_info['metadata']['system']['model']} running \
                {self._start_info['metadata']['system']['os']}."

    def _smooth(self, data, weight):
        # Based on an idea posted here:
        #    https://stackoverflow.com/questions/5283649/plot-smooth-line-with-pyplot

        last = data[0]
        smoothed = list()
        for point in data:
            smoothed_val = last * weight + (1 - weight) * point
            smoothed.append(smoothed_val)
            last = smoothed_val

        return smoothed

    def add_admin_bar_chart(self, labels, values):
        """Plot bar graphs for admin commands."""
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(False)
        y_position = [i for i, _ in enumerate(labels)]
        plt.barh(y_position, values)
        plt.yticks(y_position, labels)
        plt.xlabel("Latency (mS)")
        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

    def add_bandwidth_plot(self, data_dir, ref_dir=None, read=True, write=True, width=6.5, height=2.5):
        """Plot BW vs time from temp_bw.csv."""
        times, temps, writes, reads = self._get_info_attributes(data_dir)

        if ref_dir is not None:
            times2, temps2, writes2, reads2 = self._get_info_attributes(ref_dir)
            if not read:
                reads = None
                reads2 = None
            if not write:
                writes = None
                writes2 = None
            self._add_bandwidth_plot2(
                times, writes, reads, times2, writes2, reads2, vlines=None, width=width, height=height
            )

        else:
            if not read:
                reads = None
            if not write:
                writes = None
            self._add_bandwidth_plot(times, writes, reads, vlines=None, width=width, height=height)

    def add_bigfile_read_plot(self, data_dir, file_size=None, height=2):
        """Plot bandwidth for cont reads including file markers"""
        time_data = []
        read_data = []
        vlines = []
        file_read_data = 0

        with open(os.path.join(data_dir, "nvme_attributes.csv"), newline="") as file_object:
            rows = csv.reader(file_object)
            next(rows)
            for row in rows:
                time_data.append(float(row[0]))
                read_data.append(float(row[5]))

                if file_size is not None:
                    if file_read_data == 0 and float(row[5]) != 0:
                        vlines.append(float(row[0]))

                    file_read_data += float(row[5])

                    if file_read_data > file_size / BYTES_IN_GB:
                        file_read_data = 0

        if file_size is None:
            self._add_bandwidth_plot(time_data, None, read_data, height=height)
        else:
            self._add_bandwidth_plot(time_data, None, read_data, vlines=vlines, height=height)

    def add_bigfile_write_plot(self, data_dir, file_size=None, offset=0, height=2):
        """Plot bandwidth for cont writes including file markers"""
        time_data = []
        write_data = []
        vlines = []
        if file_size is None:
            file_write_data = 0
        else:
            file_write_data = file_size * offset / BYTES_IN_GB

        with open(os.path.join(data_dir, "nvme_attributes.csv"), newline="") as file_object:
            rows = csv.reader(file_object)
            next(rows)
            for row in rows:
                time_data.append(float(row[0]))
                write_data.append(float(row[4]))

                if file_size is not None:

                    if file_write_data == 0 and float(row[4]) != 0:
                        vlines.append(float(row[0]))

                    file_write_data += float(row[4])

                    if file_write_data > file_size / BYTES_IN_GB:
                        file_write_data = 0

        if file_size is None:
            self._add_bandwidth_plot(time_data, write_data, None, height=height)
        else:
            self._add_bandwidth_plot(time_data, write_data, None, vlines=vlines, height=height)

    def add_bigfile_bar_chart(self, labels, values):
        """Plot bar graphs for IO bursts commands."""
        fig, ax = plt.subplots(figsize=(6, 1.5))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(False)
        y_position = [i for i, _ in enumerate(labels)]
        bars = plt.barh(y_position, values)
        ax.bar_label(bars, padding=2, fmt="%.3f")
        plt.yticks(y_position, labels)
        plt.xlabel("Bandwidth (GB/s)")
        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

    def add_bigfile_bandwidth_plot(self, fio_bw_log, time_limit=None, width=6.5, height=2):
        """Plot bandwidth from fio bandwidth logfile."""
        time_data = []
        bw_data = []
        cum_data = []
        total_data = 0
        total_time = 0

        with open(fio_bw_log, newline="") as file_object:
            rows = csv.reader(file_object)
            for row in rows:
                row_time = int(row[0]) / MS_IN_SEC
                if time_limit and row_time > time_limit:
                    break

                time_data.append(row_time)
                bw_data.append(int(row[1]) * KIB_TO_GB)

                sample_time = (int(row[0]) - total_time) / MS_IN_SEC
                sample_data = int(row[1]) * KIB_TO_GB * sample_time
                total_data += sample_data
                total_time += sample_time

                cum_data.append(total_data)

        fig, ax = plt.subplots(figsize=(6, 2))

        ax.ticklabel_format(style="plain", axis="y")
        ax.set_xlabel("Time (Sec)")
        ax.set_ylabel("Bandwidth (GB/s)")

        ax.plot(time_data, bw_data)

        ax.get_yaxis().set_label_coords(self._LABEL_X, 0.5)

        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

        fig, ax = plt.subplots(figsize=(6, 2))
        ax.ticklabel_format(style="plain", axis="y")
        ax.set_xlabel("Time (Sec)")
        ax.set_ylabel("Data Written (GB)")
        ax.plot(time_data, cum_data)
        ax.get_yaxis().set_label_coords(self._LABEL_X, 0.5)
        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

    def get_bigfile_bandwidth_info(self, fio_bw_log, start=0, end=1e9):
        """Plot bandwidth from fio bandwidth logfile."""
        file_data = 0
        file_time = 0

        cache_data = 0
        cache_time = 0

        total_data = 0
        total_time = 0

        with open(fio_bw_log, newline="") as file_object:
            rows = csv.reader(file_object)
            for row in rows:

                sample_time = int(row[0]) / MS_IN_SEC - total_time
                sample_data = int(row[1]) * KIB_TO_GB * sample_time
                total_data += sample_data
                total_time += sample_time

                if total_data >= start and total_data < end:
                    file_data += sample_data
                    file_time += sample_time

            average_bandwidth = file_data / file_time
            cache_limit = average_bandwidth * 2

            for row in rows:

                sample_time = int(row[0]) / MS_IN_SEC - total_time
                sample_data = int(row[1]) * KIB_TO_GB * sample_time
                total_data += sample_data
                total_time += sample_time

                if total_data >= start and total_data < end:
                    if int(row[1]) * KIB_TO_GB > cache_limit:
                        cache_data += sample_data
                        cache_time += sample_time

            average_cache_bandwidth = cache_data / cache_time

        return (average_bandwidth, average_cache_bandwidth, file_data, cache_data)

    def add_description(self, text):
        self.add_subheading("DESCRIPTION")
        self.add_paragraph(text)

    def add_diagnostic_progress_plot(self, time, progress, time_io=None, progress_with_io=None):
        """Add progress plot for diagnostic test.

        Adds plot of self-test progress from the diagnostic test to the report.   The plot includes
        self-test progress run standalone and concurrent with IO.

        TODO: This should be single plot and testnvme should override with 2 plots
        """
        fig, ax = plt.subplots(figsize=(6, 2))

        ax.set_xlabel("Time (Minutes)")
        ax.set_ylabel("Progress (%)")
        ax.get_yaxis().set_label_coords(-0.075, 0.5)
        ax.plot(time, progress, label="Standalone", linewidth=2)
        if progress_with_io is not None:
            ax.plot(time_io, progress_with_io, label="Concurrent", linewidth=1)
            plt.legend(bbox_to_anchor=(1.05, 0.5), loc="center left")

        self._elements.append(convert_plot_to_image(fig, ax))

    def add_diagnostic_temperature_plot(self, time, temp, time_io=None, temp_with_io=None):
        """Add plot of temperature for diagnostic test."""
        fig, ax1 = plt.subplots(figsize=(6, 4))

        self.add_throttle_lines(plt)

        ax1.set_xlabel("Time (Minutes)")
        ax1.set_ylabel("Temperature (C)")
        ax1.get_yaxis().set_label_coords(-0.075, 0.5)

        if temp_with_io is not None:
            ax1.plot(time, temp, label="Standalone", linewidth=2)
            ax1.plot(time_io, temp_with_io, label="Concurrent", linewidth=1)
        else:
            ax1.plot(time, temp, linewidth=1)

        plt.legend(bbox_to_anchor=(1.05, 0.5), loc="center left")
        self._elements.append(convert_plot_to_image(fig, ax1))

    def add_fio_bandwidth_plot(self, fio_bw_log, time_limit=None, width=6.5, height=2.5):
        """Plot bandwidth from fio bandwidth logfile."""
        time_data = []
        bw_data = []
        with open(fio_bw_log, newline="") as file_object:
            rows = csv.reader(file_object)
            for row in rows:
                row_time = int(row[0]) / MS_IN_SEC
                if time_limit and row_time > time_limit:
                    break

                time_data.append(row_time)
                bw_data.append(int(row[1]) * KIB_TO_GB)

        self.add_plot(time_data, "Time (Sec)", bw_data, "Bandwidth (GB/s)", width=width, height=height)

    def add_histogram(self, cmd_times, log=False, xlabel="Latency (mS)"):
        """Histogram with test result."""
        fig, ax = plt.subplots(figsize=(6, 1.5))
        ax.ticklabel_format(style="plain", axis="y")

        ax.set_xlabel(xlabel)
        ax.set_ylabel("Count")
        ax.get_yaxis().set_label_coords(-0.125, 0.5)
        n, bins, patches = plt.hist(cmd_times, 150, log=log)
        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

    def add_idle_latency_plot(self, file, unit="mS"):
        """Plot read latency vs. idle time."""
        fig, ax = plt.subplots(figsize=(6.5, 2))
        ax.set_xlabel(f"Idle Time ({unit})")
        ax.set_ylabel("Latency (mS)")
        ax.get_yaxis().set_label_coords(self._LABEL_X, 0.5)

        time_data = []
        latency_data = []
        with open(file, newline="") as file_object:
            rows = csv.reader(file_object)
            for row in rows:
                time_data.append(int(row[0]))
                latency_data.append(float(row[1]))
        ax.plot(time_data, latency_data, linewidth=1, label="raw", color="#ff8f1e")
        ax.plot(time_data, self._smooth(latency_data, 0.8), linewidth=1.5, label="smooth", color="#0f67a4")

        plt.legend(bbox_to_anchor=(1.05, 0.5), loc="center left")
        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

    def add_latency_bar_charts(self, read0, read1, write0, write1):
        """Plot bar graphs for standalone/concurrent IO."""
        fig, ax = plt.subplots(figsize=(6, 1.5))

        stdalone_means = [read0, write0]
        concurrent_means = [read1, write1]
        labels = ["Read", "Write"]
        width = 0.3
        y_value = np.arange(len(labels))

        rects1 = ax.barh(y_value + width / 2, stdalone_means, width, label="Standalone")
        rects2 = ax.barh(y_value - width / 2, concurrent_means, width, label="Concurrent")

        plt.legend(bbox_to_anchor=(1.15, 0.5), loc="center left")
        plt.xlabel("Latency (mS)")

        ax.set_yticks(y_value, labels)
        ax.grid(False)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.bar_label(rects1, padding=2, fmt="%.3f")
        ax.bar_label(rects2, padding=2, fmt="%.3f")

        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

    def add_performance_bar_charts(self, empty, full):
        """Plot bar graphs for short/long term peformance."""
        fig, ax = plt.subplots(figsize=(6, 1.5))
        labels = ["Short", "Long"]
        width = 0.3
        y_value = np.arange(len(labels))

        rects1 = ax.barh(y_value + width / 2, empty, width, label="Empty Drive")
        rects2 = ax.barh(y_value - width / 2, full, width, label="Full Drive")

        plt.legend(bbox_to_anchor=(1.15, 0.5), loc="center left")
        plt.xlabel("Bandwidth (GB/s)")

        ax.set_yticks(y_value, labels)
        ax.grid(False)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.bar_label(rects1, padding=2, fmt="%.3f")
        ax.bar_label(rects2, padding=2, fmt="%.3f")

        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

    def _add_performance_row(self, name, data, iops=False):
        """Add row to report bandwidth or iops table."""
        io = as_io(name)

        if data["limits"] is None:
            limit = ""
        elif data["limits"][name] == 0:
            limit = ""
        else:
            number_limit = data["limits"][name]
            limit = f"{number_limit:0,.3f} GB/s"

        number_iops = data[io["pattern"]]["results"][io["depth"]][io["size"]]["bw"] * BYTES_IN_GB / int(io["size"])
        iops = f"{number_iops:0,.0f}"

        number_bandwidth = data[io["pattern"]]["results"][io["depth"]][io["size"]]["bw"]
        bandwidth = f"{number_bandwidth:0,.3f} GB/s"

        if number_bandwidth > number_limit:
            result = "PASS"
        else:
            result = "FAIL"

        return [name, iops, bandwidth, limit, result]

    def add_bandwidth_performance_table(self, test_result, random_qd32=True):

        table_data = [
            ["IO PATTERN", "IOPS", "BANDWIDTH", "LIMIT", "RESULT"],
            self._add_performance_row("Sequential Write, QD32, 128KiB", test_result["data"]),
            self._add_performance_row("Sequential Read, QD32, 128KiB", test_result["data"]),
            self._add_performance_row("Random Write, QD1, 4KiB", test_result["data"]),
            self._add_performance_row("Random Read, QD1, 4KiB", test_result["data"]),
        ]
        if random_qd32:
            table_data.append(self._add_performance_row("Random Write, QD32, 4KiB", test_result["data"]))
            table_data.append(self._add_performance_row("Random Read, QD32, 4KiB", test_result["data"]))

        self.add_table(table_data, widths=[160, 90, 80, 80, 70], fail_fmt=True)

    def add_plot(self, x_data, x_name, y_data, y_name, width=6.5, height=2.5, ymin=None, xmin=None, xticks=None):
        """Plot temperature and BW vs time from temp_bw.csv."""
        fig, ax = plt.subplots(figsize=(width, height))
        ax.ticklabel_format(style="plain", axis="y")
        ax.set_xlabel(x_name)
        ax.set_ylabel(y_name)
        ax.plot(x_data, y_data)
        if ymin is not None:
            ax.set_ylim(ymin=ymin)
        if xmin is not None:
            ax.set_xlim(xmin=xmin)

        ax.get_yaxis().set_label_coords(self._LABEL_X, 0.5)
        if xticks is not None:
            ax.xaxis.set_major_locator(ticker.FixedLocator(xticks))
        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

    def add_power_state_plot(self, file, timeouts, exit_latencies):
        """Plot BW vs time from temp_bw.csv."""
        fig, ax = plt.subplots(figsize=(6.5, 2))
        ax.set_xlabel("Idle Time (mS)")
        ax.set_ylabel("Latency (mS)")
        ax.get_yaxis().set_label_coords(self._LABEL_X, 0.5)
        linestyles = ["--", "-", ":", ":"]

        time_data = []
        latency_data = []

        with open(file, newline="") as file_object:
            rows = csv.reader(file_object)
            for row in rows:
                time_data.append(int(row[0]))
                latency_data.append(float(row[1]))

        for i, latency in enumerate(exit_latencies):
            plt.axhline(
                y=exit_latencies[latency],
                linewidth=1,
                color="#fd625e",
                linestyle=linestyles[i],
                label=latency,
            )
        for i, timeout in enumerate(timeouts):
            plt.axvline(
                x=timeouts[timeout],
                linewidth=1,
                color=mcolors.CSS4_COLORS["black"],
                linestyle=linestyles[i],
                label=timeout,
            )
        ax.plot(time_data, latency_data, linewidth=2, color="#0f67a4")
        plt.legend(bbox_to_anchor=(1.05, 0.5), loc="center left")

        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

    def add_results(self, result):
        self.add_subheading("RESULTS")

        data_directory = os.path.join(self._results_directory, result["directory name"])
        review_file = os.path.join(data_directory, "review.txt")
        if os.path.exists(review_file):
            with open(review_file, "r") as file_object:
                review_text = file_object.read()
                self.add_paragraph(review_text)

        if result["result"] == ABORTED:
            raise AbortedTestError

    def add_short_burst_plot(self, result):

        sizes = result["data"]["block sizes"]
        performance_data = result["data"]
        sizes_kib = []
        for bs in sizes:
            sizes_kib.append(int(bs / 1024))

        for io_pattern in ["random write", "random read", "sequential write", "sequential read"]:
            if io_pattern == "sequential write":
                self.add_pagebreak()
            fig, ax = plt.subplots(figsize=(6, 4))

            ax.set_xlabel("Block Size (KiB)")
            ax.set_ylabel("Bandwidth (GB/s)")
            ax.get_yaxis().set_label_coords(-0.1, 0.5)

            self.add_subheading2(f"{io_pattern.title()} Bandwidth")

            results = performance_data[io_pattern]["results"]
            for depth in results:
                bandwidth = []

                for bs in sizes:
                    bandwidth.append(results[depth][str(bs)]["bw"])

                ax.yaxis.set_major_formatter(plt.FormatStrFormatter("%.2f"))
                plt.xticks(ticks=range(len(sizes)), labels=sizes_kib)
                ax.plot(range(len(sizes)), bandwidth, label=f"QD{depth}")

            plt.legend(bbox_to_anchor=(1.05, 0.5), loc="center left")

            self._elements.append(convert_plot_to_image(fig, ax))
            plt.close("all")

    def add_temperature_plot(self, data_dir, ymin=20, width=6.5, height=2):
        """Plot temperature data with throttle limits shown."""
        times, temps, write, read = self._get_info_attributes(data_dir)
        fig, ax = plt.subplots(figsize=(width, height))

        self.add_throttle_lines(plt)

        ax.set_xlabel("Time (Sec)")
        ax.set_ylabel("Temperature (C)")
        ax.plot(times, temps)
        if ymin:
            ax.set_ylim(ymin=ymin)
        ax.get_yaxis().set_label_coords(self._LABEL_X, 0.5)
        plt.legend(bbox_to_anchor=(1.05, 0.5), loc="center left")
        self._elements.append(convert_plot_to_image(fig, ax))
        plt.close("all")

    def add_verifications(self, test_result):
        """Add test result summary for the test.

        Adds single line to report that indicates if the test failed any requirements.

        Args:
           test_result: Test results from json file.
        """
        self.add_subheading("VERIFICATIONS")
        self.add_paragraph("This section lists the test steps and requirement verifications.")
        self._add_verification_table(test_result)

    def add_throttle_lines(self, plt: plt):
        """Add thermal throttle lines to plot.

        Adds horizontal lines to a plot indicating the thermal throttle limits of CCTEMP, WCTEMP, TMT2,
        and TMT1.

        Args:
           plt: Plot to add the lines too.
        """
        value = self._get_value
        if value("Critical Composite Temperature Threshold (CCTEMP)") != "Not Reported":
            plt.axhline(
                y=as_int(value("Critical Composite Temperature Threshold (CCTEMP)")),
                linewidth=1,
                color=LIMIT_COLOR,
                linestyle="-",
                label="CCTEMP",
            )
        if value("Warning Composite Temperature Threshold (WCTEMP)") != "Not Reported":
            plt.axhline(
                y=as_int(value("Warning Composite Temperature Threshold (WCTEMP)")),
                linewidth=1.5,
                color=LIMIT_COLOR,
                linestyle="--",
                label="WCTEMP",
            )
        if value("Thermal Management Temperature 2 (TMT2)") != "Disabled":
            plt.axhline(
                y=as_int(value("Thermal Management Temperature 2 (TMT2)")),
                linewidth=1.5,
                color=LIMIT_COLOR,
                linestyle=(0, (3, 1, 1, 1, 1, 1)),
                label="TMT2",
            )
        if value("Thermal Management Temperature 1 (TMT1)") != "Disabled":
            plt.axhline(
                y=as_int(value("Thermal Management Temperature 1 (TMT1)")),
                linewidth=1.5,
                color=LIMIT_COLOR,
                linestyle=":",
                label="TMT1",
            )

    def save(self, filepath=None):
        """Save the report as a PDF file.

        Saves the report as a PDF file with a header and footer.

        Args:
           filepath: Optional path to the file to create.
        """
        if filepath is not None:
            self.filepath = filepath

        log.debug(f"Saving report: {filepath}")

        save_reportlab_report(self.filepath, self._elements, drive=self.drive_name, add_header_footer=True)


def create_dashboard(results_directory, show_dashboard=True):

    dashboard_file = os.path.join(results_directory, "dashboard.html")

    with open(os.path.join(RESOURCE_DIRECTORY, "html", "index.html"), "r") as file_object:
        lines = file_object.readlines()

        write_lines = []
        for line in lines:
            if line.find("./assets/data.js") != -1:
                json_result_file = os.path.join(results_directory, RESULTS_FILE)
                write_lines.append("<script>\n")

                view_filter_file = os.path.join(RESOURCE_DIRECTORY, "html", "assets", "filter.json")
                with open(view_filter_file, "r") as file_object:
                    filters = json.load(file_object)

                with open(json_result_file, "r") as file_object:
                    data = json.load(file_object)

                    metadata = data["data"]["start_info"]["metadata"]
                    start_parameters = data["data"]["start_info"]["full_parameters"]

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

                    mystring = f"const rqmtListData = {json.dumps(rqmts, sort_keys=False, indent=4)};\n\n"
                    mystring += f"const testListData = {json.dumps(data['tests'], sort_keys=False, indent=4)};\n\n"

                    for index, _ver in enumerate(data["verifications"]):
                        data["verifications"][index]["value"] = str(data["verifications"][index]["value"])

                    mystring += "const verificationListData = "
                    mystring += f"{json.dumps(data['verifications'], sort_keys=False, indent=4)};\n\n"
                    if "end_info" in data["data"]:
                        mystring += "const compareInfo = true;"
                    else:
                        mystring += "const compareInfo = null;"
                    mystring += "const compareSystemData = null;\n\n"
                    parameters = []
                    for name, value in start_parameters.items():

                        if "end_info" in data["data"]:
                            end_parameters = data["data"]["end_info"]["full_parameters"]

                            if end_parameters[name]["value"] == value["value"]:
                                change = ""
                            else:
                                change = end_parameters[name]["value"]

                        else:
                            change = "N/A"

                        parameters.append(
                            {
                                "name": value["name"],
                                "value": value["value"],
                                "change": change,
                                "description": value["description"],
                            }
                        )

                    mystring += (
                        f"const systemData = {json.dumps(metadata['system'], sort_keys=False, indent=4)};\n\n"
                    )

                    mystring += f"const parameters = {json.dumps(parameters, sort_keys=False, indent=4)};\n\n"
                    data.pop("data")
                    mystring += f"\n const info = {json.dumps(data, sort_keys=False, indent=4)};\n\n"

                    for filtername, filtervalues in filters.items():
                        matching_parameters = []
                        for parameter in parameters:
                            if parameter["name"] in filtervalues:
                                matching_parameters.append(parameter)

                        mystring += f"const {filtername} = "
                        mystring += f"{json.dumps(matching_parameters, sort_keys=False, indent=4)};\n\n"

                write_lines.extend(mystring.split("\n"))
                write_lines.append("</script>")
            elif line.find("./assets/dashboard.css") != -1:
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "assets", "dashboard.css")
                write_lines.append("<style>")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</style>")
            elif line.find("./assets/bootstrap.css") != -1:
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "assets", "bootstrap.css")
                write_lines.append("<style>")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</style>")
            elif line.find("./assets/bootstrap.bundle.min.js") != -1:
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "assets", "bootstrap.bundle.min.js")
                write_lines.append("<script>")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</script>")
            elif line.find("./assets/dashboard.js") != -1:
                write_lines.append("<script>")
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "assets", "dashboard.js")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</script>")

            elif line.find("./assets/chart.min.js") != -1:
                write_lines.append("<script>")
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "assets", "chart.min.js")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</script>")

            else:
                write_lines.append(line)

    with open(dashboard_file, "w") as file_object:
        file_object.writelines(write_lines)

    if show_dashboard:
        webbrowser.open(dashboard_file, new=2)

    log.info(f" Dashboard:    {dashboard_file}", indent=False)


def create_info_dashboard(directory, info_file, compare_info_file):

    dashboard_file = os.path.join(directory, "info.html")

    with open(info_file, "r") as file_object:
        info_data = json.load(file_object)
        metadata = info_data["_metadata"]
        parameters = info_data["nvme"]["parameters"]
        final_parameters = []
        for parameter in parameters:
            final_parameters.append(
                {
                    "name": parameters[parameter]["name"],
                    "value": parameters[parameter]["value"],
                    "change": None,
                    "description": parameters[parameter]["description"],
                }
            )

    if compare_info_file != "":
        with open(compare_info_file, "r") as file_object:
            compare_info_data = json.load(file_object)
            compare_metadata = compare_info_data["_metadata"]
            compare_parameters = compare_info_data["nvme"]["parameters"]

            final_parameters = []
            for parameter in parameters:
                if parameter in compare_parameters:
                    if compare_parameters[parameter]["value"] == parameters[parameter]["value"]:
                        change = ""
                    else:
                        change = compare_parameters[parameter]["value"]
                else:
                    change = "N/A"

                final_parameters.append(
                    {
                        "name": parameters[parameter]["name"],
                        "value": parameters[parameter]["value"],
                        "change": change,
                        "description": parameters[parameter]["description"],
                    }
                )

    with open(os.path.join(RESOURCE_DIRECTORY, "html", "index-info.html"), "r") as file_object:
        lines = file_object.readlines()

        write_lines = []
        for line in lines:
            if line.find("./assets/data.js") != -1:
                write_lines.append("<script>\n")
                view_filter_file = os.path.join(RESOURCE_DIRECTORY, "html", "assets", "filter.json")
                with open(view_filter_file, "r") as file_object:
                    filters = json.load(file_object)
                    mystring = (
                        f"const systemData = {json.dumps(metadata['system'], sort_keys=False, indent=4)};\n\n"
                    )
                    if compare_info_file != "":
                        mystring += f"const compareSystemData = {json.dumps(compare_metadata['system'], sort_keys=False, indent=4)};\n\n"
                        mystring += f"\n const compareInfo = {json.dumps(compare_info_data, sort_keys=False, indent=4)};\n\n"
                    else:
                        mystring += "const compareSystemData = null;\n\n"
                        mystring += "const compareInfo = null;\n\n"

                    mystring += (
                        f"const parameters = {json.dumps(final_parameters, sort_keys=False, indent=4)};\n\n"
                    )
                    mystring += f"\n const info = {json.dumps(info_data, sort_keys=False, indent=4)};\n\n"

                    for filtername, filtervalues in filters.items():
                        matching_parameters = []
                        for parameter in final_parameters:
                            if parameter["name"] in filtervalues:
                                matching_parameters.append(parameter)

                        mystring += f"const {filtername} = "
                        mystring += f"{json.dumps(matching_parameters, sort_keys=False, indent=4)};\n\n"

                write_lines.extend(mystring.split("\n"))
                write_lines.append("</script>")

            elif line.find("./assets/bootstrap.css") != -1:
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "assets", "bootstrap.css")
                write_lines.append("<style>")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</style>")
            elif line.find("./assets/dashboard.css") != -1:
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "assets", "dashboard.css")
                write_lines.append("<style>")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</style>")
            elif line.find("./assets/bootstrap.bundle.min.js") != -1:
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "assets", "bootstrap.bundle.min.js")
                write_lines.append("<script>")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</script>")

            elif line.find("./assets/chart.min.js") != -1:
                write_lines.append("<script>")
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "assets", "chart.min.js")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</script>")
            elif line.find("./assets/dashboard.js") != -1:
                write_lines.append("<script>")
                html_input = os.path.join(RESOURCE_DIRECTORY, "html", "assets", "dashboard.js")
                with open(html_input, "r") as file_object:
                    write_lines.extend(file_object.readlines())
                write_lines.append("</script>")
            else:
                write_lines.append(line)

    with open(dashboard_file, "w") as file_object:
        file_object.writelines(write_lines)

    webbrowser.open(dashboard_file, new=2)

    log.info(f" Dashboard:    {dashboard_file}", indent=False)


def create_reports(results_directory, title="N/A", description="N/A", show_dashboard=True):
    try:
        log.info(f" Logs:         {results_directory}", indent=False)
        pdf = NvmeReport(results_directory=results_directory, title=title, description=description)
        pdf.save()
        create_dashboard(results_directory, show_dashboard)
        log.info(f" Report:       {os.path.join(results_directory,'report.pdf')}", indent=False)

    except Exception:
        log.exception("\n  Error creating reports:\n\n")


def _encode_png_icon(icon_file):
    """Function to encode image for inclusion in standalone html file."""
    with open(icon_file, "rb") as binary_file:
        binary_file_data = binary_file.read()
        base64_encoded_data = base64.b64encode(binary_file_data)
        base64_message = base64_encoded_data.decode("utf-8")
        print(base64_message)
