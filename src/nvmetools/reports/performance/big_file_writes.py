# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import os

from nvmetools.support.conversions import BYTES_IN_GB


def report(report, test_result):

    data = test_result["data"]
    test_dir = os.path.join(report._results_directory, test_result["directory name"])

    report.add_description(
        """This test measures IO bandwidth while continuously writing a big file with high queue
        depth, large block, sequential writes.  Continuous write bandwidth can identify the
        performance of features such as write caching, logical to physical mapping, erased block
        starvation, and thermal throttling.
        <br/><br/>

        The test starts with an less than 5% space used and creates a big file by continuously
        writing it several times.  During the first write the logical addresses are
        "new" and may not be cached.  If the logical to physical mapping is read from the NAND flash
        instead of the host or device DRAM the first write bandwidth maybe lower.
        <br/><br/>

        Drives with a write cache, such as SLC cache, will have much higher bandwidth at the start
        of the writes but, when the write cache fills up, the bandwidth drops significantly.  The
        continuous writes will likely prevent the cache from being flushed.  Some drives dynamically
        adjust the size of the write cache based on the amount of free space.  The free space
        on the first write is >95% but on subsequent writes the free space is <5%.  Therefore the
        write cache size may appear to decrease after the first write.
        <br/><br/>

        After the initial file write, the test waits a significant amount of time to allow the
        write cache to be flushed. The big file is read once more but starting at the 50% offset
        of the file.   If the write cache was flushed as expected the initial bandwidth will be
        much higher even though the writes are starting at the midpoint of the file.
        <br/><br/>

        The test then runs several write bursts with varying amounts of idle time between them. The
        different idle times between bursts can identify how fast the write cache is flushed. """
    )

    report.add_results(test_result)
    report.add_paragraph(
        f""" The file size tested was {data['file size']/BYTES_IN_GB:0,.1f} GB which is
        {data['file ratio']:0.0f}% of the disk size of {data['disk size']/BYTES_IN_GB:0,.1f} GB.
        The continuous writes used sequential addressing, block size of {data['block size kib']}KiB,
        and queue depth of {data['queue depth']}."""
    )
    report.add_subheading2("Initial File Writes")
    step_directory = os.path.join(test_dir, "5_sample_info")
    report.add_paragraph(
        f"""The big file was written {data['multiple file writes']} times for a total of
        {data['io size']/BYTES_IN_GB:0.1f} GB. The average bandwidth was
        {data['bw']['continuous']/BYTES_IN_GB:0.2f} GB.  The plots below show the write bandwidth
        and temperature during the multiple file writes.  The vertical red lines indicate the start
        of the file.
        <br/><br/>

        If a write cache exists, verify the initial bandwidth is higher than the average indicating
        the writes are going to the cache."""
    )
    report.add_bigfile_write_plot(step_directory, data["file size"])
    report.add_temperature_plot(step_directory)

    report.add_subheading2("Half File Write")
    step_directory = os.path.join(test_dir, "10_sample_info")
    report.add_paragraph(
        """The plots below shows the write bandwidth and temperature for writing the second half
        of the big file after a long delay.  The long delay allows the write cache to flush so the
        next writes are high bandwidth.  These writes began at the 50% offset of the file and
        continue to the end of the file.
        <br/><br/>

        If write cache exists, verify the initial bandwidth is higher than the average indicating
        the writes are going to the cache."""
    )

    report.add_bigfile_write_plot(step_directory, data["file size"], offset=0.5)
    report.add_temperature_plot(step_directory)

    report.add_pagebreak()
    report.add_subheading2("Write Cache Info")
    report.add_paragraph(
        """In the bandwidth plots above, writes with a bandwidth greater then twice the average are
        assumed to be going to the write cache.  The table below summarizes the measured write
        cache size and bandwidth based on this assumption.
        <br/><br/>
        Verify any average bandwidth difference between file writes is acceptable.
        """
    )
    table_data = [["File Write", "Data Written", "Average Bandwidth", "Cache Written", "Cache Bandwidth"]]

    for write in data["file writes"]:
        table_data.append(
            [
                write["number"],
                f"{write['data']:0,.1f} GB",
                f"{write['bw']:0,.3f} GB/s",
                f"{write['cache data']:0,.1f} GB",
                f"{write['cache bw']:0,.3f} GB/s",
            ]
        )
    report.add_table(table_data, [75, 100, 100, 100, 100])
    report.add_subheading2("Cache Size Burst Writes")

    report.add_paragraph(
        f"""Several cache size burst writes were completed with varying amount of idle time before
        the bursts.  This idle time allows drive to flush the write cache  Each burst was
        {data['write cache size']/BYTES_IN_GB} GB.  Writes with a bandwidth above
        {data['write cache limit']:0,.3f} GB/s were assumed to be going to the write cache.
        """
    )
    table_data = [["Burst", "Pre-Burst Idle", "Average Bandwidth", "Cache Written", "Cache Bandwidth"]]

    for burst in data["bursts"]:
        table_data.append(
            [
                burst["number"],
                f"{burst['delay']} sec",
                f"{burst['bw']:0,.3f} GB/s",
                f"{burst['cache data']:0,.1f} GB",
                f"{burst['cache bw']:0,.3f} GB/s",
            ]
        )
    report.add_table(table_data, [75, 100, 100, 100, 100])

    report.add_verifications(test_result)
