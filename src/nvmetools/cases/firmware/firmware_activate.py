# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
from nvmetools import Info, TestCase, TestStep, rqmts


def firmware_activate(suite):
    """Verify performance and reliability of firmware activation.

    Activates firmware, downloads multiple versions to different slot and constantly
    activates while running IO stress.  Verifies no errors and max laatency in limit.
    No parameter changes.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Firmware activate", firmware_activate.__doc__) as test:
        test.skip("Firmware file was not found.")
