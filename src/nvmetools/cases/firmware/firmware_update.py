# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
from nvmetools import Info, TestCase, TestStep, rqmts


def firmware_update(suite):
    """Verify the firmware update feature.

    Downloads and activates firmware file.  Cycles between n and n-1.  Checks every slot.
    Assumes update without reset.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Firmware update", firmware_update.__doc__) as test:
        test.skip("Firmware file was not found.")
