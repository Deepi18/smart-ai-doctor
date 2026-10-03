import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def generate_pdf_report(patient_name, patient_age, patient_gender, symptoms, predictions, ai_summary=None):
    """
    Generates a PDF byte stream for a Medical Assessment Report using ReportLab.
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

    # Custom Color Palette
    PRIMARY_COLOR = colors.HexColor("#0077b6")
    SECONDARY_COLOR = colors.HexColor("#023e8a")
    TEXT_COLOR = colors.HexColor("#1d3557")
    BG_LIGHT = colors.HexColor("#f8f9fa")
    WARNING_RED = colors.HexColor("#e63946")

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=PRIMARY_COLOR,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#6c757d"),
        fontName='Helvetica'
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=SECONDARY_COLOR,
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=TEXT_COLOR,
        fontName='Helvetica'
    )

    # 1. Header Banner
    story.append(Paragraph("Smart AI Doctor — Medical Assessment Summary", title_style))
    date_str = datetime.now().strftime("%B %d, %Y | %I:%M %p")
    story.append(Paragraph(f"Report Generated: {date_str} | Reference ID: SAD-{int(datetime.now().timestamp())}", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=15))

    # 2. Patient Demographics & Reported Symptoms Table
    patient_info_data = [
        [
            Paragraph("<b>Patient Name:</b> " + str(patient_name), body_style),
            Paragraph("<b>Age / Gender:</b> " + str(patient_age) + " / " + str(patient_gender), body_style)
        ],
        [
            Paragraph("<b>Reported Symptoms:</b> " + (symptoms if symptoms else "None specified"), body_style),
            Paragraph("<b>Assessment Type:</b> Dual AI & ML Analysis", body_style)
        ]
    ]

    patient_table = Table(patient_info_data, colWidths=[270, 270])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e9ecef")),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 15))

    # 3. Machine Learning Diagnoses Section
    story.append(Paragraph("Diagnoses & Condition Probabilities", section_heading))

    if predictions:
        pred_table_data = [
            [Paragraph("<b>Condition</b>", body_style), 
             Paragraph("<b>Match Confidence</b>", body_style), 
             Paragraph("<b>Urgency</b>", body_style), 
             Paragraph("<b>Recommended Specialist</b>", body_style)]
        ]

        for p in predictions:
            urgency_text = p['urgency']
            urgency_color = "red" if urgency_text == "High" else ("orange" if urgency_text == "Moderate" else "green")
            
            pred_table_data.append([
                Paragraph(f"<b>{p['disease']}</b><br/><font size=8 color='#495057'>{p['description']}</font>", body_style),
                Paragraph(f"<b>{p['confidence_percent']}%</b>", body_style),
                Paragraph(f"<font color='{urgency_color}'><b>{urgency_text}</b></font>", body_style),
                Paragraph(p['specialist'], body_style)
            ])

        pred_table = Table(pred_table_data, colWidths=[200, 90, 80, 170])
        pred_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2eafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#ced4da")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e9ecef")),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(pred_table)
    else:
        story.append(Paragraph("No specific high-confidence ML condition matched reported symptoms.", body_style))

    story.append(Spacer(1, 15))

    # 4. Detailed AI Recommendations / Summary
    if ai_summary:
        story.append(Paragraph("Clinical Advice & Insights", section_heading))
        # Format pre-formatted text into paragraphs
        lines = ai_summary.split('\n')
        for line in lines:
            line_clean = line.strip()
            if line_clean:
                story.append(Paragraph(line_clean, body_style))
                story.append(Spacer(1, 3))
        story.append(Spacer(1, 10))

    # 5. Precautions Summary
    if predictions:
        story.append(Paragraph("General Health Precautions", section_heading))
        all_precautions = []
        for p in predictions:
            all_precautions.extend(p.get("precautions", []))
        
        # Deduplicate precautions
        unique_precautions = list(dict.fromkeys(all_precautions))
        for prec in unique_precautions[:5]:
            story.append(Paragraph(f"• {prec}", body_style))
            story.append(Spacer(1, 2))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#ced4da"), spaceAfter=10))

    # 6. Medical Disclaimer Footer
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#6c757d"),
        fontName='Helvetica-Oblique'
    )
    story.append(Paragraph(
        "<b>Important Disclaimer:</b> Smart AI Doctor is an artificial intelligence decision-support tool. "
        "This report is for informational educational purposes only and does NOT constitute formal clinical medical diagnosis or prescription. "
        "If you are experiencing chest pain, severe dyspnea, or life-threatening symptoms, seek immediate emergency medical care.",
        disclaimer_style
    ))

    # Build Document
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
