# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Test suite to measure NVMe IO performance.

Measures IO peformance for several conditions including short and long bursts of reads
and writes.
"""
from nvmetools import TestSuite, fio, tests

with TestSuite("Performance Test", __doc__) as suite:

    info = tests.suite_start_info(suite)

    tests.short_burst_performance(suite)
    tests.long_burst_performance(suite)
    tests.idle_latency(suite)
    tests.data_deduplication(suite)
    tests.read_buffer(suite)

    if fio.space_for_big_file(info, suite.volume):

        tests.big_file_writes(suite)
        tests.big_file_reads(suite)
        tests.data_compression(suite)

        tests.short_burst_performance_full(suite)
        tests.long_burst_performance_full(suite)

    tests.suite_end_info(suite, info)
