# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import platform
import time

import nvmetools.lib.nvme.requirements as rqmts
from nvmetools.apps.fio import clean_fio_files
from nvmetools.support.framework import TestCase, TestStep
from nvmetools.support.process import RunProcess


def trim(suite):
    """Perform trim to free up and erase unused blocks.

    This test deletes any fio data files and then runs the OS specific trim command.  This command
    informs the drive of the blocks not being used by the OS.  The drive can then erase these blocks
    and add them to the available list.

    After the command the test waits several minutes to ensure the trim command completes.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Trim", trim.__doc__) as test:

        with TestStep(test, "Run trim") as step:
            clean_fio_files(suite.volume)

            if platform.system() == "Windows":
                args = ["defrag.exe", suite.volume, "/retrim"]
            else:
                args = ["fstrim", suite.volume]

            trim_process = RunProcess(args, step.directory, wait=True, timeout_sec=300)
            test.data["return code"] = trim_process.return_code
            rqmts.trim_command_pass(step, trim_process.return_code)

            time.sleep(180)
