from __future__ import annotations

import tempfile
import textwrap
from pathlib import Path
from datetime import date as _date
from typing import Optional

from fpdf import FPDF  # ensure this is fpdf2
import arabic_reshaper
from bidi.algorithm import get_display

FONT_CACHE: dict[str, tuple[str, str]] = {}

# -----------------------------------------------------------------------------
# 🔤 Font utilities
# -----------------------------------------------------------------------------


def _get_dejavu_font() -> tuple[str, str]:
    """Return the bundled DejaVuSans.ttf font for PDF generation."""
    if "dejavu" in FONT_CACHE:
        return FONT_CACHE["dejavu"]

    # Vendored font path relative to this helper module
    bundled = Path(__file__).parent.parent / "fonts" / "DejaVuSans.ttf"
    if not bundled.is_file():
        raise FileNotFoundError(
            f"Cannot find bundled font at {bundled}. "
            "Make sure you have downloaded DejaVuSans.ttf into the ./fonts directory."
        )

    FONT_CACHE["dejavu"] = ("DejaVu", str(bundled))
    return FONT_CACHE["dejavu"]


# -----------------------------------------------------------------------------
# 🛠️  Text helpers
# -----------------------------------------------------------------------------


def _shape(txt: str) -> str:
    return get_display(arabic_reshaper.reshape(txt))


def _wrap_rtl(text: str, width: int = 90) -> list[str]:
    shaped = _shape(text)
    return textwrap.wrap(
        shaped, width=width, break_long_words=False, replace_whitespace=False
    )


# -----------------------------------------------------------------------------
# 🖨️  Public API
# -----------------------------------------------------------------------------


def export_summary_pdf(
    doctor_name: str,
    patient_name: str,
    date: _date,
    summary: str,
    transcript: Optional[str] = None,
) -> str:
    """Generate an Arabic PDF with summary **and optionally the full transcript**."""

    fam, font_path = _get_dejavu_font()
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font(fam, style="", fname=font_path, uni=True)
    pdf.set_font(fam, size=14)

    header_lines = [
        f"الطبيب: {doctor_name}",
        f"المريض: {patient_name}",
        f"التاريخ: {date.strftime('%Y-%m-%d')}",
        "",
        "الملخص:",
    ]

    for line in header_lines:
        for seg in _wrap_rtl(line):
            pdf.cell(0, 8, seg, ln=1, align="R")

    pdf.ln(1)
    for raw in summary.splitlines():
        for seg in _wrap_rtl(raw):
            pdf.cell(0, 8, seg, ln=1, align="R")

    # ---------------- Transcript section ----------------
    if transcript:
        pdf.ln(4)
        for seg in _wrap_rtl("النص الكامل:"):
            pdf.cell(0, 8, seg, ln=1, align="R")
        pdf.ln(1)
        for raw in transcript.splitlines():
            for seg in _wrap_rtl(raw):
                pdf.cell(0, 8, seg, ln=1, align="R")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        return tmp.name
