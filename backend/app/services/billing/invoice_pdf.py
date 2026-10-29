from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.responses.billing import InvoiceResponse


def _money(value: Decimal) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") if "." in f"{value:.4f}" else f"{value:.4f}"


def build_invoice_pdf(invoice: InvoiceResponse) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"Invoice {invoice.id}")
    styles = getSampleStyleSheet()
    story = []

    title = invoice.document_number or invoice.reference_number or str(invoice.id)[:8]
    story.append(Paragraph(f"Invoice {title}", styles["Title"]))
    story.append(Paragraph(f"Status: {invoice.status}", styles["Normal"]))
    story.append(Paragraph(f"Payment: {invoice.payment_condition}", styles["Normal"]))
    if invoice.customer_name:
        story.append(Paragraph(f"Customer: {invoice.customer_name}", styles["Normal"]))
    if invoice.due_date:
        story.append(Paragraph(f"Due date: {invoice.due_date.isoformat()}", styles["Normal"]))
    if invoice.issued_at:
        story.append(Paragraph(f"Issued: {invoice.issued_at.isoformat()}", styles["Normal"]))
    story.append(Spacer(1, 16))

    rows = [["#", "Description", "Qty", "Unit price", "Tax %", "Total"]]
    for line in invoice.lines:
        rows.append(
            [
                str(line.line_number),
                line.description,
                _money(line.quantity),
                _money(line.unit_price),
                _money(line.tax_rate) if line.tax_rate is not None else "—",
                _money(line.line_total),
            ]
        )

    table = Table(rows, colWidths=[30, 220, 50, 70, 50, 70])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef7")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 16))
    story.append(Paragraph(f"Subtotal: {_money(invoice.subtotal)} {invoice.currency}", styles["Normal"]))
    story.append(Paragraph(f"Tax: {_money(invoice.tax_total)} {invoice.currency}", styles["Normal"]))
    story.append(Paragraph(f"<b>Total: {_money(invoice.total)} {invoice.currency}</b>", styles["Normal"]))
    story.append(Paragraph(f"Paid: {_money(invoice.amount_paid)} {invoice.currency}", styles["Normal"]))
    story.append(Paragraph(f"Balance: {_money(invoice.balance_due)} {invoice.currency}", styles["Normal"]))
    if invoice.notes:
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Notes: {invoice.notes}", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
