from __future__ import annotations

import tempfile
from pathlib import Path
from datetime import date as _date
from typing import Optional

from fpdf import FPDF  # fpdf2
import arabic_reshaper
from bidi.algorithm import get_display
from functools import lru_cache


# -----------------------------------------------------------------------------
# 🔤 Font utilities
# -----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _get_dejavu_font() -> tuple[str, str]:
    """Return the bundled DejaVuSans.ttf font for PDF generation."""

    bundled = Path(__file__).parent.parent / "fonts" / "DejaVuSans.ttf"
    if not bundled.is_file():
        raise FileNotFoundError(
            f"Cannot find bundled font at {bundled}. "
            "Make sure you have downloaded DejaVuSans.ttf into the ./fonts directory."
        )

    return ("DejaVu", str(bundled))


# -----------------------------------------------------------------------------
# 🛠️  Text helpers (Arabic shaping + RTL wrapping)
# -----------------------------------------------------------------------------
def _shape(txt: str) -> str:
    """Reshape Arabic and reverse for correct RTL display."""
    return get_display(arabic_reshaper.reshape(txt))


def _wrap_rtl(text: str, width: int = 90) -> list[str]:
    """Word-wrap a longer Arabic string for RTL PDFs."""
    import textwrap

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
    summary: dict,
    transcript: Optional[str] = None,
) -> str:
    """
    Build a mixed-language PDF:

    • English header + summary (LTR, left-aligned)
    • Arabic transcript heading + transcript text (RTL, right-aligned)
    """
    fam, font_path = _get_dejavu_font()
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font(fam, style="", fname=font_path, uni=True)
    pdf.set_font(fam, size=12)

    # ------------ English header ------------
    header_lines = [
        f"Doctor: {doctor_name}",
        f"Patient: {patient_name}",
        f"Date: {date.strftime('%Y-%m-%d')}",
        "",
    ]
    for line in header_lines:
        pdf.cell(0, 8, line, ln=1, align="L")

    # ------------ English summary -----------
    pdf.ln(2)
    for section_title, content in summary.items():
        content = str(content).strip()
        if content:
            pdf.set_font(fam, style="", size=12)
            pdf.cell(0, 10, f"{section_title}:", ln=1)

            pdf.set_font(fam, style="", size=12)
            indented_content = "\n".join(f"    {line}" for line in content.splitlines())
            pdf.multi_cell(0, 8, indented_content, align="L")
            pdf.ln(2)

    # ------------ Arabic transcript ---------
    if transcript:
        pdf.ln(6)
        for seg in _wrap_rtl("Full Transcript:"):  # “Full transcript:” in Arabic
            pdf.cell(0, 8, seg, ln=1, align="R")
        pdf.ln(2)
        for raw in transcript.splitlines():
            for seg in _wrap_rtl(raw):
                pdf.cell(0, 8, seg, ln=1, align="R")

    # ------------ Save to a temp file -------
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        return tmp.name
