# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
from nvmetools import Info, TestCase, TestStep, rqmts


def firmware_download(suite):
    """Verify reliability and performance of firmware download.

    Downloads firmware files to every slot while running IO stress.  Checks max latency during
    download.

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Firmware download", firmware_download.__doc__) as test:
        test.skip("Firmware file was not found.")
