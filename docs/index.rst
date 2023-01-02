Welcome to the nvmetools documentation
======================================
The nvmetools python package to read and test NVMe drives.

This package supports two use cases:  Tool User and Test Developer.  A Tool Users runs console
commands to read or test NVMe drives.  A Test Developer modifies or creates NVMe tests and
has a working knowledge of python and NVMe drives.

.. warning::
   The NVMe Test Cases provided in this release are examples only.

   This is a beta release and has only been tested on a small number of drives, systems, and OS.

Future Enhancements - Tool User
-------------------------------
Expand the amount of information read from the drive.  Specfically, the additional features and logs
defined in the NVMe Base Specification 1.4 and later.

Future Enhancements - Test Developer
-------------------------------------
Create a complete NVMe Test Suite that can be used for the integration testing of NVMe PCIe drives
in commercial computers (e.g. laptops).

        - Aquire additional computers to verify the current NVMe Test Cases
        - Add the following NVMe Test Cases
                - Reset and Power Cycles
                - Power measurements
                - Power loss protection
                - Firmware update
                - Format and Sanitize features

Change History
--------------
- `CHANGELOG <https://github.com/jtjones1001/nvmetools/blob/e4dbba5f95b5a5b621d131e6db3ea104dc51d1f3/src/nvmetools/resources/documentation/checknvme/nvme_health_check.pdf>`_


.. Hidden TOCs

.. toctree::
        :caption: Tool User
        :maxdepth: 1
        :hidden:

        install_steps
        info_commands
        test_commands

.. toctree::
        :maxdepth: 1
        :caption: Test Developer
        :hidden:

        framework
        test_suites
        test_cases
        test_steps
        verifications
        information



