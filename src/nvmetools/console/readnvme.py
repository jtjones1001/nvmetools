# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Console command that displays and logs NVMe drive information.

Reads NVMe drive information using the Admin Commands: Get Log Page, Get Feature, Identify
Controller, and Identify Namespace. A few parameters, such as PCIe location and link info, are read
from the OS.

The amount and type of information displayed can be configured with command line parameters.

**Command Line Parameters**
    --nvme, -n      Integer NVMe device number, can be found using listnvme.
    --verbose, -v   Display additional parameters.
    --all, -a       Display all parameters.
    --describe, -d  Display descriptions for each parameter.
    --list, -l      Display parameters as a list.
    --hex, -x       Display raw data read as hex format.
    --pdf, -p       Flag to create PDF report.

The following log files are saved to the working directory:

    - readnvme.log contains the console output
    - nvme.info.json contains the NVMe parameters in json format
    - readnvme.pdf is a PDF format report (only if --pdf specified)
    - nvmecmd.trace.log and trace.log are trace file for debug if something goes wrong
    - read.summary.json contains information on the Admin commands used

**Example**

    This example reads the information of NVMe 0.  To display all NVMe parameters to the console add --all.
    To display the raw data in hex format use --hex.

    .. highlight:: none
    .. code-block:: python

        readnvme  --nvme 0
        readnvme  --nvme 0 --all
        readnvme  --nvme 0 --hex

    Example console output

    .. code-block::

        EPIC NVMe Utilities, version 0.0.8, www.epicutils.com, Copyright (C) 2022 Joe Jones

         ------------------------------------------------------------------------------------------
          NVME DRIVE 0  (/dev/nvme0)
         ------------------------------------------------------------------------------------------
          Vendor                                             Sandisk
          Model Number (MN)                                  WDC WDS250G2B0C-00PXH0
          Serial Number (SN)                                 2035A0805352
          Size                                               250 GB
          Version (VER)                                      1.4.0

          Number of Namespaces (NN)                          1
          Namespace 1 Size                                   250 GB
          Namespace 1 Active LBA Size                        512
          Namespace 1 EUID                                   001b44-8b49bc0ecb
          Namespace 1 NGUID                                  e8238fa6bf530001-001b44-8b49bc0ecb

          Firmware Revision (FR)                             211070WD
          Firmware Slots                                     2
          Firmware Activation Without Reset                  Supported

          Maximum Data Transfer Size (MDTS)                  128
          Enable Host Memory (EHM)                           Enabled
          Host Memory Buffer Size (HSIZE)                    8,192 pages
          Volatile Write Cache (VWC)                         Supported
          Volatile Write Cache Enable (WCE)                  Enabled

          Critical Warnings                                  No
          Media and Data Integrity Errors                    0
          Number Of Failed Self-Tests                        0
          Number of Error Information Log Entries            1

         ----------------------------------------------------------------------
          Temperature       Value          Under Threshold     Over Threshold
         ----------------------------------------------------------------------
          Composite         25 C           -5 C                80 C

         ------------------------------------------------------------------------
          Throttle      Total       TMT1        TMT2        WCTEMP      CCTEMP
         ------------------------------------------------------------------------
          Time (Hrs)    0.917       0.000       0.000       0.015       0.001
          Threshold                 Disabled    Disabled    80 C        85 C
          Count                     0           0           --          --

          Available Spare                                    100 %
          Available Spare Threshold                          10 %
          Controller Busy Time                               15,937 Min
          Data Read                                          356,901.852 GB
          Data Written                                       120,948.038 GB
          Host Read Commands                                 9,314,262,073
          Host Write Commands                                5,212,102,971
          Percentage Used                                    17 %
          Power On Hours                                     1,779
          Power Cycles                                       153
          Unsafe Shutdowns                                   23

         ------------------------------------------------------------------------------------------
          State   NOP    Max         Active      Idle        Entry Latency   Exit Latency
         ------------------------------------------------------------------------------------------
          0              3.5 W       1.8 W       0.63 W
          1              2.4 W       1.6 W       0.63 W
          2              1.9 W       1.5 W       0.63 W
          3       Yes    0.02 W                  0.02 W      3,900 uS        11,000 uS
          4       Yes    0.005 W                 0.005 W     5,000 uS        39,000 uS

          Autonomous Power State Transition                  Supported
          Autonomous Power State Transition Enable (APSTE)   Enabled
          Non-Operational Power State Permissive Mode        Supported
          Non-Operational Power State Permissive Mode Enable (NOPPME) Enabled

          PCI Width                                          x4
          PCI Speed                                          Gen3 8.0GT/s
          PCI Rated Width                                    x4
          PCI Rated Speed                                    Gen3 8.0GT/s

         ------------------------------------------------------------------------------------------
          PCI         Vendor              Vendor ID    Device ID    Location
         ------------------------------------------------------------------------------------------
          Endpoint    Sandisk             0x15B7       0x5009       Bus 1, device 0, function 0
          Root                            0x8086       0xA340       Bus 0, device 27, function 0


    * `Example console output with --all (readnvme.log) <https://raw.githubusercontent.com/jtjones1001/nvmetools/2ff9f4c3f2c6b7d41f57f01e299c6272fef21994/docs/examples/readnvme_all/readnvme.log>`_
    * `Example console output with --hex (readnvme.log) <https://raw.githubusercontent.com/jtjones1001/nvmetools/2ff9f4c3f2c6b7d41f57f01e299c6272fef21994/docs/examples/readnvme_hex/readnvme.log>`_

"""  # noqa: E501
import argparse
import logging
import os
import sys

from nvmetools.support.console import exit_on_exception
from nvmetools.support.info import Info
from nvmetools.support.log import start_logger


def _parse_arguments():
    """Parse input arguments from command line."""
    parser = argparse.ArgumentParser(
        description=read_nvme.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-n", "--nvme", type=int, default=0, help="NVMe drive to read", metavar="#")
    parser.add_argument("-d", "--describe", help="Display parameter descriptions", action="store_true")
    parser.add_argument("-l", "--list", dest="as_list", help="Display parameters as list", action="store_true")
    parser.add_argument(
        "-x", "--hex", dest="as_hex", help="Display information in hex format", action="store_true"
    )
    parser.add_argument("-a", "--all", dest="as_all", help="Display all parameters", action="store_true")
    parser.add_argument("-p", "--pdf", dest="create_pdf", help="Create a pdf report", action="store_true")
    parser.add_argument("-v", "--verbose", help="Display additional parameters", action="store_true")
    return vars(parser.parse_args())


def read_nvme(nvme=0, as_list=False, as_hex=False, as_all=False, describe=False, create_pdf=False, verbose=False):
    """Display and log NVMe information.

    Reads NVMe information using the nvmecmd utility. This utility creates a file named nvme.info.json
    with the entire set of information. This script reads nvme.info.json and displays some or all of
    the NVMe information.

    Additional parameters are displayed if --verbose is specified.  All parameters are displayed if
    --all specified.  Parameters are displayed as a list if --list specified.  Parameter descriptions
    are displayed if --describe specified.

    Information is displayed as hex data if --hex specified.  If this option is specified
    these options have no effect: --list, --all, and --description.

    The console output is logged to readnvme.log.  If the --pdf option is specified an
    readnvme.pdf file is created.
    """
    try:
        directory = os.path.join(os.path.abspath("."))
        log_level = logging.INFO

        if verbose:
            log_level = logging.VERBOSE

        start_logger(directory, log_level, "readnvme.log")

        info = Info(
            nvme=nvme,
            directory=directory,
            description=describe,
            verbose=verbose,
        )
        if as_hex:
            info.show_hex()
            sys.exit()

        if as_all:
            info.show_all()
        else:
            if as_list:
                info.show_list()
            else:
                info.show()

        # Create report if specified, only load report module if using it because it's slow

        if create_pdf:
            from nvmetools.support.report import InfoReport

            report = InfoReport(info)
            report.save()

        sys.exit()

    except Exception as e:
        exit_on_exception(e)


def main():
    """Allow command line operation with unique arguments."""
    args = _parse_arguments()
    read_nvme(**args)


if __name__ == "__main__":
    main()
