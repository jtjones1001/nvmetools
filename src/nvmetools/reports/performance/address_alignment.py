# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
def report(report, test_result):

    report.add_description(
        f"""This test reports the read latency at different address offests to gather information about
            the device interleaving.  A total of {test_result['data']['max offset in 4kib']-1}
            address offsets are tested that are aligned on multiples of 4 KiB.  A total of
            {test_result['data']['total ios']:,} reads are completed at each offset. The first
            {test_result['data']['delayed ios']} reads of each offset are excluded from the latency
            calculation to avoid any influence from power state exit latencies.  A queue depth of
            {test_result['data']['queue depth']} with block size of
            {test_result['data']['block size kib']} KiB is used to saturate any specific
            IO path."""
    )
    report.add_results(test_result)
    report.add_paragraph(
        f"""This plot shows the latency of {test_result['data']['reported ios']:,} IO reads at each of the
        {len(test_result['data']['read latency us'])} different address offsets."""
    )
    report.add_plot(
        test_result["data"]["read latency us"].keys(),
        "Address Offset (KiB)",
        test_result["data"]["read latency us"].values(),
        "Latency (uS)",
        xticks=range(-1, test_result["data"]["max offset in 4kib"], 16),
        width=8,
    )
    report.add_verifications(test_result)
