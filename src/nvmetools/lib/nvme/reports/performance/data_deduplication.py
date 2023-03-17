# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------


def _format_row(io_type, data):
    """Format row to table in report function."""
    delta = data[f"{io_type} unique"] - data[f"{io_type} duplicate"]
    delta_percent = 100 * delta / data[f"{io_type} unique"]
    name = f"{io_type}"
    return [
        name,
        f"{data[ f'{io_type} unique']:.3f} mS",
        f"{data[ f'{io_type} duplicate']:.3f} mS",
        f"{delta:.3f} mS",
        f"{delta_percent:.1f}%",
    ]


def report(report, test_result):
    report.add_description(
        f""" This test attempts to determine if the drive implements data deduplication.  Data
        deduplication is a feature that reduces the amount of duplicate data written to the NAND
        flash resulting in lower write latency, extended drive life, and reduced garbage collection
        overhead.
        <br/><br/>

        This test reports the average latency for {test_result['data']['io size gib']} GiB of writes
        with repeating and non-repeating data. Drives with data deduplication should have much lower
        latency for the repeating data pattern.  The repeating data pattern uses the same
        psuedo-random pattern for every block. The non-repeating pattern uses a unique psuedo-random
        pattern every block.  For example, the repeating pattern is a psuedo-random data pattern
        that is 4 KiB in size when the block size is 4 KiB.
        <br/><br/>

        The writes are completed with a queue depth of 1 and block sizes of 4 KiB, 8 KiB, 32 KiB,
        and 128 KiB. Different block sizes are tried because any data deduplication chunk size is
        unknown."""
    )
    report.add_results(test_result)

    report.add_subheading2("Write Latency vs Data Repeatability")
    table_rows = [["IO PATTERN", "NONREPEATING", "REPEATING", "DELTA", "% DELTA"]]
    for block_size in test_result["data"]["block sizes"]:
        table_rows.append(_format_row(f"Sequential Write, {block_size} KiB, QD1", test_result["data"]))
    report.add_table(table_rows, [160, 90, 90, 90, 70])

    report.add_verifications(test_result)
