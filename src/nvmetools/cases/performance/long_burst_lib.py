import csv
import os
import time

from nvmetools import Info, InfoSamples, TestCase, TestStep, log, rqmts, steps
from nvmetools.apps.fio import FioFiles, RunFio
from nvmetools.support.conversions import BYTES_IN_GB, KIB_TO_GB, MS_IN_SEC, as_int


def _run_burst(test, nvme, volume, fio_file, access, bs, qd, rwmix, jobs):
    """Run a long burst of a specific IO type (read/write, random/seq)."""
    if access == "rw":
        access_type = "sequential"
    else:
        access_type = "random"

    if rwmix == 100:
        rdwr = "read"
    elif rwmix == 0:
        rdwr = "write"
    else:
        rdwr = "read_write"

    io_pattern = f"{access_type} {rdwr}"

    # build a unique descriptor to use for test description, the name is a shorter
    # version better suited for directory names

    burst_descriptor = f"{access_type} {rdwr}, size={bs}, depth={qd}"

    if jobs == 1:
        name = f"{access_type}_{rdwr}"
        friendly_name = f"{access_type.title()} {rdwr.title()}, QD{qd}, {int(bs/1024)}KiB"
    else:
        name = f"mt_{access_type}_{rdwr}"
        friendly_name = f"MT {access_type.title()} {rdwr.title()}, QD{qd}, {int(bs/1024)}KiB"

    test.data["io sample ms"] = IO_SAMPLE_MS = 200  # time in mS for fio to sample bandwidth
    test.data["end bw time sec"] = END_BW_TIME_SEC = 120  # sample time at end of burst
    test.data["burst wait sec"] = BURST_WAIT_SEC = 120
    test.data["io runtime sec"] = IO_RUNTIME_SEC = 600
    test.data["burst end sec"] = BURST_END_SEC = 1800

    with TestStep(
        test, f"{access_type.title()} {rdwr}", f"Start reading NVMe information for {burst_descriptor}"
    ) as step:

        # Take the first reading

        start_io_directory = os.path.join(step.directory, "start_info")
        start_info = Info(nvme, directory=start_io_directory)
        rqmts.no_critical_warnings(step, start_info)

        # Start reading information every second.  Use large sample so runs until stopped at end
        # of test.  This data can be used to plot temp, BW, etc during the tests.  It also verifies
        # static and counter parameters every second

        info_samples = InfoSamples(
            nvme,
            directory=os.path.join(step.directory, "info"),
            wait=False,
            samples=100000,
            interval=1000,
            cmd_file="state",
        )

        #  Collect some data at start of IO so get idle temperature

        time.sleep(BURST_WAIT_SEC)

        # Run fio with given workload, note this test does not verify data integrity.  The test
        # does log average bandwidth so can be plotted for the report

        fio_args = [
            "--direct=1",
            "--thread",
            f"--numjobs={jobs}",
            f"--filesize={fio_file.file_size}",
            f"--filename={fio_file.filepath}",
            f"--offset_increment={1024*1024*1024/jobs:.0f}",
            "--group_reporting",
            f"--rw={access}",
            f"--iodepth={qd}",
            f"--bs={bs}",
            f"--rwmixread={rwmix}",
            f"--size={1024*1024*1024/jobs:.0f}",
            f"--output={os.path.join(step.directory,'fio.json')}",
            "--output-format=json",
            "--time_based",
            "--write_bw_log=bandwidth",
            f"--log_avg_ms={IO_SAMPLE_MS}",
            f"--runtime={IO_RUNTIME_SEC}",
            "--name=fio",
        ]
        fio_result = RunFio(args=fio_args, directory=step.directory, volume=volume)

        # after fio completes wait for idle

        time.sleep(BURST_END_SEC)

        # stop collecting the nvme information and verify the data, create files with
        # temperature and bandwidth data to be plotted for the report

        info_samples.stop()
        rqmts.no_counter_parameter_decrements(step, info_samples)
        rqmts.no_errorcount_change(step, info_samples)

        rqmts.no_io_errors(step, fio_result)

        fio_result.split_log("bandwidth_bw.1.log")

        # Take one last reading and compare against the first reading to verify
        # no errors or throttling

        end_info = Info(nvme=nvme, directory=os.path.join(step.directory, "end_info"), compare_info=start_info)

        rqmts.no_critical_warnings(step, end_info)
        rqmts.no_errorcount_change(step, end_info)
        rqmts.no_static_parameter_changes(step, end_info)
        rqmts.no_counter_parameter_decrements(step, end_info)

        # Check temperature at start of IO and at the end to verify drive returns to idle temperature

        delta_temperature = as_int(end_info.parameters["Composite Temperature"]) - as_int(
            start_info.parameters["Composite Temperature"]
        )

        rqmts.idle_temperature_delta(step, delta_temperature)

        throttle_sec = as_int(end_info.parameters["Seconds Throttled"]) - as_int(
            start_info.parameters["Seconds Throttled"]
        )
        test.data[io_pattern] = {"results": {f"{qd}": {f"{bs}": None}}}
        if rdwr == "read":
            bandwidth = fio_result.logfile["jobs"][0]["read"]["bw_bytes"] / BYTES_IN_GB
            bandwidth_csv_file = os.path.join(step.directory, "bandwidth_read.csv")
            bw = fio_result.read_bw_kib * KIB_TO_GB
            lat = fio_result.read_mean_latency_ms
            test.data[io_pattern]["results"][f"{qd}"][f"{bs}"] = {
                "lat": lat,
                "bw": bw,
                "iops": bw / bs,
            }
        else:
            bandwidth = fio_result.logfile["jobs"][0]["write"]["bw_bytes"] / BYTES_IN_GB
            bandwidth_csv_file = os.path.join(step.directory, "bandwidth_write.csv")

            bw = fio_result.write_bw_kib * KIB_TO_GB
            lat = fio_result.write_mean_latency_ms

            test.data[io_pattern]["results"][f"{qd}"][f"{bs}"] = {
                "lat": lat,
                "bw": bw,
                "iops": bw / bs,
            }

        temp = []
        start_bandwidth = {1: None, 5: None, 10: None, 15: None}

        end_bandwidth = []

        end_sample_time = IO_RUNTIME_SEC - END_BW_TIME_SEC

        with open(bandwidth_csv_file, "r", newline="") as file_object:
            bandwidth_data = csv.reader(file_object)
            for index, row in enumerate(bandwidth_data):

                for seconds in [1, 5, 10, 15]:
                    if (start_bandwidth[seconds] is None) and (float(row[0]) / MS_IN_SEC) >= seconds:
                        start_bandwidth[seconds] = (float(row[2]) * KIB_TO_GB) / (index + 1)

                if (float(row[0]) / MS_IN_SEC) > end_sample_time:
                    end_bandwidth.append(float(row[1]) * KIB_TO_GB)

        for sample in info_samples.summary["read details"]["sample"]:
            temp.append(as_int(sample["Composite Temperature"]))

        # read in the bandwidth file to get start and end bandwidth

        test.data.setdefault("bursts", {})
        test.data["bursts"][friendly_name] = {
            "directory": name,
            "bandwidth": bandwidth,
            "1 second bandwidth": start_bandwidth[1],
            "5 second bandwidth": start_bandwidth[5],
            "10 second bandwidth": start_bandwidth[10],
            "15 second bandwidth": start_bandwidth[15],
            "end bandwidth": sum(end_bandwidth) / len(end_bandwidth),
            "throttle time": throttle_sec,
            "io start temperature": start_info.parameters["Composite Temperature"],
            "end temperature": end_info.parameters["Composite Temperature"],
            "delta temperature": f"{delta_temperature} C",
            "max temperature": f"{max(temp)} C",
        }
