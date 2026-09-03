"""
PDF Audit Trail Export
───────────────────────
Generates a professional PDF report for a single bidder containing:
  - Bidder summary (name, identifiers, score, risk)
  - Per-check compliance results
  - AI recommendation text
  - Full audit trail (every event with timestamp)
  - Officer overrides log

Uses ReportLab for PDF generation — no external service, fully offline.
"""
from io import BytesIO
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# ── Color palette ─────────────────────────────────────────────────────────
DARK = colors.HexColor("#0f172a")
ACCENT = colors.HexColor("#6366f1")
SUCCESS = colors.HexColor("#10b981")
DANGER = colors.HexColor("#ef4444")
WARNING = colors.HexColor("#f59e0b")
MUTED = colors.HexColor("#64748b")
BG_LIGHT = colors.HexColor("#f8fafc")


def _risk_color(risk_level: str) -> colors.Color:
    return {"Low": SUCCESS, "Medium": WARNING, "High": DANGER, "Critical": DANGER}.get(risk_level, MUTED)


def _status_color(status: str) -> colors.Color:
    return {"pass": SUCCESS, "fail": DANGER, "manual_review": WARNING, "not_applicable": MUTED}.get(status, MUTED)


def generate_bidder_pdf(
    bidder_data: dict,
    checks: list[dict],
    audit_entries: list[dict],
    overrides: list[dict],
) -> bytes:
    """
    Generate a complete compliance audit PDF for a single bidder.
    Returns PDF as bytes.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", fontSize=20, textColor=ACCENT, fontName="Helvetica-Bold", spaceAfter=4)
    h2_style = ParagraphStyle("h2", fontSize=13, textColor=DARK, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)
    h3_style = ParagraphStyle("h3", fontSize=11, textColor=ACCENT, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle("body", fontSize=9.5, textColor=DARK, leading=14)
    muted_style = ParagraphStyle("muted", fontSize=8.5, textColor=MUTED, leading=12)
    mono_style = ParagraphStyle("mono", fontSize=8, fontName="Courier", textColor=DARK, leading=12)

    story = []

    # ── Header ───────────────────────────────────────────────────────────
    story.append(Paragraph("GeM Bid Compliance Verification Platform", muted_style))
    story.append(Paragraph("CPCL · Ministry of Petroleum &amp; Natural Gas · SIH 2026 — PS-26100", muted_style))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"Compliance Audit Report: {bidder_data.get('company_name', 'Unknown')}", title_style))
    story.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", muted_style))
    story.append(Spacer(1, 0.5 * cm))

    # ── Score Summary ─────────────────────────────────────────────────────
    score = bidder_data.get("compliance_score")
    risk = bidder_data.get("risk_level", "N/A")
    risk_clr = _risk_color(risk)

    summary_data = [
        ["Compliance Score", f"{score}/100" if score is not None else "Not Run"],
        ["Risk Level", risk],
        ["GSTIN", bidder_data.get("gstin", "—")],
        ["PAN", bidder_data.get("pan", "—")],
        ["CIN", bidder_data.get("cin", "—")],
        ["Last Verified", str(bidder_data.get("last_verified_at", "Never"))[:19]],
    ]

    summary_table = Table(summary_data, colWidths=[5 * cm, 10 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), BG_LIGHT),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, BG_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Compliance Checks ─────────────────────────────────────────────────
    story.append(Paragraph("Compliance Check Results", h2_style))

    check_headers = [["Check", "Tier", "Status", "Detail"]]
    check_rows = []
    for c in checks:
        status = c.get("status", "")
        check_rows.append([
            c.get("check_name", "").replace("_", " ").title(),
            c.get("check_tier", "").replace("tier", "Tier "),
            status.upper().replace("_", " "),
            Paragraph(str(c.get("detail", "—"))[:120], muted_style),
        ])

    check_table = Table(check_headers + check_rows, colWidths=[4 * cm, 2.5 * cm, 3 * cm, 7.5 * cm])
    check_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(check_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Officer Overrides ─────────────────────────────────────────────────
    if overrides:
        story.append(Paragraph("Officer Overrides", h2_style))
        for ov in overrides:
            story.append(Paragraph(
                f"<b>{ov.get('check_name', '').replace('_', ' ').title()}</b>: "
                f"{ov.get('original_status')} → {ov.get('overridden_status')} | "
                f"Reason: {ov.get('reason')} | Officer: {ov.get('officer_id')} | "
                f"Time: {str(ov.get('overridden_at', ''))[:19]}",
                body_style,
            ))
            story.append(Spacer(1, 0.1 * cm))

    # ── AI Recommendation ─────────────────────────────────────────────────
    if bidder_data.get("recommendation"):
        story.append(Paragraph("AI Recommendation (Python Template Engine)", h2_style))
        # Strip markdown for PDF
        rec_text = bidder_data["recommendation"].replace("**", "").replace("##", "").replace("#", "")
        for line in rec_text.split("\n")[:30]:
            if line.strip():
                story.append(Paragraph(line.strip(), body_style))
        story.append(Spacer(1, 0.4 * cm))

    # ── Audit Trail ───────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Paragraph("Immutable Audit Trail", h2_style))
    story.append(Paragraph("Every automated query, manual verification, AI output, and officer action — PRD §12", muted_style))
    story.append(Spacer(1, 0.3 * cm))

    for entry in audit_entries:
        ts = str(entry.get("timestamp", ""))[:19]
        evt = entry.get("event_type", "").replace("_", " ")
        desc = entry.get("description", "")
        story.append(Paragraph(f"[{ts}] <b>{evt}</b> — {desc}", mono_style))

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "This report is generated by the GeM Bid Compliance Verification Platform. "
        "The final qualify/disqualify decision rests with the Procurement Officer. "
        "This document constitutes an official audit record.",
        muted_style,
    ))

    doc.build(story)
    return buf.getvalue()
