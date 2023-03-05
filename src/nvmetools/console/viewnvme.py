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

The following log files are saved to the working directory under viewnvme:

    - viewnvme.log contains the console output
    - viewnvme.html is a html format report

    And for each NVMe read there is a folder with:

    - nvme.info.json contains the NVMe parameters in json format
    - nvmecmd.trace.log and trace.log are trace file for debug if something goes wrong
    - read.summary.json contains information on the Admin commands used

**Example**

    This example reads the information of NVMe 0

    .. highlight:: none
    .. code-block:: python

        viewnvme  --nvme 0

   * `Example viewnvme.html <https://htmlpreview.github.io/?https://raw.githubusercontent.com/jtjones1001/nvmetools/main/docs/examples/viewnvme/viewnvme.html>`_

"""  # noqa: E501
import argparse
import logging
import os
import shutil
import sys

import nvmetools.support.console as console
from nvmetools.support.info import Info
from nvmetools.support.log import start_logger
from nvmetools.support.report import create_dashboard


def _parse_arguments():
    """Parse input arguments from command line."""
    parser = argparse.ArgumentParser(
        description=read_nvme.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-n", "--nvme", type=int, help="NVMe to read, reads all if not specified", metavar="#")
    parser.add_argument("-f", "--file", default="", help="Read NVMe info from this file")
    '''
        Disable this argument for now
        parser.add_argument("-c", "--comparefile", default="", help="Compare info against NVMe info in this file")
    '''
    return vars(parser.parse_args())


def read_nvme(nvme=None, file="", comparefile=""):
    """Display and log NVMe information.

    Reads NVMe information using the nvmecmd utility. This utility creates a file named nvme.info.json
    with the entire set of information. This script reads nvme.info.json and displays the NVMe
    information as an html dashboard (viewnvme.html).
    """
    try:
        directory = os.path.join(os.path.abspath("."), "viewnvme")

        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=False)

        log = start_logger(directory, logging.INFO, "viewnvme.log", False)

        log.info(f" Logs: {directory}", indent=False)
        all_nvme_info = {}
        start_nvme = None

        if file == "":
            if nvme is None:
                base_info = Info(nvme="*", directory=directory)
                os.remove(os.path.join(directory, "nvme.info.json"))
                os.remove(os.path.join(directory, "read.summary.json"))
                if os.path.exists(os.path.join(directory, "nvmecmd.trace.log")):
                    os.remove(os.path.join(directory, "nvmecmd.trace.log"))

                for nvme_entry in base_info.info["_metadata"]["system"]["nvme list"]:
                    nvme_number = nvme_entry.split()[1]

                    info_directory = os.path.join(directory, f"nvme{nvme_number}")
                    this_info = Info(nvme=nvme_number, directory=info_directory)
                    uid = this_info.parameters["Unique Description"]
                    all_nvme_info[uid] = this_info

                    log.info(f" Read: {uid}", indent=False)

                    if start_nvme is None:
                        if nvme is None or nvme == nvme_number:
                            start_nvme = this_info.parameters["Unique Description"]
            else:
                info_directory = os.path.join(directory, f"nvme{nvme}")
                this_info = Info(nvme=nvme, directory=info_directory)

                start_nvme = this_info.parameters["Unique Description"]
                all_nvme_info[start_nvme] = this_info
                log.info(f" Read: {start_nvme}", indent=False)

        else:
            if not os.path.exists(file):
                raise console.NoInfoFile(file)

            log.info(f" Reading: {file}", indent=False)
            info = Info(from_file=file)
            start_nvme = info.parameters["Unique Description"]
            all_nvme_info[start_nvme] = info

        """
        if comparefile != "":
            if not os.path.exists(comparefile):
                raise console.NoCompareFile(comparefile)
            compare_info = Info(nvme=None, from_file=comparefile)
        else:
            compare_info = None
        """

        if start_nvme is None:
            raise console.NoNvme(nvme)

        create_dashboard(directory, start_nvme, all_nvme_info)

        sys.exit()

    except Exception as e:
        console.exit_on_exception(e)


def main():
    """Allow command line operation with unique arguments."""
    args = _parse_arguments()
    read_nvme(**args)


if __name__ == "__main__":
    main()
