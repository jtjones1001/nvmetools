# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Console command that displays NVMe drive information in html format.

Reads NVMe drive information using the Admin Commands: Get Log Page, Get Feature, Identify
Controller, and Identify Namespace. A few parameters, such as PCIe location and link info, are read
from the OS.

**Command Line Parameters**
    --nvme, -n      Integer NVMe device number, can be found using listnvme.
    --info, -i      Optional file to read information from (instead of from device)
    --compare, -c   Optional file that contain information to compare against

The following log files are saved to the working directory under viewnvme:

    - readnvme.log contains the console output
    - nvme.info.json contains the NVMe parameters in json format
    - info.html is a html format report
    - nvmecmd.trace.log and trace.log are trace file for debug if something goes wrong
    - read.summary.json contains information on the Admin commands used

**Example**

    This example reads the information of NVMe 0

    .. highlight:: none
    .. code-block:: python

        viewnvme  --nvme 0

   * `Example info.html <https://htmlpreview.github.io/?https://raw.githubusercontent.com/jtjones1001/nvmetools/main/docs/examples/viewnvme/info.html>`_

"""  # noqa: E501
import argparse
import logging
import os
import sys

from nvmetools.support.console import exit_on_exception
from nvmetools.support.info import Info
from nvmetools.support.log import start_logger
from nvmetools.support.report import create_info_dashboard


def _parse_arguments():
    """Parse input arguments from command line."""
    parser = argparse.ArgumentParser(
        description=read_nvme.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-n", "--nvme", type=int, default=0, help="NVMe drive to read", metavar="#")
    parser.add_argument("-i", "--info", default="", help="File with NVMe info")
    parser.add_argument("-c", "--compare", default="", help="File with NVMe info to compare")

    return vars(parser.parse_args())


def read_nvme(nvme=0, info="", compare=""):
    """Display and log NVMe information.

    Reads NVMe information using the nvmecmd utility. This utility creates a file named nvme.info.json
    with the entire set of information. This script reads nvme.info.json and displays the NVMe
    information as an html dashboard (info.html).
    """
    try:
        directory = os.path.join(os.path.abspath("."), "viewnvme")
        os.makedirs(directory, exist_ok=True)
        start_logger(directory, logging.INFO, "viewnvme.log")
        if info == "":
            Info(nvme=nvme, directory=directory)
            info = os.path.join(directory, "nvme.info.json")

        create_info_dashboard(directory, info, compare)
        sys.exit()

    except Exception as e:
        exit_on_exception(e)


def main():
    """Allow command line operation with unique arguments."""
    args = _parse_arguments()
    read_nvme(**args)


if __name__ == "__main__":
    main()
