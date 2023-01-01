# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Console command that updates test suite results.

Test Suite results can be updated after completion by editing the results.json files.  This command
updates the html dashboard, PDF report, and results.json summary sections to reflect any changed
verification results.

To update a test result edit the results.json file in the test directory.  In the ["steps"]
section find verification to change.  Change the verification's "result" to "PASSED" or "FAILED".
Also recommend completing the "reviewer" and "note" parameters to track the change.

After the results.json files for all tests have been updated run this command.

Command Line Parameters
    --directory, -d     Directory of the test suite results to update

**Example**

    This example updates the test suite for the current directory.

    .. code-block:: python

        updatenvme .

"""
import argparse

from nvmetools.support.console import exit_on_exception
from nvmetools.support.framework import update_suite_files


def main():

    try:
        parser = argparse.ArgumentParser(
            description=main.__doc__,
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, max_help_position=50),
        )
        parser.add_argument("-d", "--directory", help="test suite directory", default=".")

        args = parser.parse_args()

        update_suite_files(args.directory)

    except Exception as e:
        exit_on_exception(e)


if __name__ == "__main__":
    main()
