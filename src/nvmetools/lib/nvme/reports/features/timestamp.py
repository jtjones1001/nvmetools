# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
def report(report, test_result):

    report.add_description(
        """Timestamp Feature Identifier 0Eh is an optional feature that reports the number
        of milliseconds that have elapsed since the epoch: midnight, 01-Jan-1970, UTC.  The
        timestamp is set to the current time by the host and then the drive increments the
        timestamp every millisecond.  The test reads the Get Feature data structure to get
        the timestamp info and verify the timestamp has been set by the host and matches
        the current time.
        <br/><br/>

        On some drives, the timestamp may stop under some conditions such as entering
        into non-operational power states. This test verifies the timestamp has not stopped
        by reading the synch attribute in the Get Feature data structure.
        <br/><br/>

        The test samples the host and drive timestamps every second for several minutes of idle
        and IO traffic.  This verifies the drive timestamp is accurate in multiple power states
        which is especially important since some stop in non-operational states.
        <br/><br/>

        This test uses the host timestamp as the reference.  Therefore, any issues with the host
        timestamp may cause this test to fail."""
    )
    report.add_results(test_result)

    data = test_result["data"]
    if data["timestamp supported"] is False:
        report.add_paragraph("""The drive does not support the optional Timestamp (Feature Identifier 0Eh).""")
        return

    if data["start stopped"] == "True" or data["end stopped"] == "True":
        report.add_paragraph(
            """The timestamp synch attribute in the Get Feature data structure was set indicating
            the timestamp has stopped and may not be valid."""
        )

    table_rows = [
        ["PARAMETER", "HOST", "DRIVE", "DELTA", "LIMIT"],
        [
            "Starting Timestamp",
            f"{data['start drive timestamp']:,} mS",
            f"{data['start host timestamp']:,} mS",
            f"{data['start delta hrs']:.1f} hrs",
            f"{data['Timestamp Absolute Hours']} hrs",
        ],
        [
            "Timestamp Change",
            f"{data['host change']:,} mS",
            f"{data['drive change']:,} mS",
            f"{data['percentage error']:.2f}%",
            f"{data['Timestamp Relative Percent']}%",
        ],
    ]
    report.add_table(table_rows, [150, 125, 125, 50, 50])
    report.add_paragraph(
        f"""The plot below shows the linearity between the drive and host timestamps.  The
        measured Pearson product-moment correlation coefficent was: {data['linearity']:.3f}.
        Anything less than 0.99 indicates the host and drive timestamps do not track as
        expected.  If the tracking is erratic it can be cross-referenced againt the power
        states in the second plot."""
    )
    report.add_plot(data["host"], "Host Time (Sec)", data["drive"], "Drive Time (Sec)", height=2)
    report.add_paragraph("<br/><br/>")
    report.add_plot(data["host"], "Host Time (Sec)", data["power states"], "Power State", height=2)

    report.add_verifications(test_result)
