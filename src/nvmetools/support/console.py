# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Exception and constants for standardizing script exit."""
import sys

from nvmetools.support.log import log

USAGE_EXIT_CODE = 1
FAILURE_EXIT_CODE = 2
EXCEPTION_EXIT_CODE = 50


def exit_on_exception(e):
    """Log exceptions in a standard way and exit with an exception error code.

    Exceptions with the nvmetools attribute are specific to this package and have a unique error
    code that is returned.  All other exceptions return the generic exception error code.

    Args:
      e (exception): The fatal exception that was raised
    """
    if not hasattr(e, "nvmetools"):
        e.code = EXCEPTION_EXIT_CODE
        log.header(f" FATAL ERROR : {e.code}", indent=False)
        log.exception("Unknown error.  Send developer details below and debug.log\n\n")
    else:
        log.header(f"FATAL ERROR : {e.code}", indent=False)
        log.error(e)

    sys.exit(e.code)
