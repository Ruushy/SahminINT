import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER


BG_COLOR = HexColor("#050810")
CARD_BG = HexColor("#0a1020")
ACCENT = HexColor("#22d3ee")
ACCENT2 = HexColor("#14b8a6")
TEXT_COLOR = HexColor("#e2e8f0")
MUTED = HexColor("#94a3b8")
SUCCESS = HexColor("#10b981")
WARN = HexColor("#f59e0b")
DANGER = HexColor("#f43f5e")


def build_pdf(report):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20*mm, bottomMargin=20*mm,
        leftMargin=15*mm, rightMargin=15*mm,
        title=report.title,
        author="SahminINT - Ruushy",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RH_Title", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=22,
        textColor=ACCENT, spaceAfter=6*mm,
        alignment=TA_CENTER,
    )
    h2_style = ParagraphStyle(
        "RH_H2", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=14,
        textColor=ACCENT, spaceBefore=8*mm, spaceAfter=4*mm,
    )
    body_style = ParagraphStyle(
        "RH_Body", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9,
        textColor=TEXT_COLOR, spaceAfter=3*mm,
        leading=13,
    )
    muted_style = ParagraphStyle(
        "RH_Muted", parent=body_style,
        textColor=MUTED, fontSize=8,
    )
    header_style = ParagraphStyle(
        "RH_Header", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=8,
        textColor=ACCENT2,
    )
    footer_style = ParagraphStyle(
        "RH_Footer", parent=styles["Normal"],
        fontName="Helvetica", fontSize=7,
        textColor=MUTED, alignment=TA_CENTER,
    )

    data = report.get_data()
    elements = []

    # Title
    elements.append(Paragraph(report.title, title_style))
    elements.append(Spacer(1, 4*mm))

    # Meta
    meta_text = f"Generated: {report.created_at.strftime('%Y-%m-%d %H:%M UTC')} | Type: {report.report_type}"
    if report.target:
        meta_text += f" | Target: {report.target.domain}"
    elements.append(Paragraph(meta_text, muted_style))
    elements.append(Spacer(1, 6*mm))

    # Stats table
    stats = data.get("stats", {})
    if stats:
        elements.append(Paragraph("Statistics", h2_style))
        stat_data = [[Paragraph(k.replace("_", " ").title(), header_style), Paragraph(str(v), body_style)] for k, v in stats.items()]
        t = Table([["Metric", "Value"]] + stat_data, colWidths=[120*mm, 80*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#000000")),
            ("BACKGROUND", (0, 1), (-1, -1), CARD_BG),
            ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_COLOR),
            ("GRID", (0, 0), (-1, -1), 0.5, ACCENT),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)

    # DNS Records
    dns_records = data.get("dns", [])
    if dns_records:
        elements.append(Paragraph("DNS Records", h2_style))
        dns_display = [r if isinstance(r, dict) else {"type": "?", "value": str(r)} for r in dns_records]
        ddata = [[Paragraph(r.get("record_type", r.get("type", "?")), header_style), Paragraph(str(r.get("value", ""))[:200], body_style)] for r in dns_display]
        t = Table([["Type", "Value"]] + ddata, colWidths=[30*mm, 170*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#000000")),
            ("BACKGROUND", (0, 1), (-1, -1), CARD_BG),
            ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_COLOR),
            ("GRID", (0, 0), (-1, -1), 0.5, ACCENT),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t)

    # Subdomains
    subs = data.get("subdomains", [])
    if subs:
        elements.append(Paragraph(f"Subdomains ({len(subs)})", h2_style))
        sdata = [[Paragraph(s[:70], body_style)] for s in subs[:100]]
        if sdata:
            t = Table([["Hostname"]] + sdata, colWidths=[200*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#000000")),
                ("BACKGROUND", (0, 1), (-1, -1), CARD_BG),
                ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_COLOR),
                ("GRID", (0, 0), (-1, -1), 0.5, ACCENT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(t)

    # Saved Dorks
    dorks = data.get("dorks", [])
    if dorks:
        elements.append(Paragraph("Saved Dorks", h2_style))
        ddata = [[Paragraph(d.get("query", str(d))[:100], body_style)] for d in dorks[:50]]
        if ddata:
            t = Table([["Query"]] + ddata, colWidths=[200*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#000000")),
                ("BACKGROUND", (0, 1), (-1, -1), CARD_BG),
                ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_COLOR),
                ("GRID", (0, 0), (-1, -1), 0.5, ACCENT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(t)

    # Author credit footer
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph(
        "Built by <a href='https://ruushy.github.io/protfolio/' color='#22d3ee'>Ruushy</a> &middot; "
        "<a href='https://github.com/Ruushy' color='#22d3ee'>GitHub</a> &middot; "
        "<a href='https://t.me/hacking_akhlaaqyin' color='#22d3ee'>Telegram</a> &middot; "
        "<a href='https://discord.gg/55GhmhcSY' color='#22d3ee'>Discord</a> &middot; "
        "<a href='https://instagram.com/arkani659' color='#22d3ee'>Instagram</a>",
        footer_style,
    ))

    # Build
    doc.build(elements)
    buf.seek(0)
    return buf
