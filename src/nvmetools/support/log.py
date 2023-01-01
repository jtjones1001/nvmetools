# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Logs information to screen and files for this package."""

import logging
import os
import platform
import sys

from nvmetools import __brandname__, __copyright__, __package_name__, __version__, __website__

import psutil

IMPORTANT = 25
VERBOSE = 15

logging.VERBOSE = VERBOSE
logging.IMPORTANT = IMPORTANT


class _DebugLogger(logging.Logger):
    def debug(self, msg, indent=True, *args: any, **kwargs: any):
        if self.isEnabledFor(logging.DEBUG):
            if indent:
                msg = "       " + msg
            else:
                msg = " " + msg

            self._log(logging.DEBUG, msg, args, **kwargs)

    def verbose(self, msg, indent=True, *args: any, **kwargs: any):
        if self.isEnabledFor(logging.VERBOSE):
            if indent:
                msg = "       " + msg
            else:
                msg = " " + msg

            self._log(logging.VERBOSE, msg, args, **kwargs)

    def info(self, msg, indent=True, *args: any, **kwargs: any):

        if self.isEnabledFor(logging.INFO):
            if indent:
                msg = "       " + msg
            else:
                msg = " " + msg

            self._log(logging.INFO, msg, args, **kwargs)

    def important(self, msg, indent=True, *args: any, **kwargs: any):
        if self.isEnabledFor(logging.IMPORTANT):
            if indent:
                msg = "       " + msg
            else:
                msg = " " + msg

            self._log(logging.IMPORTANT, msg, args, **kwargs)

    def banner(self):
        epic_banner = f" {__brandname__}, version {__version__}, {__website__}, {__copyright__}"
        p = psutil.Process(os.getpid())

        self.info("")
        self.info(f"{epic_banner}", indent=False)
        self.verbose("")
        self.verbose(f" Python: {p.exe()}", indent=False)
        self.verbose(f"         {sys.version}", indent=False)
        self.verbose(f"         Process ID: {p.pid}", indent=False)
        self.verbose("")
        self.verbose(f" Host:   {platform.node()}", indent=False)
        self.verbose(f" OS:     {platform.system()} {platform.version()}", indent=False)
        self.info("")

    def frames(self, function, frames: list, indent=True):
        self.debug(" ")
        self.debug(f"{function}() called from {frames[1].filename} line {frames[1].lineno}", indent=indent)

    def header(self, title, width=90, indent=True):
        self.info("-" * width, indent=indent)
        self.info(title, indent=indent)
        self.info("-" * width, indent=indent)


def start_logger(directory, log_level, filename=None, debug_log=True):
    """Start the package logger.

    This function starts the log file that is used by all other modules.

    Args:
       directory:  Directory to create the log file
       log_level:  Level of logging, e.g. logging.INFO, logging.DEBUG
       filename:  (optional) Name of log file.  Default is debug.log
       debug_log: Flag indicating to add more details for debug

    """
    os.makedirs(directory, exist_ok=True)

    if debug_log:
        file_handler = logging.FileHandler(os.path.join(directory, "trace.log"), mode="w")
        log.addHandler(file_handler)
        file_handler.setFormatter(logging.Formatter("[%(asctime)s]  %(message)s"))
        file_handler.setLevel(logging.DEBUG)

    if filename is not None:
        file2_handler = logging.FileHandler(os.path.join(directory, filename), mode="w")
        log.addHandler(file2_handler)

    log.handlers[0].setLevel(log_level)
    file2_handler.setLevel(log.handlers[0].level)

    log.banner()

    return log


log = _DebugLogger(__package_name__)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
log.addHandler(console_handler)
log.setLevel(logging.DEBUG)
