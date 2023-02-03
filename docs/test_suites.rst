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
This suite runs Test Cases to verify firmware update, firmware activate, firmware download,
and firmware security features.

Functional
----------
This suite runs Test Cases to verify the admin commands, SMART attrbiutes, timestamp, and
short self-test.

Health
------
Check NVMe is a short Test Suite that verifies drive health and wear by running the drive
diagnostic, reviewing SMART data and Self-Test history.

Performance
-----------
Measures IO peformance for several conditions including short and long bursts of reads
and writes.

Selftest
--------
This suite runs Test Cases to verify the short and extended versions of the self-test.

Stress
------
This suite runs Test Cases to stress the drive in several different ways
