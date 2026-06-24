from reportlab.pdfgen import canvas

pdf = canvas.Canvas(
"Student_Report.pdf"
)

pdf.drawString(
100,
750,
"Student Dropout Report"
)

pdf.save()