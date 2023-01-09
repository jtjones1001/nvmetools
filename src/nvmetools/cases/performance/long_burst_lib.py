# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
import csv
import os
import time

from nvmetools import InfoSamples, TestStep, fio, rqmts
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

    title = f"{access_type.title()} {rdwr}"
    description = f"Start reading NVMe information for {access_type} {rdwr}, size={bs}, depth={qd}"

    with TestStep(test, title, description) as step:

        info_samples = InfoSamples(
            nvme,
            directory=os.path.join(step.directory, "sample_info"),
            wait=False,
            samples=100000,
            interval=1000,
            cmd_file="state",
        )
        time.sleep(BURST_WAIT_SEC)

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
        fio_result = fio.RunFio(args=fio_args, directory=step.directory, volume=volume)

        time.sleep(BURST_END_SEC)

        info_samples.stop()
        fio_result.split_log("bandwidth_bw.1.log")

        rqmts.no_counter_parameter_decrements(step, info_samples)
        rqmts.no_errorcount_change(step, info_samples)
        rqmts.no_io_errors(step, fio_result)

        start_temp = as_int(info_samples._first_sample.parameters["Composite Temperature"])
        end_temp = as_int(info_samples._last_sample.parameters["Composite Temperature"])
        delta_temperature = end_temp - start_temp

        rqmts.idle_temperature_delta(step, delta_temperature)

        start_throttle = as_int(info_samples._first_sample.parameters["Seconds Throttled"])
        end_throttle = as_int(info_samples._last_sample.parameters["Seconds Throttled"])
        throttle_sec = end_throttle - start_throttle

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
            "io start temperature": start_temp,
            "end temperature": end_temp,
            "delta temperature": f"{delta_temperature} C",
            "max temperature": f"{max(temp)} C",
        }
