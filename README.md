
Python package with console commands to list, read, and test NVMe SSD installed in computers running Windows and
Linux OS.

## Features

* Console commands to:
  * List NVMe devices
  * Read NVMe information
  * Check NVMe health
  * Test NVMe features
* python module that can:
  * Read NVMe information
  * Read and check NVMe information at regular interval (e.g. check SMART attributes every second)
  * Check for critical warnings, thermal throttling, excessive wear, etc.
  * Run self-test diagnostic
  * Create simple test and test suites


## Installation

```
pip install nvmetools
```
On Linux OS the nvmecmd utility must be granted access to read NVMe devices with the below commands.  Run
the listnvme console command and it will display the below commands with the actual nvmecmd path.  Run these
commands to grant nvmecmd access to read NVMe devices.
```
    sudo chmod 777 <path to nvmecmd>
    sudo setcap cap_sys_admin,cap_dac_override=ep <path to nvmecmd>
```
<br>

## List NVMe devices

This console command lists the NVMe devices with an unique NVMe number that is required by the other
console commands.
```
listnvme
```

<details>
  <summary>Example console output</summary>

  ```
  EPIC NVMe Utilities, version 0.0.7, www.epicutils.com, Copyright (C) 2022 Joe Jones

  On Window systems the NVMe number is the physical drive number.
  For example, physicaldrive2 would be listed as NVMe 2.

  On Linux systems the NVMe number is the nvme devices number.
  For example, /dev/nvme2 would be listed as NVMe 2.

       LIST OF NVME DRIVES

       NVMe 0 : Sandisk WDC WDS250G2B0C-00PXH0 250GB
       NVMe 1 : Samsung SSD 970 EVO Plus 250GB
  ```
</details>
<br/>

## Read NVMe information

This console command reads the information for an NVMe device.  Provide the NVMe number with the --nvme
parameter to specify the NVMe to read.  For example, the command below reads NVMe 0.
```
readnvme --nvme 0
```
This command displays NVMe information to the console and logs it to a couple of files.  The console output is
logged to readnvme.log and the detailed NVMe information is logged to nvme.info.json.

[Example nvme.info.json](https://github.com/jtjones1001/nvmetools/blob/7c29927faf9bf7dc3a33cfde8fd7c47dd4d78de4/docs/examples/readnvme/nvme.info.json)

By default, only a subset of NVMe parameters are displayed to the console.  All parameters can be displayed
with the -all parameter.  The raw hex data from the commands can be displayed with the --hex parameter.

<details>
  <summary>Example console output</summary>

         ------------------------------------------------------------------------------------------
          NVME DRIVE 0  (/dev/nvme0)
         ------------------------------------------------------------------------------------------
          Vendor                                             Sandisk
          Model Number (MN)                                  WDC WDS250G2B0C-00PXH0
          Serial Number (SN)                                 2035A0805352
          Size                                               250 GB
          Version (VER)                                      1.4.0

          Number of Namespaces (NN)                          1
          Namespace 1 Size                                   250 GB
          Namespace 1 Active LBA Size                        512
          Namespace 1 EUID                                   001b44-8b49bc0ecb
          Namespace 1 NGUID                                  e8238fa6bf530001-001b44-8b49bc0ecb

          Firmware Revision (FR)                             211070WD
          Firmware Slots                                     2
          Firmware Activation Without Reset                  Supported

          Maximum Data Transfer Size (MDTS)                  128
          Enable Host Memory (EHM)                           Enabled
          Host Memory Buffer Size (HSIZE)                    8,192 pages
          Volatile Write Cache (VWC)                         Supported
          Volatile Write Cache Enable (WCE)                  Enabled

          Critical Warnings                                  No
          Media and Data Integrity Errors                    0
          Number Of Failed Self-Tests                        0
          Number of Error Information Log Entries            1

         ----------------------------------------------------------------------
          Temperature       Value          Under Threshold     Over Threshold
         ----------------------------------------------------------------------
          Composite         25 C           -5 C                80 C

         ------------------------------------------------------------------------
          Throttle      Total       TMT1        TMT2        WCTEMP      CCTEMP
         ------------------------------------------------------------------------
          Time (Hrs)    0.850       0.000       0.000       0.014       0.001
          Threshold                 Disabled    Disabled    80 C        85 C
          Count                     0           0           --          --

          Available Spare                                    100 %
          Available Spare Threshold                          10 %
          Controller Busy Time                               15,158 Min
          Data Read                                          339,285.881 GB
          Data Written                                       114,666.719 GB
          Host Read Commands                                 8,937,852,313
          Host Write Commands                                4,997,601,165
          Percentage Used                                    16 %
          Power On Hours                                     1,733
          Power Cycles                                       146
          Unsafe Shutdowns                                   22

         ------------------------------------------------------------------------------------------
          State   NOP    Max         Active      Idle        Entry Latency   Exit Latency
         ------------------------------------------------------------------------------------------
          0              3.5 W       1.8 W       0.63 W
          1              2.4 W       1.6 W       0.63 W
          2              1.9 W       1.5 W       0.63 W
          3       Yes    0.02 W                  0.02 W      3,900 uS        11,000 uS
          4       Yes    0.005 W                 0.005 W     5,000 uS        39,000 uS

          Autonomous Power State Transition                  Supported
          Autonomous Power State Transition Enable (APSTE)   Enabled
          Non-Operational Power State Permissive Mode        Supported
          Non-Operational Power State Permissive Mode Enable (NOPPME) Enabled

          PCI Width                                          x4
          PCI Speed                                          Gen3 8.0GT/s
          PCI Rated Width                                    x4
          PCI Rated Speed                                    Gen3 8.0GT/s

         ------------------------------------------------------------------------------------------
          PCI         Vendor              Vendor ID    Device ID    Location
         ------------------------------------------------------------------------------------------
          Endpoint    Sandisk             0x15B7       0x5009       Bus 1, device 0, function 0
          Root                            0x8086       0xA340       Bus 0, device 27, function 0

</details>

<details>
  <summary>Example console output with --all option</summary>

          128-bit Host Identifier                            Not Supported
          ANA Group Identifier Maximum (ANAGRPMAX)           Not Supported
          ANA Transition Time (ANATT)                        Not Supported
          Abort Command Limit (ACL)                          5
          Admin Vendor Specific command handling             Not Vendor Specific
          Aggregation Threshold (THR)                        1
          Aggregation Time (TIME)                            No Delay
          Arbitration Burst (AB)                             4 (2^4=16)
          Associated Function Type                           PCI
          Asymmetric Namespace Access Change Notices         Not Supported
          Asymmetric Namespace Access Reporting              Not Supported
          Asynchronous Event Request Limit (AERL)            8
          Atomic Write Unit Normal (AWUN)                    1
          Atomic Write Unit Power Fail (AWUPF)               1
          Autonomous Power State Transition                  Supported
          Autonomous Power State Transition Enable (APSTE)   Enabled
          Available Space Below Threshold                    No
          Available Spare                                    100 %
          Available Spare Threshold                          10 %
          Block Erase Sanitize                               Supported
          Command Retry Delay Time 1 (CRDT1)                 0 (0 mS)
          Command Retry Delay Time 2 (CRDT2)                 0 (0 mS)
          Command Retry Delay Time 3 (CRDT3)                 0 (0 mS)
          Commands Supported and Effects Log Page            Supported
          Compare NVM Command                                Supported
          Compare and Write Fused Operation                  Not Supported
          Composite Temperature                              26 C
          Composite Temperature Over Threshold               80 C
          Composite Temperature Under Threshold              -5 C
          Controller Busy Time                               15,158 Min
          Controller ID (CNTLID)                             1
          Controller Type (CNTRLTYPE)                        I/O Controller
          Controller Vendor                                  Sandisk
          Critical Composite Temperature Threshold (CCTEMP)  85 C
          Critical Composite Temperature Time                2 Min
          Critical Warnings                                  No
          Crypto Erase                                       Not Supported
          Crypto Erase Sanitize                              Not Supported
          Current Number Of Errors                           0
          Current Number Of Self-Tests                       20
          Current Power State (PS)                           4
          Current Self-Test Completion                       0
          Current Self-Test Operation                        No Test In Progress
          Data Read                                          339,285.881 GB
          Data Units Read                                    662,667,737
          Data Units Written                                 223,958,435
          Data Written                                       114,666.719 GB
          Dataset Management NVM Command                     Supported
          Deallocated or Unwritten Logical Block Error Enable (DULBE) Disabled
          Device Self-test Command                           Supported
          Directive Send and Directive Receive Commands      Not Supported
          Disable Normal (DN)                                Not Supported
          Doorbell Buffer Config Command                     Not Supported
          EG Available Space Below Threshold                 No
          EG Critical Warnings                               No
          EG Reliability Degraded                            No
          EG in Read Only                                    No
          Enable Host Memory (EHM)                           Enabled
          Endurance Group Event Log Page Change Notices      Not Supported
          Endurance Group Identifier Maximum (ENDGIDMAX)     0
          Endurance Groups                                   Not Supported
          Error Log Page Entries (ELPE)                      256
          Extended Data for Get Log Page                     Supported
          Extended Device Self-test Time (EDSTT)             44 Min
          FRU Globally Unique Identifier (FGUID)             000000-00000000000000000000000000
          Firmware Activation Notices                        Supported
          Firmware Activation Notices Enable                 Enabled
          Firmware Activation Without Reset                  Supported
          Firmware Active Slot                               1
          Firmware Commit and Image Download Commands        Supported
          Firmware Pending Slot                              Not Reported
          Firmware Revision (FR)                             211070WD
          Firmware Slot 1 Read Status                        Read/Write
          Firmware Slot 1 Revision                           211070WD
          Firmware Slot 2 Revision
          Firmware Slots                                     2
          Firmware Update Granularity (FWUG)                 4 KiB
          Format All Namespaces                              Not Supported
          Format NVM Command                                 Supported
          Get LBA Status capability                          Not Supported
          High Priority Weight (HPW)                         1
          Highest Version Detected                           1.4.0
          Host Controlled Thermal Management (HCTMA)         Supported
          Host Memory Buffer Minimum Descriptor Entry Size (HMMINDS) No limitations
          Host Memory Buffer Minimum Size (HMMIN)            823 (3,292 KiB)
          Host Memory Buffer Preferred Size (HMPRE)          51,200 (204,800 KiB)
          Host Memory Buffer Size (HSIZE)                    8,192
          Host Memory Descriptor List Address (HMDLAL)       0x0A028000
          Host Memory Descriptor List Address (HMDLAU)       0x00000001
          Host Memory Descriptor List Entry Count (HMDLEC)   8
          Host Memory Maximum Descriptors Entries (HMMAXD)   8
          Host Read Commands                                 8,937,852,313
          Host Timestamp                                     1,659,225,286,713 mS
          Host Timestamp Decoded                             2022-07-30 16:54:46.713 DST
          Host Write Commands                                4,997,601,165
          IEEE OUI Identifier (IEEE)                         00-1b-44
          Keep Alive Support (KAS)                           Not Supported
          LBA Status Information Notices                     Not Supported
          Low Priority Weight (LPW)                          1
          Maximum Completion Queue Entry Size                4 (2^4=16)
          Maximum Data Transfer Size (MDTS)                  7 (2^7=128)
          Maximum Number Allowed Namespaces (MNAN)           0
          Maximum Outstanding Commands (MAXCMD)              Not Supported
          Maximum Submission Queue Entry Size                6 (2^6=64)
          Maximum Thermal Management Temperature (MXTMT)     85 C
          Maximum Time for Firmware Activation (MTFA)        5,000 mS
          Media and Data Integrity Errors                    0
          Media in Read Only                                 No
          Medium Priority Weight (MPW)                       1
          Minimum Thermal Management Temperature (MNTMT)     0 C
          Model Number (MN)                                  WDC WDS250G2B0C-00PXH0
          NVM Set Identifier Maximum (NSETIDMAX)             0
          NVM Sets                                           Not Supported
          NVM Subsystem Controllers                          Single
          NVM Subsystem NVMe Qualified Name (SUBNQN)         nqn.2018-01.com.wdc:nguid:E8238FA6BF53-0001-001B448B49BC0ECB
          NVM Subsystem PCIe Ports                           Single
          NVME MI Send/Receive Commands                      Not Supported
          Namespace 1 ANA Group Identifier (ANAGRPID)        Not Reported
          Namespace 1 Active LBA Format                      0
          Namespace 1 Atomic Boundary Offset (NABO)          7
          Namespace 1 Atomic Boundary Size Normal (NABSN)    7
          Namespace 1 Atomic Boundary Size Power Fail (NABSPF) 7
          Namespace 1 Atomic Compare & Write Unit (NACWU)    Same as ACWU
          Namespace 1 Atomic Write Unit Normal (NAWUN)       7
          Namespace 1 Atomic Write Unit Power Fail (NAWUPF)  7
          Namespace 1 Atomic Writes                          Supported
          Namespace 1 Capacity (NCAP)                        488,397,168
          Namespace 1 Deallocate Bit in Write Zeros          Supported
          Namespace 1 Deallocate Guard Field                 Not Supported
          Namespace 1 Deallocate Logical Block Value         All 00h
          Namespace 1 Endurance Group Identifier (ENDGID)    Not Supported
          Namespace 1 Exclusive Access All Registrants Reservation Not Supported
          Namespace 1 Exclusive Access Registrants Only Reservation Not Supported
          Namespace 1 Exclusive Access Reservation           Not Supported
          Namespace 1 Extended Data LBA                      Not Supported
          Namespace 1 Format Percent Complete                0
          Namespace 1 Format Progress Indicator              Supported
          Namespace 1 Globally Unique Identifier (NGUID)     e8238fa6bf530001-001b44-8b49bc0ecb
          Namespace 1 IEEE Extended Unique Identifier (EUI64) 001b44-8b49bc0ecb
          Namespace 1 IO Optimize Fields                     Not Supported
          Namespace 1 Ignore Existing Key Specification      1.2.1 or earlier
          Namespace 1 LBA 0 Data Size (LBADS)                9 (2^9=512) *
          Namespace 1 LBA 0 Relative Performance (RP)        Good Performance *
          Namespace 1 LBA 1 Data Size (LBADS)                12 (2^12=4096)
          Namespace 1 LBA 1 Relative Performance (RP)        Better Performance
          Namespace 1 Logical Block Error                    Not Supported
          Namespace 1 Metadata Transfer Buffer               Not Supported
          Namespace 1 Metadata Transfer Extended LBA         Not Supported
          Namespace 1 NGUID/EUID Not Reused                  Not Supported
          Namespace 1 NVM Capacity (NVMCAP)                  250,059,350,016
          Namespace 1 NVM Set Identifier (NVMSETID)          Not Supported
          Namespace 1 Number of LBA Formats (NLBAF)          2
          Namespace 1 Optimal IO Boundary (NOIOB)            Not Reported
          Namespace 1 Optimal Write Size (NOWS)              1
          Namespace 1 Persist Through Power Loss             Not Supported
          Namespace 1 Preferred Deallocate Alignment (NPDA)  1
          Namespace 1 Preferred Deallocate Granularity (NPDG) 1
          Namespace 1 Preferred Write Alignment (NPWA)       1
          Namespace 1 Preferred Write Granularity (NPWG)     1
          Namespace 1 Protection First                       Not Supported
          Namespace 1 Protection Information Enabled         Disabled
          Namespace 1 Protection Information First           Last 8 Bytes
          Namespace 1 Protection Last                        Not Supported
          Namespace 1 Protection Type 1                      Not Supported
          Namespace 1 Protection Type 2                      Not Supported
          Namespace 1 Protection Type 3                      Not Supported
          Namespace 1 Shared                                 Not Supported
          Namespace 1 Size                                   250 GB
          Namespace 1 Size in GiB                            232.9 GiB
          Namespace 1 Size in LBA (NSZE)                     488,397,168
          Namespace 1 Thin Provisioning                      Not Supported
          Namespace 1 Utilization (NUSE)                     488,397,168
          Namespace 1 Write Exclusive All Registrants Reservation Not Supported
          Namespace 1 Write Exclusive Registrants Only Reservation Not Supported
          Namespace 1 Write Exclusive Reservation            Not Supported
          Namespace 1 Write Protected                        No
          Namespace Attribute Notices                        Not Supported
          Namespace Granularity                              Not Supported
          Namespace Management and Attachment Commands       Not Supported
          No-Deallocate Inhibited (NDI)                      Supported
          No-Deallocate Modifies Media After Sanitize (NODMMAS) Media not modified
          Non-Operational Power State Permissive Mode        Supported
          Non-Operational Power State Permissive Mode Enable (NOPPME) Enabled
          Non-zero ANAGRPID                                  Not Supported
          Number Of Failed Self-Tests                        0
          Number of ANA Group Identifiers (NANAGRPID)        Not Supported
          Number of Error Information Log Entries            1
          Number of Namespaces (NN)                          1
          Number of Power States Support (NPSS)              5
          OS Location                                        /dev/nvme0
          One Self-Test                                      Per System
          Overwrite Sanitize                                 Not Supported
          PCI Device ID                                      0x5009
          PCI Location                                       Bus 1, device 0, function 0
          PCI Rated Speed                                    Gen3 8.0GT/s
          PCI Rated Width                                    x4
          PCI Speed                                          Gen3 8.0GT/s
          PCI Subsystem Vendor ID (SSVID)                    0x15B7
          PCI Vendor ID (VID)                                0x15B7
          PCI Width                                          x4
          PCIe Management Endpoint (PCIEME)                  Not Supported
          Percentage Used                                    16 %
          Permanent Write Protect                            Not Supported
          Persistent Event Log                               Supported
          Persistent Event Log Size (PELS)                   64 KiB
          Persistent Memory Unreliable                       No
          Power Cycles                                       146
          Power On Hours                                     1,733
          Power State 0 Active Power (ACTP)                  1.8 Watts
          Power State 0 Active Power Workload (APW)          Workload #2
          Power State 0 Entry Latency (ENLAT)                Not Reported
          Power State 0 Exit Latency (EXLAT)                 Not Reported
          Power State 0 Idle Power (IDLP)                    0.63 Watts
          Power State 0 Idle Time Prior to Transition (ITPT) 100 mS
          Power State 0 Idle Transition Power State (ITPS)   3
          Power State 0 Maximum Power (MP)                   3.5 Watts
          Power State 0 Non-Operational State (NOPS)         False
          Power State 0 Relative Read Latency (RRL)          0
          Power State 0 Relative Read Throughput (RRT)       0
          Power State 0 Relative Write Latency (RWL)         0
          Power State 0 Relative Write Throughput (RWT)      0
          Power State 1 Active Power (ACTP)                  1.6 Watts
          Power State 1 Active Power Workload (APW)          Workload #2
          Power State 1 Entry Latency (ENLAT)                Not Reported
          Power State 1 Exit Latency (EXLAT)                 Not Reported
          Power State 1 Idle Power (IDLP)                    0.63 Watts
          Power State 1 Idle Time Prior to Transition (ITPT) 100 mS
          Power State 1 Idle Transition Power State (ITPS)   3
          Power State 1 Maximum Power (MP)                   2.4 Watts
          Power State 1 Non-Operational State (NOPS)         False
          Power State 1 Relative Read Latency (RRL)          0
          Power State 1 Relative Read Throughput (RRT)       0
          Power State 1 Relative Write Latency (RWL)         0
          Power State 1 Relative Write Throughput (RWT)      0
          Power State 2 Active Power (ACTP)                  1.5 Watts
          Power State 2 Active Power Workload (APW)          Workload #2
          Power State 2 Entry Latency (ENLAT)                Not Reported
          Power State 2 Exit Latency (EXLAT)                 Not Reported
          Power State 2 Idle Power (IDLP)                    0.63 Watts
          Power State 2 Idle Time Prior to Transition (ITPT) 100 mS
          Power State 2 Idle Transition Power State (ITPS)   3
          Power State 2 Maximum Power (MP)                   1.9 Watts
          Power State 2 Non-Operational State (NOPS)         False
          Power State 2 Relative Read Latency (RRL)          0
          Power State 2 Relative Read Throughput (RRT)       0
          Power State 2 Relative Write Latency (RWL)         0
          Power State 2 Relative Write Throughput (RWT)      0
          Power State 3 Active Power (ACTP)                  Not Reported
          Power State 3 Active Power Workload (APW)          No workload
          Power State 3 Entry Latency (ENLAT)                3,900 uS (0.003 sec)
          Power State 3 Exit Latency (EXLAT)                 11,000 uS (0.011 sec)
          Power State 3 Idle Power (IDLP)                    0.02 Watts
          Power State 3 Idle Time Prior to Transition (ITPT) 2,000 mS
          Power State 3 Idle Transition Power State (ITPS)   4
          Power State 3 Maximum Power (MP)                   0.02 Watts
          Power State 3 Non-Operational State (NOPS)         True
          Power State 3 Relative Read Latency (RRL)          3
          Power State 3 Relative Read Throughput (RRT)       3
          Power State 3 Relative Write Latency (RWL)         3
          Power State 3 Relative Write Throughput (RWT)      3
          Power State 4 Active Power (ACTP)                  Not Reported
          Power State 4 Active Power Workload (APW)          No workload
          Power State 4 Entry Latency (ENLAT)                5,000 uS (0.005 sec)
          Power State 4 Exit Latency (EXLAT)                 39,000 uS (0.039 sec)
          Power State 4 Idle Power (IDLP)                    0.005 Watts
          Power State 4 Idle Time Prior to Transition (ITPT) Disabled
          Power State 4 Maximum Power (MP)                   0.005 Watts
          Power State 4 Non-Operational State (NOPS)         True
          Power State 4 Relative Read Latency (RRL)          4
          Power State 4 Relative Read Throughput (RRT)       4
          Power State 4 Relative Write Latency (RWL)         4
          Power State 4 Relative Write Throughput (RWT)      4
          Predictable Latency Event Log Change Notices       Not Supported
          Predictable Latency Mode                           Not Supported
          RTD3 Entry Latency (RTD3E)                         1,000,000 uS (1.000 sec)
          RTD3 Resume Latency (RTD3R)                        500,000 uS (0.500 sec)
          Read Recovery Levels                               Not Supported
          Read Recovery Levels Supported (RRLS)              0x0000
          Recommended Arbitration Burst (RAB)                4 (2^4=16)
          Reliability Degraded                               No
          Replay Protected Memory Blocks (RPMBS)             Not Supported
          Report ANA Change state                            Not Supported
          Report ANA Inaccessible state                      Not Supported
          Report ANA Non-Optimized state                     Not Supported
          Report ANA Optimized state                         Not Supported
          Report ANA Persistent Loss state                   Not Supported
          Required Completion Queue Entry Size               4 (2^4=16)
          Required Submission Queue Entry Size               6 (2^6=64)
          Reservations                                       Not Supported
          Root PCI Device ID                                 0xA340
          Root PCI Location                                  Bus 0, device 27, function 0
          Root PCI Vendor ID                                 0x8086
          SGL support in NVM command                         Not Supported
          SMART Critical Warning Notices Enable              0x00
          SMART/Health Log Page per Namespace                Not Supported
          SMBus Management Endpoint (SMBUSME)                Not Supported
          SQ Associations                                    Not Supported
          Save/Select Fields in Features Command             Supported
          Secure Erase All Namespaces                        Not Supported
          Security Send and Security Receive Command         Supported
          Self-Test 1 Power On Hours                         1,733
          Self-Test 1 Result                                 Passed
          Self-Test 1 Result Code                            0
          Self-Test 1 Type                                   Short Test
          Self-Test 10 Power On Hours                        1,685
          Self-Test 10 Result                                Passed
          Self-Test 10 Result Code                           0
          Self-Test 10 Type                                  Extended Test
          Self-Test 11 Power On Hours                        1,684
          Self-Test 11 Result                                Passed
          Self-Test 11 Result Code                           0
          Self-Test 11 Type                                  Extended Test
          Self-Test 12 Power On Hours                        1,684
          Self-Test 12 Result                                Passed
          Self-Test 12 Result Code                           0
          Self-Test 12 Type                                  Short Test
          Self-Test 13 Power On Hours                        1,684
          Self-Test 13 Result                                Passed
          Self-Test 13 Result Code                           0
          Self-Test 13 Type                                  Short Test
          Self-Test 14 Power On Hours                        1,665
          Self-Test 14 Result                                Passed
          Self-Test 14 Result Code                           0
          Self-Test 14 Type                                  Extended Test
          Self-Test 15 Power On Hours                        1,664
          Self-Test 15 Result                                Passed
          Self-Test 15 Result Code                           0
          Self-Test 15 Type                                  Extended Test
          Self-Test 16 Power On Hours                        1,663
          Self-Test 16 Result                                Passed
          Self-Test 16 Result Code                           0
          Self-Test 16 Type                                  Short Test
          Self-Test 17 Power On Hours                        1,663
          Self-Test 17 Result                                Passed
          Self-Test 17 Result Code                           0
          Self-Test 17 Type                                  Short Test
          Self-Test 18 Power On Hours                        1,578
          Self-Test 18 Result                                Passed
          Self-Test 18 Result Code                           0
          Self-Test 18 Type                                  Extended Test
          Self-Test 19 Power On Hours                        1,577
          Self-Test 19 Result                                Passed
          Self-Test 19 Result Code                           0
          Self-Test 19 Type                                  Extended Test
          Self-Test 2 Power On Hours                         1,706
          Self-Test 2 Result                                 Passed
          Self-Test 2 Result Code                            0
          Self-Test 2 Type                                   Extended Test
          Self-Test 20 Power On Hours                        1,577
          Self-Test 20 Result                                Passed
          Self-Test 20 Result Code                           0
          Self-Test 20 Type                                  Short Test
          Self-Test 3 Power On Hours                         1,705
          Self-Test 3 Result                                 Passed
          Self-Test 3 Result Code                            0
          Self-Test 3 Type                                   Extended Test
          Self-Test 4 Power On Hours                         1,704
          Self-Test 4 Result                                 Passed
          Self-Test 4 Result Code                            0
          Self-Test 4 Type                                   Short Test
          Self-Test 5 Power On Hours                         1,704
          Self-Test 5 Result                                 Passed
          Self-Test 5 Result Code                            0
          Self-Test 5 Type                                   Short Test
          Self-Test 6 Power On Hours                         1,704
          Self-Test 6 Result                                 Passed
          Self-Test 6 Result Code                            0
          Self-Test 6 Type                                   Extended Test
          Self-Test 7 Power On Hours                         1,702
          Self-Test 7 Result                                 Passed
          Self-Test 7 Result Code                            0
          Self-Test 7 Type                                   Extended Test
          Self-Test 8 Power On Hours                         1,702
          Self-Test 8 Result                                 Passed
          Self-Test 8 Result Code                            0
          Self-Test 8 Type                                   Short Test
          Self-Test 9 Power On Hours                         1,702
          Self-Test 9 Result                                 Passed
          Self-Test 9 Result Code                            0
          Self-Test 9 Type                                   Short Test
          Serial Number (SN)                                 2035A0805352
          Size                                               250 GB
          Size in GiB                                        232.9 GiB
          Subsystem Vendor                                   Sandisk
          Telemetry Log Notices                              Supported
          Telemetry Log Notices Enable                       Disabled
          Temperature Over/Under Threshold                   No
          Thermal Management Temperature 1 (TMT1)            Disabled
          Thermal Management Temperature 1 Count             0
          Thermal Management Temperature 1 Time              0 Sec
          Thermal Management Temperature 2 (TMT2)            Disabled
          Thermal Management Temperature 2 Count             0
          Thermal Management Temperature 2 Time              0 Sec
          Time Limited Error Recovery (TLER)                 No Timeout
          Timestamp                                          1,659,114,368,176 mS
          Timestamp Decoded                                  2022-07-29 10:06:08.176 DST
          Timestamp Feature                                  Supported
          Timestamp Origin                                   Host Programmed
          Timestamp Stopped                                  True
          Traffic Based Keep Alive Support                   Not Supported
          UUID List                                          Not Supported
          Unchanged ANAGRPID                                 Not Supported
          Unsafe Shutdowns                                   22
          Vendor Specific Command Configuration              Not Vendor Specific
          Verify NVM Command                                 Not Supported
          Version (VER)                                      1.4.0
          Virtualization Mgt Command                         Not Supported
          Volatile Backup Failed                             No
          Volatile Write Cache (VWC)                         Supported
          Volatile Write Cache Enable (WCE)                  Enabled
          Volatile Write Cache Flush All NSID                Supported
          Warning Composite Temperature Threshold (WCTEMP)   80 C
          Warning Composite Temperature Time                 49 Min
          Workload Hint (WH)                                 0
          Write Protect Namespace States                     Not Supported
          Write Protect Until Power Cycle                    Not Supported
          Write Uncorrectable NVM Command                    Supported
          Write Zeroes NVM Command                           Supported
          Time Throttled                                     3060
          Namespace 1 Active LBA Size                        512
</details>

<details>
  <summary>Example console output with --hex option (partial output only)</summary>

         This is only part of the console output since listing all of the data is impractical.

         ----------------------------------------------------------------------------------------------------------
          Identify Controller
         ----------------------------------------------------------------------------------------------------------
          0x0000  |  B7 15 B7 15 32 30 33 35  |  41 30 38 30 35 33 35 32        . . . . 2 0 3 5  |  A 0 8 0 5 3 5 2
          0x0010  |  20 20 20 20 20 20 20 20  |  57 44 43 20 57 44 53 32                         |  W D C   W D S 2
          0x0020  |  35 30 47 32 42 30 43 2D  |  30 30 50 58 48 30 20 20        5 0 G 2 B 0 C -  |  0 0 P X H 0
          0x0030  |  20 20 20 20 20 20 20 20  |  20 20 20 20 20 20 20 20                         |
          0x0040  |  32 31 31 30 37 30 57 44  |  04 44 1B 00 00 07 01 00        2 1 1 0 7 0 W D  |  . D . . . . . .
          0x0050  |  00 04 01 00 20 A1 07 00  |  40 42 0F 00 00 02 00 00        . . . .   . . .  |  @ B . . . . . .
          0x0060  |  02 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 01        . . . . . . . .  |  . . . . . . . .
          0x0070  |  00 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .
          0x0080  |  00 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .
          0x0090  |  00 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .
          0x00A0  |  00 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .
          0x00B0  |  00 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .
          0x00C0  |  00 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .
          0x00D0  |  00 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .
          0x00E0  |  00 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .
          0x00F0  |  00 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .
          0x0100  |  17 00 04 07 14 1E FF 04  |  01 01 61 01 66 01 32 00        . . . . . . . .  |  . . a . f . 2 .
          0x0110  |  00 C8 00 00 37 03 00 00  |  00 E0 B2 38 3A 00 00 00        . . . . 7 . . .  |  . . . 8 : . . .
          0x0120  |  00 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .
          0x0130  |  00 00 00 00 00 00 00 00  |  00 00 00 00 2C 00 01 01        . . . . . . . .  |  . . . . , . . .
          0x0140  |  00 00 01 00 11 01 66 01  |  02 00 00 60 00 00 00 00        . . . . . . f .  |  . . . ` . . . .
          0x0150  |  08 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .
          0x0160  |  01 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .
          0x0170  |  00 00 00 00 00 00 00 00  |  00 00 00 00 00 00 00 00        . . . . . . . .  |  . . . . . . . .

</details>
<br/>

## Check NVMe health

This console command checks NVMe health and wear by running the self-test diagnostic, reviewing SMART data and
self-test history.  This command must be run as Administrator on Windows OS.
```
checknvme  --nvme 0
```

This command displays detailed results to the console and creates a summary PDF report:

[Example report: report.pdf](https://raw.githubusercontent.com/jtjones1001/nvmetools/2ff9f4c3f2c6b7d41f57f01e299c6272fef21994/docs/examples/checknvme/report.pdf)

<br/>

## nvmetools

The nvmetools python package provides functionality to read and test NVMe drives within your own modules. The
nvmetools online documentation can be found on Read The Docs.

[Online Documentation](https://nvmetools.readthedocs.io/en/latest/)

<br/><br/>
