Welcome to the nvmetools documentation
======================================
The nvmetools python package to read and test NVMe drives.

This package supports two use cases:  Tool User and Test Developer.  A Tool Users runs console
commands to read or test NVMe drives.  A Test Developer modifies or creates NVMe tests and
has a working knowledge of python and NVMe drives.

Click these links for examples of the information and test reporting provided by this package

- `NVMe Information <https://raw.githubusercontent.com/jtjones1001/nvmetools/2ff9f4c3f2c6b7d41f57f01e299c6272fef21994/docs/examples/readnvme/readnvme.log>`_
- `NVMe Information (all parameters) <https://raw.githubusercontent.com/jtjones1001/nvmetools/2ff9f4c3f2c6b7d41f57f01e299c6272fef21994/docs/examples/readnvme_all/readnvme.log>`_
- `NVMe Information (hex format) <https://raw.githubusercontent.com/jtjones1001/nvmetools/2ff9f4c3f2c6b7d41f57f01e299c6272fef21994/docs/examples/readnvme_hex/readnvme.log>`_
- `Test Dashboard <https://htmlpreview.github.io?https://github.com/jtjones1001/nvmetools/blob/03da67a81119e3b1d0a366e36c964796fd3a5683/docs/examples/big_demo/dashboard.html>`_
- `Test Report <https://raw.githubusercontent.com/jtjones1001/nvmetools/03da67a81119e3b1d0a366e36c964796fd3a5683/docs/examples/big_demo/report.pdf>`_

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
- `CHANGELOG <https://raw.githubusercontent.com/jtjones1001/nvmetools/main/CHANGELOG.md>`_


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



