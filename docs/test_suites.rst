Test Suites
===========
Test Suites for NVMe solid state drives (SSD) run using the testnvme console command..

Test Suites are defined in a python file that is the first positional argument to testnvme. By
default testnvme first looks for the file in the local directory, then in the
~/Documents/nvmetools/suites directory, and lastly in the the nvmetools package.

The testnvme command passes the same standard parameter args parameter to each Test Suite.  This
parameter is a dictionary containing the following:

        nvme: NVMe to test
        volume: Logical volume to test
        loglevel: Amount of detail to include in the logging
        uid: Unique ID to use for directory name

The first test case in every Test Suite is suite_start_info and the last test case is suite_end_info.

Firmware
--------
.. automodule:: nvmetools.suites.firmware

Functional
----------
.. automodule:: nvmetools.suites.functional
.. automodule:: nvmetools.suites.stress

Performance
-----------
.. automodule:: nvmetools.suites.performance

Selftest
--------
.. automodule:: nvmetools.suites.health
.. automodule:: nvmetools.suites.selftest



