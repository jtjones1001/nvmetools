# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
from nvmetools import TestCase, TestStep, rqmts, steps
from nvmetools.cases.performance.long_burst_lib import _run_burst


def long_burst_performance(suite):
    """Measure performance of long bursts of IO reads and writes.

    Runs a long burst of IO on the volume specified.  This burst consists of:
      1) idle time to ensure device temperature and activity is stable
      2) read or write IO using fio
      3) idle to ensure device return to idle temperature

    The volume provided (volume) must exist on the physical device provided (nvme).

    Args:
        suite:  Parent TestSuite instance
    """
    with TestCase(suite, "Long Burst Performance", long_burst_performance.__doc__) as test:

        test.data["limits"] = suite.device["Long Burst Bandwidth (GB/s)"]
        test.data["random block size"] = RANDOM_BLOCK_SIZE = 4096
        test.data["random queue depth"] = RANDOM_QUEUE_DEPTH = 1
        test.data["sequential block size"] = SEQ_BLOCK_SIZE = 128 * 1024
        test.data["sequential queue depth"] = SEQ_QUEUE_DEPTH = 32

        # -----------------------------------------------------------------------------------------
        # Before test, read NVMe info and verify no critical warnings, get fio file, wait for idle
        # -----------------------------------------------------------------------------------------
        start_info = steps.test_start_info(test)
        fio_file = steps.get_fio_performance_file(test)
        steps.wait_for_idle(test)

        # -----------------------------------------------------------------------------------------
        # Multiple Steps : Run the bursts with the target IO types
        # -----------------------------------------------------------------------------------------
        for rwmix in [0, 100]:
            _run_burst(
                test,
                suite.nvme,
                suite.volume,
                fio_file,
                "randrw",
                RANDOM_BLOCK_SIZE,
                RANDOM_QUEUE_DEPTH,
                rwmix,
                1,
            )
        for rwmix in [0, 100]:
            _run_burst(
                test,
                suite.nvme,
                suite.volume,
                fio_file,
                "rw",
                SEQ_BLOCK_SIZE,
                SEQ_QUEUE_DEPTH,
                rwmix,
                1,
            )
        # -----------------------------------------------------------------------------------------
        # Verify performance within limits
        # -----------------------------------------------------------------------------------------
        with TestStep(test, "Verify performance", "Verify long burst performance.") as step:

            rqmts.random_read_4k_qd1_bandwidth(step, test.data, burst_type="Long")
            rqmts.random_write_4k_qd1_bandwidth(step, test.data, burst_type="Long")
            rqmts.sequential_read_128k_qd32_bandwidth(step, test.data, burst_type="Long")
            rqmts.sequential_write_128k_qd32_bandwidth(step, test.data, burst_type="Long")
            rqmts.review_io_bandwidth(step)

        # -----------------------------------------------------------------------------------------
        # After test, read NVMe info and compare against the starting info
        # -----------------------------------------------------------------------------------------
        steps.test_end_info(test, start_info)
