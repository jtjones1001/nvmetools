# Changelog

## v0.4.3

 Updated to support PCIe gen4/5 devices

### Improvements
- Updated nvmecmd to version that supports PCIe gen4/5 speed
- Set read default to exclude log pages 7/8 because they can be too big

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

