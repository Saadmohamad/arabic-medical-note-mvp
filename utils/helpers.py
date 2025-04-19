from fpdf import FPDF
import tempfile

def export_summary_pdf(doctor_name, patient_name, date, summary):
    """
    Generate and save a PDF of the summary.

    Args:
        doctor_name (str): Name of the doctor.
        patient_name (str): Name of the patient.
        date (datetime.date): Date of the session.
        summary (str): Clinical summary text.

    Returns:
        str: Path to the generated PDF file.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Doctor: {doctor_name}\nPatient: {patient_name}\nDate: {date.strftime('%Y-%m-%d')}\n\nSummary:\n{summary}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        return tmp.name
