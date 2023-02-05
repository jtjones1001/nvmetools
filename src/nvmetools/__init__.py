# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
""" nvmetools package for reading information and testing NVMe drives.

This package uses the following:
   - black formatter with the wider line length defined in pyproject.toml
   - flakeheaven linter with custom settings defined in pyproject.toml

To disable pycache...
   export PYTHONDONTWRITEBYTECODE=1

To create a package:
   Update version in both pyproject.toml and docs/conf.py
   find . -name ".DS_Store" -delete -print  (OS-X only)
   python3 -m build
   twine upload -r testpypi dist/* or twine upload dist/*

To update the Read The Docs (RTD) documentation (https://readthedocs.org):
   - update the files in docs directory and RTD will build the documentation when checked into github
   - Documentation location:  https://nvmetools.readthedocs.io/en/latest/
   - To test build the documentation
       sphinx-build -b html docs docs/build/html, then open
     docs/build/html/index.html in browser
   - See...
      - The Google Docstring format.  Style Guide:  http://google.github.io/styleguide/pyguide.html
      - Sphinx extension: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

To change firefox view mode for PDF report:
   about:config, pdfjs.defaultZoomValue to page-fit

To install fio:
   Fedora:  sudo yum -y install fio
   Ubuntu:  sudo apt -y install fio

"""
import os
from importlib.metadata import metadata

__copyright__ = "Copyright (C) 2023 Joe Jones"
__brandname__ = "EPIC NVMe Utilities"
__website__ = "www.epicutils.com"
__package_name__ = "nvmetools"

try:
    __version__ = metadata("nvmetools")["Version"]
except Exception:
    __version__ = "N/A"

TEST_SUITE_DIRECTORY = os.path.expanduser("~/Documents/nvmetools/suites")
TEST_RESULT_DIRECTORY = os.path.expanduser("~/Documents/nvmetools/results")
USER_INFO_DIRECTORY = os.path.expanduser("~/Documents/nvmetools/drives")

PACKAGE_DIRECTORY = os.path.dirname(__file__)
SRC_DIRECTORY = os.path.split(PACKAGE_DIRECTORY)[0]
TOP_DIRECTORY = os.path.split(SRC_DIRECTORY)[0]
RESOURCE_DIRECTORY = os.path.join(PACKAGE_DIRECTORY, "resources")
DEFAULT_INFO_DIRECTORY = os.path.join(RESOURCE_DIRECTORY, "drives")
RESULTS_FILE = "result.json"

import nvmetools.requirements as rqmts
import nvmetools.apps.fio as fio

from nvmetools.support.log import log
from nvmetools.support.info import Info, InfoSamples
from nvmetools.support.framework import TestCase, TestStep, TestSuite

import nvmetools.steps as steps
import nvmetools.cases as tests
