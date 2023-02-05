# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Console command that runs an NVMe Test Suite.

.. highlight:: none

Runs the NVME Test Suite defined in the file provided.  The test suite file is a python file.
By default testnvme first looks for the file in the local directory, then in the
~/Documents/nvmetools/suites directory, and lastly in the the nvmetools package.

Logs results to a directory in ~/Documents/nvmetools/results/<suite>.  The directory name is
defined by the uid command line parameter.  If uid was not specified the directory name is
based on the date and time the command was run.

.. warning::
   Test Suites create files in the fio directory on the volume being tested.  These files can
   take up signficant amount of space and are not deleted after the test suite runs.  They must
   be deleted manually.

.. note::
   Test Suites with self-test tests must be run as Administrator on Windows OS.

Command Line Parameters
    suite           Required positional argument.  Name of test suite to run
    --nvme, -n      Required. Integer NVMe device number, can be found using listnvme.
    --volume, -v    Required. Volume to test
    --uid, -i       String to use for the results directory name.  Must be unique.
    --loglevel, -l  The amount of information to display, integer, 0 is least and 3 is most.

**Example**

    This example runs a Test Suite called short_demo on NVMe 1.

    .. code-block:: python

        testnvme  short_demo  --nvme 1  --volume /mnt/nvme1a

    - `short_demo report (report.pdf) <https://raw.githubusercontent.com/jtjones1001/nvmetools/8c2dc6868e109702024e60037f6903a713f6ee1d/docs/examples/short_demo/report.pdf>`_
    - `short_demo dashboard (dashboard.html) <https://htmlpreview.github.io?https://github.com/jtjones1001/nvmetools/blob/8c2dc6868e109702024e60037f6903a713f6ee1d/docs/examples/short_demo/dashboard.html>`_

**Example**

    This example runs a Test Suite called big_demo on NVMe 1.

    .. code-block:: python

        testnvme  big_demo  --nvme 1 --volume g:

    - `big_demo report (report.pdf) <https://raw.githubusercontent.com/jtjones1001/nvmetools/d680e14fbbd71ede2d5ff0a154e40e2dfe467b43/docs/examples/big_demo/report.pdf>`_
    - `big_demo dashboard (dashboard.html) <https://htmlpreview.github.io?https://github.com/jtjones1001/nvmetools/blob/d680e14fbbd71ede2d5ff0a154e40e2dfe467b43/docs/examples/big_demo/dashboard.html>`_

"""  # noqa: E501
import argparse
import os
import sys

import nvmetools.support.console as console
from nvmetools import PACKAGE_DIRECTORY, TEST_SUITE_DIRECTORY, TestSuite


def main():
    """Runs NVMe Test Suite.

    Runs an NVME Test Suite defined in the nvmetools.suite python package.

    The test suite, NVMe to test, and logical volume to test must be specified.  Run the listnvme
    command to display the NVMe numbers.   The logical volume must reside on the physical NVMe drive
    being tested.

    Logs results to a directory in ~/Documents/nvmetools/results/<suite>.  The directory name is
    defined by the uid argument.  If uid was not specified the directory name is defined by the date
    and time the command was run.
    """
    try:
        parser = argparse.ArgumentParser(
            description=main.__doc__,
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, max_help_position=50),
        )
        parser.add_argument("suite", help="test suite to run")

        parser.add_argument(
            "-n",
            "--nvme",
            required=True,
            type=int,
            help="NVMe drive to test",
            metavar="#",
        )
        parser.add_argument(
            "-v",
            "--volume",
            required=True,
            help="logical volume to test",
        )
        parser.add_argument(
            "-l",
            "--loglevel",
            type=int,
            default=1,
            metavar="#",
            help="level of detail in logging, 0 is least, 3 is most",
        )
        parser.add_argument("-i", "--uid", help="unique id for directory name")

        args = vars(parser.parse_args())
        args["result directory"] = os.path.expanduser("~/Documents/nvmetools/results")

        for item in args.items():
            setattr(TestSuite, item[0], item[1])

        filename = f"{args['suite']}.py"

        # find the test suite file.

        filepath = os.path.abspath(filename)
        if not os.path.exists(filepath):
            filepath = os.path.join(TEST_SUITE_DIRECTORY, filename)
        if not os.path.exists(filepath):
            filepath = os.path.join(PACKAGE_DIRECTORY, "suites", filename)
        if not os.path.exists(filepath):
            raise console.NoTestSuite(args["suite"])

        with open(filepath, "r") as file_object:
            code = file_object.read()

        global suite
        exec(code, globals())
        if suite.state["result"] == "PASSED":
            sys.exit(0)
        else:
            sys.exit(2)

    except Exception as e:
        console.exit_on_exception(e)


if __name__ == "__main__":
    main()
