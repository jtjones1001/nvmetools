import os

from nvmetools.support.conversions import US_IN_MS, as_int
from nvmetools.support.info import Info


def report(report, test_result):

    report.add_description(
        """ This test measures the read latency for ASPM enabled and disabled.  ASPM is....
        <br/><br/>

        Read latency is determined by measuring the latency of the first IO
        read after an idle period long enough that the drive transitions to a lower
        ASPM state (L0s, L1, L1.1, L1.2).  Several samples are taken and the outliers are removed
        to avoid unrelated latency changes from OS interupts or drive accesses that take the
        drive out of idle.
        <br/><br/>
        """
    )
    report.add_results(test_result)

    report.add_paragraph(
        """The latency in the plot below is for the first read after the idle time for both ASPM
        enabled and disabled. """
    )

    report.add_verifications(test_result)
