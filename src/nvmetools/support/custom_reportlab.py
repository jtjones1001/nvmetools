# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Custom reportlab flowables used to create PDF test reports."""

# flake8: noqa

import cycler
import datetime
import functools
import io
import os
import time

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox

import numpy

from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, Image, Paragraph, SimpleDocTemplate, TableStyle

from nvmetools import RESOURCE_DIRECTORY, __brandname__, __website__
from nvmetools.support.log import log

SKIPPED = "SKIPPED"
PASSED = "PASSED"
FAILED = "FAILED"
ABORTED = "ABORTED"
STARTED = "STARTED"

# ----------------------------------------------------------------------
# customize defaults
# ----------------------------------------------------------------------
# TODO:  RTD fails these commands, check into this some more
try:
    mpl.rcParams.update({"font.size": 8})
    mpl.rcParams["savefig.dpi"] = 300
    mpl.rcParams["grid.linewidth"] = 0.5
    mpl.rcParams["axes.grid"] = True
    mpl.rcParams["axes.prop_cycle"] = cycler.cycler(color=["#0f67a4", "#ff8f1e", "#009f40", "#707070", "#ea5545"])
except:
    pass
# ----------------------------------------------------------------------
# report page dimensions
# ----------------------------------------------------------------------
REPORT_DPI = 72
PAGE_WIDTH = 8.5 * REPORT_DPI
PAGE_HEIGHT = 11.0 * REPORT_DPI

FRAME_PAD = 6
H_MARGIN = 54 - FRAME_PAD
V_MARGIN = 54 - FRAME_PAD

USABLE_WIDTH = PAGE_WIDTH - 2 * (H_MARGIN + FRAME_PAD)
USABLE_HEIGHT = PAGE_HEIGHT - 2 * (V_MARGIN + FRAME_PAD)
# ----------------------------------------------------------------------
# report text styles
# ----------------------------------------------------------------------
HEADING_COLOR = "#0F2864"
TEXT_COLOR = "#303030"
PASS_COLOR = "#2ca02c"  # noqa
FAIL_COLOR = "#d62728"
SKIP_COLOR = "#808080"
LIMIT_COLOR = "#fd625e"

TEXT_FONT_SIZE = 10
TABLE_FONT_SIZE = 9


HEADING_STYLE = ParagraphStyle(
    "heading",
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=16,
    spaceBefore=0,
    spaceAfter=0,  # 16
    textColor=HEADING_COLOR,
    underlineWidth=2,
    underlineOffset=6,
)
TEXT_STYLE = ParagraphStyle(
    "text",
    fontName="Helvetica",
    fontSize=TEXT_FONT_SIZE,
    alignment=4,
    spaceAfter=8,
    textColor=TEXT_COLOR,
)
FAIL_TABLE_TEXT_STYLE = ParagraphStyle(
    "fail",
    fontName="Helvetica-BOLD",
    fontSize=TABLE_FONT_SIZE,
    alignment=4,
    spaceAfter=8,
    textColor="red",
)
SUBHEADING2_STYLE = ParagraphStyle(
    "subheading2", parent=TEXT_STYLE, fontName="Helvetica-Bold", textColor=HEADING_COLOR
)
SUBHEADING_STYLE = ParagraphStyle(
    "subheading",
    fontName="Helvetica-Bold",
    fontSize=11,
    spaceBefore=16,
    spaceAfter=6,
    textColor=HEADING_COLOR,
)

# ----------------------------------------------------------------------
# reportlab table configuration
# ----------------------------------------------------------------------
TABLE_HEADER_COLOR = "#3f87b4"
TABLE_HEADER_TEXT_COLOR = "#ffffff"
TABLE_ROW_GRAY_COLOR = "#e8e8e8"
TABLE_GRID_COLOR = "#888888"
TABLE_HEADER_GRID_COLOR = "#303030"

TABLE_TEXT_STYLE = ParagraphStyle(
    "table",
    fontName="Helvetica",
    fontSize=TABLE_FONT_SIZE,
    alignment=4,
    spaceAfter=8,
    textColor=TEXT_COLOR,
)
TABLE_STYLE = TableStyle(
    [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_COLOR),
        ("GRID", (0, 1), (-1, -1), 1, TABLE_GRID_COLOR),
        ("GRID", (0, 0), (-1, 0), 1, TABLE_HEADER_GRID_COLOR),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, 0), TABLE_HEADER_TEXT_COLOR),
        ("TOPPADDING", (0, 0), (-1, 0), 4),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), TABLE_FONT_SIZE),
        ("LEADING", (0, 0), (-1, -1), TABLE_FONT_SIZE * 1.2),
    ]
)
TABLE_STYLE_NO_HEADER = TableStyle(
    [
        ("GRID", (0, 0), (-1, -1), 1, TABLE_GRID_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), TABLE_FONT_SIZE),
        ("LEADING", (0, 0), (-1, -1), TABLE_FONT_SIZE * 1.2),
    ]
)


def _add_header_footer(canvas, doc, drive_name):
    hdr_ftr_font_size = 8

    x1 = H_MARGIN + FRAME_PAD
    x2 = PAGE_WIDTH - H_MARGIN - FRAME_PAD
    y1 = PAGE_HEIGHT - V_MARGIN + 12
    y2 = V_MARGIN - hdr_ftr_font_size - 12

    short_date = time.strftime("%b %d, %Y")

    canvas.saveState()
    canvas.setFont("Helvetica", hdr_ftr_font_size)
    canvas.drawString(x1, y1, "Epic NVMe Utilities")
    canvas.drawRightString(x2, y1, f"{drive_name}")
    canvas.drawString(x1, y2, short_date)
    canvas.drawRightString(x2, y2, "Page %d" % doc.page)
    canvas.restoreState()


def convert_plot_to_image(fig, ax, ax2=None):
    """Convert matplotlib plot to reportlab image."""
    plot_width, plot_height = fig.get_size_inches()

    actual_x0 = ax.get_tightbbox(fig.canvas.get_renderer()).x0 / fig.dpi
    actual_y0 = ax.get_tightbbox(fig.canvas.get_renderer()).y0 / fig.dpi

    actual_x1 = ax.get_tightbbox(fig.canvas.get_renderer()).x1 / fig.dpi
    actual_y1 = ax.get_tightbbox(fig.canvas.get_renderer()).y1 / fig.dpi

    if ax2 is not None:
        ax2_x0 = ax2.get_tightbbox(fig.canvas.get_renderer()).x0 / fig.dpi
        ax2_y0 = ax2.get_tightbbox(fig.canvas.get_renderer()).y0 / fig.dpi

        ax2_x1 = ax2.get_tightbbox(fig.canvas.get_renderer()).x1 / fig.dpi
        ax2_y1 = ax2.get_tightbbox(fig.canvas.get_renderer()).y1 / fig.dpi

        actual_x1 = max(actual_x0 + actual_x1, ax2_x0 + ax2_x1)
        actual_y1 = max(actual_y0 + actual_y1, ax2_y0 + ax2_y1)

        if ax2_x0 < actual_x0:
            actual_x0 = ax2_x0

        if ax2_y0 < actual_y0:
            actual_y0 = ax2_y0

    # Save entire plot accounting for legend and y-labels extending outside of
    # figure

    box = Bbox(numpy.array([[actual_x0 - 0.05, actual_y0 - 0.05], [actual_x1 + 0.05, actual_y1 + 0.05]]))

    image_bytes = io.BytesIO()
    fig.savefig(image_bytes, format="png", bbox_inches=box)
    image_bytes.seek(0)

    # Truncate image to page size if necessary

    if (actual_x1 - actual_x0) > USABLE_WIDTH:
        actual_width = USABLE_WIDTH
    else:
        actual_width = actual_x1 - actual_x0

    return ImageFromBytes(
        ImageReader(image_bytes),
        width=actual_width * REPORT_DPI,
        height=plot_height * REPORT_DPI,
    )


from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate

# class MyDocTemplate(SimpleDocTemplate):
class MyDocTemplate(SimpleDocTemplate):

    allowSplitting = 0

    def afterFlowable(self, flowable):

        if flowable.__class__.__name__ == "Heading":
            if flowable.text != "Table of Contents":
                self.notify("TOCEntry", (0, flowable.text, self.page, flowable.text))


def save_reportlab_report(filepath, elements, drive="N/A", add_header_footer=True):

    pdf = MyDocTemplate(
        filepath,
        rightMargin=H_MARGIN,
        leftMargin=H_MARGIN,
        topMargin=V_MARGIN,
        bottomMargin=V_MARGIN,
        pagesize=LETTER,
    )

    if add_header_footer:
        pdf.multiBuild(elements, onLaterPages=functools.partial(_add_header_footer, drive_name=drive))

    else:
        pdf.multiBuild(elements)


class ImageFromBytes(Flowable):
    """Create image from bytes.

    Custom reportlab flowable class to draw an image from byte stream.  Idea from:
    https://stackoverflow.com/questions/31712386/loading-matplotlib-object-into-reportlab/32021013
    """

    def __init__(self, img_data, width=200, height=200):
        """Initialize the flowable."""
        self.img_width = width
        self.img_height = height
        self.img_data = img_data

    def wrap(self, width, height):
        """Wrap the flowable."""
        return self.img_width, self.img_height

    def drawOn(self, canv, x, y, _sW=0):  # noqa
        """Draw on the canvas."""
        if _sW > 0 and hasattr(self, "hAlign"):
            a = self.hAlign
            if a in ("CENTER", "CENTRE", TA_CENTER):
                x += 0.5 * _sW
            elif a in ("RIGHT", TA_RIGHT):
                x += _sW
            elif a not in ("LEFT", TA_LEFT):
                raise ValueError("Bad hAlign value " + str(a))
        canv.saveState()
        canv.drawImage(self.img_data, x, y, self.img_width, self.img_height)
        canv.restoreState()


class Heading(Flowable):
    """Draw heading with underline."""

    def __init__(self, text):
        """Initialize the flowable."""
        Flowable.__init__(self)
        self.text = text
        self.width = USABLE_WIDTH
        self.height = 14  # HEADING_STYLE.fontSize + HEADING_STYLE.spaceAfter + HEADING_STYLE.spaceBefore

    def draw(self):
        """Draw the heading on the canvas."""
        self.canv.saveState()
        self.canv.setFillColor(HEADING_STYLE.textColor)
        self.canv.setFont(
            HEADING_STYLE.fontName,
            HEADING_STYLE.fontSize,
            HEADING_STYLE.leading,
        )
        #   self.canv.drawString(0, HEADING_STYLE.spaceAfter, self.text.upper())

        line_y_value = HEADING_STYLE.spaceAfter - HEADING_STYLE.underlineOffset
        line_y_value = 8

        self.canv.bookmarkPage(self.text)
        self.canv.addOutlineEntry(self.text, self.text, 0, 0)

        self.canv.setStrokeColor(HEADING_STYLE.textColor)
        self.canv.setLineWidth(HEADING_STYLE.underlineWidth)
        self.canv.line(0, line_y_value, self.width, line_y_value)
        self.canv.restoreState()


class ResultDonut:
    """Create donut pie chart with number of passes and fails."""

    def __init__(self, passed, failed, result, skipped=0, size=1):
        """Create the donut pie chart."""
        fig, ax = plt.subplots(
            figsize=(size, size),
            gridspec_kw={
                "hspace": 0,
                "wspace": 0,
                "top": 1,
                "bottom": 0,
                "right": 1,
                "left": 0,
            },
            subplot_kw={"xmargin": 0.05, "ymargin": 0.05, "aspect": "equal"},
        )
        # skipped = 0
        aborted = 0
        if result == ABORTED:
            result_label = "N/A"
            text_color = FAIL_COLOR
            aborted = 1
            passed = 0
            failed = 0
        elif result == SKIPPED:
            result_label = "N/A"
            text_color = SKIP_COLOR
            skipped = 1
            passed = 0
            failed = 0
        elif failed == 0:
            result_label = "PASS"
            text_color = PASS_COLOR
        else:
            result_label = "FAIL"
            text_color = FAIL_COLOR

        ax.pie(
            [passed, failed, aborted, skipped],
            colors=[PASS_COLOR, FAIL_COLOR, FAIL_COLOR, SKIP_COLOR],
            wedgeprops={"width": 0.5},
            startangle=90,
            counterclock=False,
        )
        ax.axis("equal")  # Set the equal axis after the pie chart is created

        plt.text(
            0,
            0,
            result_label,
            ha="center",
            va="center",
            fontweight="bold",
            color=text_color,
            size=(10 * size),
        )
        self.image = convert_plot_to_image(fig, ax)
        plt.close(fig)


class TestResult(Flowable):
    """Draw test results banner."""

    _IMAGE_SIZE = 72
    _SPACE_BELOW = 8
    _VERTICAL_LINE_MARGIN = 12
    _FONT_SPACING = 8

    def __init__(self, test_data, data_type="verifications"):
        """Initialilze the flowable."""
        Flowable.__init__(self)

        if data_type == "tests":
            self._header = "TESTS"
            self._total = test_data["summary"]["tests"]["total"]
            self._pass = test_data["summary"]["tests"]["pass"]
            self._fail = test_data["summary"]["tests"]["fail"]
            self._skip = test_data["summary"]["tests"]["skip"]

        elif data_type == "requirements":
            self._header = "REQUIREMENTS"
            self._total = test_data["summary"]["rqmts"]["total"]
            self._pass = test_data["summary"]["rqmts"]["pass"]
            self._fail = test_data["summary"]["rqmts"]["fail"]
            self._skip = 0
        else:
            self._header = "VERIFICATIONS"
            self._total = test_data["summary"]["verifications"]["total"]
            self._pass = test_data["summary"]["verifications"]["pass"]
            self._fail = test_data["summary"]["verifications"]["fail"]
            self._skip = 0

        self.data_type = data_type
        self.result = test_data["result"]
        self.width = USABLE_WIDTH
        self.height = TestResult._IMAGE_SIZE + TestResult._SPACE_BELOW

    def draw(self):
        """Draw on the canvas."""
        self.canv.saveState()

        if (self._pass + self._fail > 0) or self.result == ABORTED or self.result == SKIPPED:
            donut_chart_image = ResultDonut(self._pass, self._fail, self.result, skipped=self._skip).image
            donut_chart_image.drawOn(self.canv, 0, TestResult._SPACE_BELOW)

        x1 = TestResult._IMAGE_SIZE + 36  # vertical line
        x2 = x1 + 36  # label
        x3 = x2 + 144  # value
        x4 = x3 + 64  # percent

        line_y_start = TestResult._SPACE_BELOW + TestResult._VERTICAL_LINE_MARGIN
        line_y_end = TestResult._IMAGE_SIZE + TestResult._SPACE_BELOW - TestResult._VERTICAL_LINE_MARGIN

        self.canv.setStrokeColor(TEXT_COLOR)
        self.canv.setStrokeColor(TABLE_ROW_GRAY_COLOR)
        self.canv.setLineWidth(2)
        self.canv.line(x1, line_y_start, x1, line_y_end)

        # draw the requirements section

        if self.data_type == "tests":
            y1 = self.height / 2 + 13 + TEXT_FONT_SIZE / 2 + 8
            y2 = y1 - 7 - TEXT_FONT_SIZE
            y3 = y2 - 7 - TEXT_FONT_SIZE
            y4 = y3 - 7 - TEXT_FONT_SIZE

        else:
            y1 = self.height / 2 + 7 + TEXT_FONT_SIZE / 2 + 8
            y2 = self.height / 2 - TEXT_FONT_SIZE / 2 + 8
            y3 = y2 - 7 - TEXT_FONT_SIZE

        self.canv.setFillColor(HEADING_COLOR)

        self.canv.setFont("Helvetica-Bold", TEXT_FONT_SIZE)
        self.canv.drawString(x2, y1, self._header)

        self.canv.drawRightString(x3, y1, f"{self._total}")
        self.canv.setFillColor(PASS_COLOR)
        self.canv.drawString(x2, y2, "PASS")
        self.canv.drawRightString(x3, y2, f"{self._pass}")
        if self._total == 0:
            pct = 0
        else:
            pct = self._pass / (self._total) * 100
        self.canv.drawRightString(x4, y2, f"{pct:0.1f}%")
        self.canv.setFillColor(FAIL_COLOR)
        self.canv.drawString(x2, y3, "FAIL")
        self.canv.drawRightString(x3, y3, f"{self._fail}")

        if self._total == 0:
            pct = 0
        else:
            pct = self._fail / (self._total) * 100

        self.canv.drawRightString(x4, y3, f"{pct:0.1f}%")

        if self.data_type == "tests":
            self.canv.setFillColor(SKIP_COLOR)
            self.canv.drawString(x2, y4, "SKIP")
            self.canv.drawRightString(x3, y4, f"{self._skip}")

            if self._total == 0:
                pct = 0
            else:
                pct = self._skip / (self._total) * 100

            self.canv.drawRightString(x4, y4, f"{pct:0.1f}%")

        self.canv.restoreState()


class TestSuiteResult(Flowable):
    """Draw test results banner."""

    _IMAGE_SIZE = 144
    _SPACE_BELOW = 24
    _SPACE_ABOVE = 24
    _VERTICAL_LINE_MARGIN = 12
    _FONT_SPACING = 8

    def __init__(self, run_pass, run_fail, start, end, duration):
        """Initialize the flowable."""
        Flowable.__init__(self)
        self.total_req = run_pass + run_fail
        self.pass_req = run_pass
        self.fail_req = run_fail
        self.width = USABLE_WIDTH
        self.height = TestSuiteResult._IMAGE_SIZE + TestSuiteResult._SPACE_BELOW + TestSuiteResult._SPACE_ABOVE
        self.start = start
        self.end = end
        self.duration = duration

    def draw(self):
        """Draw on the canvas."""
        self.canv.saveState()

        donut_chart_image = ResultDonut(self.pass_req, self.fail_req, "NA", 2).image
        donut_chart_image.drawOn(self.canv, 0, TestSuiteResult._SPACE_BELOW)

        x1 = TestSuiteResult._IMAGE_SIZE + 48  # vertical line
        x2 = x1 + 140  # label

        y_value = 7 + TestSuiteResult._SPACE_BELOW

        self.canv.setFillColor(TEXT_STYLE.textColor)
        self.canv.setFont("Helvetica", 12)
        self.canv.drawString(x1, y_value, "DURATION")
        self.canv.setFont("Helvetica", 12)
        self.canv.drawString(x2, y_value, self.duration)

        y_value += 20
        self.canv.setFillColor(TEXT_STYLE.textColor)
        self.canv.setFont("Helvetica", 12)
        self.canv.drawString(x1, y_value, "ENDED")
        self.canv.setFont("Helvetica", 12)
        self.canv.drawString(x2, y_value, self.end)

        y_value += 20
        self.canv.setFillColor(TEXT_STYLE.textColor)
        self.canv.setFont("Helvetica", 12)
        self.canv.drawString(x1, y_value, "STARTED")
        self.canv.setFont("Helvetica", 12)
        self.canv.drawString(x2, y_value, self.start)

        y_value += 40
        self.canv.setFillColor(FAIL_COLOR)
        self.canv.setFont("Helvetica-Bold", 12)
        self.canv.drawString(x1, y_value, "FAIL")
        self.canv.setFont("Helvetica", 12)
        self.canv.drawString(x2, y_value, f"{self.fail_req}")

        y_value += 20
        self.canv.setFillColor(PASS_COLOR)
        self.canv.setFont("Helvetica-Bold", 12)
        self.canv.drawString(x1, y_value, "PASSED")
        self.canv.setFont("Helvetica", 12)
        self.canv.drawString(x2, y_value, f"{self.pass_req}")

        y_value += 20
        self.canv.setFillColor(TEXT_STYLE.textColor)
        self.canv.setFont("Helvetica-Bold", 12)
        self.canv.drawString(x1, y_value, "REQUIREMENTS")
        self.canv.setFont("Helvetica", 12)
        self.canv.drawString(x2, y_value, f"{self.total_req}")

        self.canv.restoreState()


class TestTime(Flowable):
    """Draw test start, end, duration."""

    _SPACE_BELOW = 0
    _FONT_SPACING = 6

    def __init__(self, test_data):
        """Initialize the flowable."""
        Flowable.__init__(self)

        tmp_start = datetime.datetime.strptime(test_data["start time"], "%Y-%m-%d %H:%M:%S.%f")
        self.start = datetime.datetime.strftime(tmp_start, "%b %d, %Y - %H:%M:%S.%f")[0:-3]

        tmp_end = datetime.datetime.strptime(test_data["end time"], "%Y-%m-%d %H:%M:%S.%f")
        self.end = datetime.datetime.strftime(tmp_end, "%b %d, %Y - %H:%M:%S.%f")[0:-3]

        self.duration = str(tmp_end - tmp_start)[0:-3]
        self.width = USABLE_WIDTH
        self.height = TestTime._SPACE_BELOW + 2 * TEXT_FONT_SIZE + 3 * TestTime._FONT_SPACING + 1

    def draw(self):
        """Draw on the canvas."""
        self.canv.saveState()

        x1 = 0
        x2 = 220
        x3 = 420

        # draw the date/time section

        y = self.height - 1
        self.canv.setStrokeColor(TEXT_COLOR)

        self.canv.setStrokeColor(TABLE_ROW_GRAY_COLOR)

        self.canv.setLineWidth(1)
        self.canv.line(x1, y, USABLE_WIDTH, y)

        y = TestTime._SPACE_BELOW
        self.canv.line(x1, y, USABLE_WIDTH, y)

        self.canv.setFillColor(TEXT_STYLE.textColor)
        self.canv.setFont("Helvetica-Bold", TEXT_FONT_SIZE)

        y1 = TestTime._SPACE_BELOW + TestTime._FONT_SPACING + 1
        y2 = y1 + TEXT_FONT_SIZE + TestTime._FONT_SPACING

        self.canv.drawString(x1 + 5, y2, "STARTED")
        self.canv.drawString(x2, y2, "ENDED")
        self.canv.drawString(x3, y2, "DURATION")

        self.canv.setFont("Helvetica", TEXT_FONT_SIZE)

        self.canv.drawString(x1 + 5, y1, self.start)
        self.canv.drawString(x2, y1, self.end)
        self.canv.drawString(x3, y1, self.duration)

        self.canv.restoreState()


class TitlePage(Flowable):
    """Draw title page.

    This class draws the title page of a report.  It requires image files in the resource directory."""

    _SUBTITLE_STYLE = ParagraphStyle(
        "subtitle",
        fontSize=14,
        leading=20,
        textColor=HEADING_COLOR,
    )
    _TITLE_BACKGROUND = "#34ABA2"
    _TITLE_FONT_SIZE = 28
    _TITLE_LINE_HEIGHT = 6
    _TITLE_PAD = 8

    _DESCRIPTION_X_START = 54
    _DESCRIPTION_X_END = 108
    _description_y_start = 8 * 72 - 16

    def __init__(self, drive_info, title, report_description, date):
        """Initialize the flowable."""
        Flowable.__init__(self)
        self.width = USABLE_WIDTH
        self.height = USABLE_HEIGHT
        self.drive_info = drive_info
        self.report_description = report_description
        self.report_date = date
        self.title = title

    def draw(self):
        """Draw on the canvas."""
        self.canv.saveState()

        self.canv.setViewerPreference("FitWindow", "true")
        self.canv.showOutline()

        self.canv.setAuthor(__brandname__)
        self.canv.setTitle(self.title)
        self.canv.setSubject("NVMe Report")
        self.canv.setFillColor(TitlePage._TITLE_BACKGROUND)
        self.canv.rect(
            0,
            self.height,
            self.width,
            TitlePage._TITLE_LINE_HEIGHT,
            stroke=0,
            fill=1,
        )
        self.canv.rect(0, 0, self.width, TitlePage._TITLE_LINE_HEIGHT, stroke=0, fill=1)

        self.canv.setFillColor(HEADING_COLOR)
        self.canv.setFont("Helvetica-Bold", TitlePage._TITLE_FONT_SIZE)
        self.canv.drawString(
            0,
            self.height - TitlePage._TITLE_FONT_SIZE - TitlePage._TITLE_PAD,
            self.title,
        )

        # Use flowable to account for wrapping

        title_style = ParagraphStyle(
            "title",
            fontSize=28,
            leading=32,
            fontName="Helvetica-Bold",
            textColor=HEADING_COLOR,
        )
        drive_p = Paragraph(self.drive_info, style=title_style)
        drive_p.wrapOn(self.canv, self.width + 20, self.height)
        drive_p.drawOn(
            self.canv,
            0,
            self.height - TitlePage._TITLE_FONT_SIZE - 2 * TitlePage._TITLE_PAD - drive_p.height,
        )
        _description_y_start = (
            self.height - TitlePage._TITLE_FONT_SIZE - 2 * TitlePage._TITLE_PAD - drive_p.height - 24
        )

        # Use flowable to account for wrapping

        p = Paragraph(self.report_description, style=TitlePage._SUBTITLE_STYLE)
        p.wrapOn(self.canv, self.width - TitlePage._DESCRIPTION_X_END, self.height)
        p.drawOn(
            self.canv,
            TitlePage._DESCRIPTION_X_START,
            _description_y_start - p.height,
        )

        # Image

        title_image = os.path.join(RESOURCE_DIRECTORY, "NVMe_Title.jpeg")
        image_y_start = 138
        image_x_start = TitlePage._DESCRIPTION_X_START - 24

        nvme_image = Image(title_image, (6.8 * 64), (5.1 * 64))
        nvme_image.drawOn(self.canv, image_x_start, image_y_start)

        # Data in bottom right

        self.canv.setFont("Helvetica-Bold", 14)
        self.canv.drawRightString(self.width, 32, self.report_date)

        # Footer

        icon_size = 36
        icon_image = os.path.join(RESOURCE_DIRECTORY, "nvme_icon.png")

        nvme_icon = Image(icon_image, icon_size, icon_size)
        nvme_icon.drawOn(self.canv, 180, -42)
        self.canv.setFont("Helvetica-BoldOblique", 14)
        self.canv.drawString(222, -22, __brandname__)
        self.canv.setFont("Helvetica", 10)
        self.canv.drawString(222, -36, __website__)
        self.canv.restoreState()
