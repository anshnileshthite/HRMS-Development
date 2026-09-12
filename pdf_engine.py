import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def generate_appointment_letter(company_name, company_address, emp_name, emp_code, designation, joining_date, ctc_monthly):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Letterhead Header
    p.setFillColor(colors.HexColor("#FF6B35"))
    p.rect(0, height - 12, width, 12, stroke=0, fill=1)
    
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, height - 50, company_name)
    p.setFont("Helvetica", 9)
    p.drawString(40, height - 65, company_address)
    p.setStrokeColor(colors.HexColor("#CCCCCC"))
    p.line(40, height - 75, width - 40, height - 75)

    # Title
    p.setFont("Helvetica-Bold", 13)
    p.drawCentredString(width / 2.0, height - 110, "LETTER OF APPOINTMENT")

    # Date & Recipient
    p.setFont("Helvetica", 10)
    p.drawString(40, height - 145, f"Date: {joining_date}")
    p.drawString(40, height - 165, f"To: {emp_name}")
    p.drawString(40, height - 180, f"Employee ID: {emp_code}")

    # Body
    text_lines = [
        f"Dear {emp_name},",
        f"",
        f"We are pleased to appoint you to the position of '{designation}' with {company_name}.",
        f"Your employment begins on {joining_date}. Below are the primary terms of your engagement:",
        f"",
        f"1. Compensation: Your Gross Monthly CTC will be Rs. {ctc_monthly:,.2f}, payable as per statutory",
        f"   wages guidelines inclusive of Basic, DA, HRA, and statutory ESIC/EPF deductions.",
        f"2. Workplace: You will be assigned to client deployment sites (e.g. SEZ Khed City / MIDC).",
        f"3. Working Hours: Shift assignments follow general manufacturing schedules (including A/B/C rotations).",
        f"4. Compliance: You agree to uphold company code of conduct and safety regulations on site.",
        f"",
        f"Please sign and return the duplicate copy of this letter as confirmation of your acceptance.",
        f"",
        f"Yours faithfully,",
        f"For {company_name}",
        f"",
        f"Authorized Signatory"
    ]

    y = height - 215
    for line in text_lines:
        p.drawString(40, y, line)
        y -= 18

    p.drawString(width - 200, height - 490, "Candidate Signature: ______________")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()