READ_SIZE = 4096
PAGE_SIZE = 4096 * 4
BLOCK_SIZE = 256 * PAGE_SIZE
ADDRESS_INCREMENT = BLOCK_SIZE * 16


def report(report, test_result):

    report.add_description(
        f""" Read disturb occurs in flash chips
        when a page read disturbs the voltage of other cells within the same block [13].
        The more times a page is read, the more the voltage of neighbor cells may change.  This test
        attempts to verify design mitigations that prevent read disturb from causing functional failures.
        However, since the physical layout and mapping of the drive are unknown it is not possible to
        guarantee the mitigations are tested.
        <br/><br/>

        The test first creates a file using large block sequential writes.  The file
        is written twice to increase the odds that "new" blocks are used and only contain pages with data
        from the file.
        <br/><br/>

        The test then reads 4096 bytes at increments of {int(ADDRESS_INCREMENT/1024/1024)} MiB.   The
            large increment should ensure that only one page per block is read.  The test loops through the file
            several thousand times reading the same pages over and over.  After several thousand loops the test
            reads all of the pages in the file to verify no pages have been disturbed.
        <br/><br/>"""
    )

    report.add_results(test_result)

    data = test_result["data"]
    table_data = [
        ["FILE SIZE", "READ INCREMENT", "PAGES PER FILE", "READS PER PAGE"],
        [
            f"{data['file size gb']:.0f} GB",
            f"{int(ADDRESS_INCREMENT/1024/1024)} MiB",
            f"{int(data['pages per file'])}",
            f"{int(data['reads per page']):,}",
        ],
    ]
    report.add_table(table_data, [125, 125, 125, 125])

    report.add_verifications(test_result)
