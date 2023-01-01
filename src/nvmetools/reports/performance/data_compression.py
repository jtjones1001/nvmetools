# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------


def _format_row(io_pattern, data):
    """Format row to table in report function."""
    delta = data[f"{io_pattern} random"] - data[f"{io_pattern} zero"]
    delta_percent = 100 * delta / data[f"{io_pattern} random"]
    return [
        io_pattern,
        f"{data[ f'{io_pattern} zero']:.3f} mS",
        f"{data[ f'{io_pattern} random']:.3f} mS",
        f"{delta:.3f} mS",
        f"{delta_percent:.1f}%",
    ]


def report(report, test_result):
    report.add_description(
        f"""This test attempts to determine if the drive implements data compression.  Data
        compression is a feature that reduces the amount of data written to the NAND flash resulting
        in lower write latency, extended drive life, and reduced garbage collection overhead.
        <br/><br/>
        This test reports the average latency for {test_result['data']['io size gib']} GiB of reads
        and writes with incompressible and compressible data. Drives with data compression should
        have lower latency for the compressible data pattern.  The compressible data pattern is all
        0s. The incompressible data pattern is a unique psuedo-random pattern every write.  The read
        and writes are completed with a queue depth of 1, block size of 8 KiB for random addressing,
         and block size of 128 KiB for sequential addressing."""
    )
    report.add_results(test_result)

    report.add_subheading2("IO Latency vs Data Compressibility")
    table_rows = [
        ["IO PATTERN", "COMPRESSIBLE", "INCOMPRESSIBLE", "DELTA", "% DELTA"],
        _format_row("Random Write, 8 KiB, QD1", test_result["data"]),
        _format_row("Random Read, 8 KiB, QD1", test_result["data"]),
        _format_row("Sequential Write, 128 KiB, QD1", test_result["data"]),
        _format_row("Sequential Read, 128 KiB, QD1", test_result["data"]),
    ]
    report.add_table(table_rows, [160, 100, 100, 70, 70])

    report.add_verifications(test_result)
