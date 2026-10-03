import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def generate_pdf_report(patient_name, patient_age, patient_gender, symptoms, predictions, ai_summary=None, safety_alerts=None, prescription_review=None, assessment_result=None):
    """
    Generates a PDF byte stream for an AI Health Assessment & Prescription Safety Report using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Brand Colors
    PRIMARY_COLOR = colors.HexColor("#0077b6")
    SECONDARY_COLOR = colors.HexColor("#023e8a")
    TEXT_COLOR = colors.HexColor("#1d3557")
    BG_LIGHT = colors.HexColor("#f8f9fa")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=PRIMARY_COLOR,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#6c757d"),
        fontName='Helvetica'
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=SECONDARY_COLOR,
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=TEXT_COLOR,
        fontName='Helvetica'
    )

    # 1. Header Banner
    story.append(Paragraph("SMART AI DOCTOR — AI Health Assessment & Safety Report", title_style))
    date_str = datetime.now().strftime("%B %d, %Y | %I:%M %p")
    story.append(Paragraph(f"Report Generated: {date_str} | Reference ID: SAD-{int(datetime.now().timestamp())}", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))

    # 2. Patient Information Table
    patient_info_data = [
        [
            Paragraph("<b>Patient Name:</b> " + str(patient_name), body_style),
            Paragraph("<b>Age / Gender:</b> " + str(patient_age) + " / " + str(patient_gender), body_style)
        ],
        [
            Paragraph("<b>Reported Symptoms:</b> " + (symptoms if symptoms else "None specified"), body_style),
            Paragraph("<b>Assessment Architecture:</b> Open-Set Hybrid ML & Medical Knowledge Base", body_style)
        ]
    ]

    patient_table = Table(patient_info_data, colWidths=[270, 270])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e9ecef")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 10))

    # Open-Set Coverage Assessment Banner
    if assessment_result and "coverage_result" in assessment_result:
        cov = assessment_result["coverage_result"]
        cov_title = "ML Domain Coverage Status"
        cov_msg = cov.get("notice", "")
        cov_bg = colors.HexColor("#e0f2fe") if cov.get("is_in_ml_domain") else colors.HexColor("#fef3c7")
        cov_txt_color = colors.HexColor("#0369a1") if cov.get("is_in_ml_domain") else colors.HexColor("#92400e")
        
        cov_style = ParagraphStyle('CovText', parent=body_style, textColor=cov_txt_color)
        story.append(Paragraph(f"<b>{cov_title}:</b> {cov_msg}", cov_style))
        story.append(Spacer(1, 8))

    # 3. Emergency Safety Alerts (If Any)
    if safety_alerts and safety_alerts.get("is_emergency"):
        alert_style = ParagraphStyle(
            'AlertText',
            parent=body_style,
            textColor=colors.HexColor("#dc2626"),
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph("⚠️ URGENT MEDICAL ATTENTION REQUIRED", section_heading))
        for alert in safety_alerts.get("alerts", []):
            story.append(Paragraph(f"• <b>{alert['name']}:</b> {alert['message']}", alert_style))
        story.append(Spacer(1, 10))

    # 4. Ranked Possible Conditions & Explainable AI
    story.append(Paragraph("Ranked Differential Conditions & Evidence Breakdown", section_heading))

    diff_conditions = assessment_result.get("differential_conditions", []) if assessment_result else None
    
    if diff_conditions:
        pred_table_data = [
            [Paragraph("<b>Condition & Source</b>", body_style), 
             Paragraph("<b>Evidence Score</b>", body_style), 
             Paragraph("<b>Urgency</b>", body_style), 
             Paragraph("<b>Clinical Citation / Referral</b>", body_style)]
        ]

        for p in diff_conditions:
            urgency_text = p.get('urgency', 'Moderate')
            urgency_color = "red" if urgency_text == "High" else ("orange" if urgency_text == "Moderate" else "green")
            score_str = f"{p.get('score_label', '')}"
            src_str = p.get('source_type', '')
            ref_str = p.get('reference', p.get('specialist', 'Specialist Consultation'))
            
            pred_table_data.append([
                Paragraph(f"<b>{p['condition_name']}</b><br/><font size=7 color='#6c757d'>{src_str}</font><br/><font size=8 color='#495057'>{p.get('description', '')}</font>", body_style),
                Paragraph(f"<b>{score_str}</b>", body_style),
                Paragraph(f"<font color='{urgency_color}'><b>{urgency_text}</b></font>", body_style),
                Paragraph(f"<b>Ref:</b> {ref_str}<br/><b>Referral:</b> {p.get('specialist', 'General Physician')}", body_style)
            ])

        pred_table = Table(pred_table_data, colWidths=[180, 110, 65, 185])
        pred_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2eafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#ced4da")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e9ecef")),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(pred_table)
    elif predictions:
        pred_table_data = [
            [Paragraph("<b>Condition</b>", body_style), 
             Paragraph("<b>Match Score</b>", body_style), 
             Paragraph("<b>Urgency</b>", body_style), 
             Paragraph("<b>Specialist Referral</b>", body_style)]
        ]

        for p in predictions:
            urgency_text = p.get('urgency', 'Moderate')
            urgency_color = "red" if urgency_text == "High" else ("orange" if urgency_text == "Moderate" else "green")
            match_score_str = p.get('model_match_score', f"Model match score: {p.get('confidence_percent', 0)}%")
            
            pred_table_data.append([
                Paragraph(f"<b>{p['disease']}</b><br/><font size=8 color='#495057'>{p['description']}</font>", body_style),
                Paragraph(f"<b>{match_score_str}</b>", body_style),
                Paragraph(f"<font color='{urgency_color}'><b>{urgency_text}</b></font>", body_style),
                Paragraph(p['specialist'], body_style)
            ])

        pred_table = Table(pred_table_data, colWidths=[190, 110, 75, 165])
        pred_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2eafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#ced4da")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e9ecef")),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(pred_table)
    else:
        story.append(Paragraph("No specific high-confidence condition matched the reported symptom vector.", body_style))

    story.append(Spacer(1, 10))

    # 5. Prescription Safety Review Summary (If Performed)
    if prescription_review:
        story.append(Paragraph("Prescription Safety Review Summary", section_heading))
        status_color = prescription_review.get("color", "#34d399")
        status_label = prescription_review.get("status_label", "Review Performed")
        med_name = prescription_review.get("prescribed_medicine", "N/A")
        
        rx_text = f"<b>Prescribed Medicine:</b> {med_name} | <b>Status:</b> <font color='{status_color}'><b>{status_label}</b></font>"
        story.append(Paragraph(rx_text, body_style))

        for flag in prescription_review.get("flags", []):
            story.append(Paragraph(f"• <b>[{flag['category']}]</b> {flag['detail']}", body_style))
        story.append(Spacer(1, 8))

    # 6. Clinical Guidance Summary
    if ai_summary:
        story.append(Paragraph("Clinical Information & Guidance", section_heading))
        lines = ai_summary.split('\n')
        for line in lines:
            line_clean = line.strip()
            if line_clean:
                story.append(Paragraph(line_clean, body_style))
                story.append(Spacer(1, 2))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#ced4da"), spaceAfter=8))

    # 7. Mandatory Decision-Support Disclaimer Footer
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#6c757d"),
        fontName='Helvetica-Oblique'
    )
    story.append(Paragraph(
        "<b>Important Disclaimer:</b> This report is generated by an AI-assisted decision-support system and is not a medical diagnosis or prescription. "
        "Consult a qualified healthcare professional for medical decisions. If experiencing chest pain, severe dyspnea, or life-threatening symptoms, seek immediate emergency care.",
        disclaimer_style
    ))

    # Build Document
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
