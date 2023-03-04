# Changelog

## v0.7.0

### Improvements
- Overhauled the html report from viewnvme/testnvme/checknvme
- Updated parameters relevant to NVMe health

### For developers
- Updated nvmecmd version with parameter changes for health and bug fix for feature reads

## v0.6.0

### Improvements
- Removed pycache and hidden OS files from the build
- Updated nvmecmd to version that supports sanitize
- Changed testnvme so user can easily add their own test suites
- Updated big file write test case

### For developers
- Split out test suites into separate files

## v0.5.0

 Added viewnvme command.  Several bug fixes and improvements in the test cases and reporting.

### Improvements
- Added viewnvme command
- Improvements and bug fixes in the html resources
- Bug fixes in the test cases, reporting, and framework


## v0.4.3

 Updated to support PCIe gen4/5 devices, several bug fixes in framework to stop on fail

### Improvements
- Updated nvmecmd to version that supports PCIe gen4/5 speed
- Set read default to exclude log pages 7/8 because they can be too big
- Bug fixes in framework for stop and stop on fail options

## v0.4.2

Added fixes for bugs found through initial testing and updated test cases to be more consistent and
simple

### Improvements
- Replaced aspm_latency and nonop_latency test cases with idle_latency
- Test Case improvements to make them more consistent and simpler
- Bug fix for issue where compare fails when new parameters added during a test suite
- Added check for free disk space in test suites that require full drive testing

## v0.4.1

Initial public release of new format.  This is a beta release with limited testing and is posted
primarily to gather feedback.

### Improvements
- Added test framework for testing NVMe devices
- Added html dashboard of test results

### For developers
- The prior release 0.2.1 was renamed to nvmetools-original-version and is available on github

