
from nvmetools.apps.fio import check_fio_installation
from nvmetools.apps.nvmecmd import check_nvmecmd_permissions
from nvmetools.lib.nvme.reporter import create_reports
from nvmetools.support.framework import TestSuite


class NvmeTestSuite(TestSuite):

    def __enter__(self):
        self.reporter = create_reports

        super().__enter__()

        check_nvmecmd_permissions()
        check_fio_installation()
        self.get_drive_specification()

        return self
