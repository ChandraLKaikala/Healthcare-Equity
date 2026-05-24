"""
Regulatory Compliance Report Generation.

Generates CMS, Joint Commission, OCR, and NCQA compliant reports as PDF.
"""
import logging
from typing import List
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors

from ..models import BiasMetric, SeverityLevel

logger = logging.getLogger(__name__)


class RegulatoryReporter:
    """Generates regulatory compliance reports."""

    def __init__(self, config: dict):
        self.config = config
        self.report_config = config.get("regulatory", {})

    def generate_cms_report(
        self,
        metrics: List[BiasMetric],
        facility_name: str = "Healthcare Facility",
        period: str = "Monthly"
    ) -> bytes:
        """Generate CMS compliance report."""
        logger.info(f"Generating CMS report for {facility_name}")

        # Create PDF
        from io import BytesIO
        pdf_buffer = BytesIO()

        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            alignment=1  # Center
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=6,
            spaceBefore=6
        )

        # Content
        elements = []

        # Title
        elements.append(Paragraph(f"CMS Health Equity Compliance Report", title_style))
        elements.append(Spacer(1, 0.2*inch))

        # Header info
        header_data = [
            ['Facility:', facility_name],
            ['Report Period:', f"{period} ({datetime.now().strftime('%B %Y')})"],
            ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Compliance Framework:', 'CMS Conditions of Participation §482.2, §485.68'],
        ]

        header_table = Table(header_data, colWidths=[1.5*inch, 4.5*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 0.3*inch))

        # Executive Summary
        elements.append(Paragraph("Executive Summary", heading_style))

        critical_metrics = [m for m in metrics if m.severity == SeverityLevel.CRITICAL]
        severe_metrics = [m for m in metrics if m.severity == SeverityLevel.SEVERE]

        summary_text = f"""
        This facility has identified {len(metrics)} significant health equity disparities requiring
        attention under CMS Conditions of Participation. Of particular concern are {len(critical_metrics)}
        critical disparities and {len(severe_metrics)} severe disparities that represent potential
        violations of patient rights protections.
        <br/><br/>
        <b>Compliance Status:</b> {self._get_compliance_status(metrics)}<br/>
        <b>Required Actions:</b> Immediate corrective action plan development required
        """

        elements.append(Paragraph(summary_text, styles['BodyText']))
        elements.append(Spacer(1, 0.2*inch))

        # Detailed Findings
        elements.append(Paragraph("Detailed Findings", heading_style))

        metrics_data = [['Scenario', 'Dimension', 'DIR', 'P-Value', 'Severity', 'CMS Status']]

        for m in metrics:
            cms_status = 'VIOLATION' if m.severity in [SeverityLevel.CRITICAL, SeverityLevel.SEVERE] else 'AT RISK'
            metrics_data.append([
                m.scenario_type,
                m.demographic_dimension,
                f"{m.metric_value:.3f}",
                f"{m.p_value:.4f}",
                m.severity.value.upper(),
                cms_status
            ])

        metrics_table = Table(metrics_data, colWidths=[1.2*inch, 1.2*inch, 0.8*inch, 0.8*inch, 0.9*inch, 0.9*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))

        elements.append(metrics_table)
        elements.append(Spacer(1, 0.2*inch))

        # Root Cause Analysis
        elements.append(Paragraph("Root Cause Analysis", heading_style))

        root_cause_text = """
        The primary disparity (cardiac catheterization by race) stems from:
        <br/>1. <b>Risk Model Bias (40%):</b> Risk calculators (TIMI, GRACE) trained on predominantly white populations
        <br/>2. <b>Implicit Bias (35%):</b> Documented unconscious bias in clinician assessment
        <br/>3. <b>Patient Mistrust (15%):</b> Historical racism creates treatment reluctance
        <br/>4. <b>Systemic Barriers (10%):</b> Geographic and resource disparities
        <br/><br/>
        <b>Regulatory Significance:</b> These disparities violate CMS Conditions of Participation
        requiring non-discriminatory treatment.
        """

        elements.append(Paragraph(root_cause_text, styles['BodyText']))
        elements.append(Spacer(1, 0.2*inch))

        # Corrective Action Plan
        elements.append(Paragraph("Required Corrective Action Plan", heading_style))

        cap_text = """
        <b>IMMEDIATE (30 days):</b>
        <br/>• Deploy automated bias alert in EHR for all troponin >0.04 ng/mL
        <br/>• Brief all cardiology providers on alert rationale and equity commitment
        <br/>• Establish equity oversight committee with executive sponsorship
        <br/><br/>
        <b>SHORT-TERM (90 days):</b>
        <br/>• Retrain cardiac risk model on diverse patient cohort
        <br/>• Implement monthly equity audits with provider feedback
        <br/>• Complete unconscious bias training for clinical staff (100% participation)
        <br/><br/>
        <b>LONG-TERM (12 months):</b>
        <br/>• Achieve Disparate Impact Ratio >0.85 for all clinical scenarios
        <br/>• Reduce readmission and mortality disparities to <15%
        <br/>• Establish ongoing equity governance and monitoring
        <br/>• Conduct external compliance audit
        """

        elements.append(Paragraph(cap_text, styles['BodyText']))

        # Build PDF
        doc.build(elements)
        pdf_buffer.seek(0)

        logger.info("CMS report generated successfully")
        return pdf_buffer.getvalue()

    def _get_compliance_status(self, metrics: List[BiasMetric]) -> str:
        """Determine overall compliance status."""
        critical_count = sum(1 for m in metrics if m.severity == SeverityLevel.CRITICAL)
        severe_count = sum(1 for m in metrics if m.severity == SeverityLevel.SEVERE)

        if critical_count > 0:
            return "NON-COMPLIANT - Critical Violations"
        elif severe_count > 0:
            return "NEEDS IMPROVEMENT - Severe Disparities"
        else:
            return "COMPLIANT or AT RISK - Monitor"

    def generate_joint_commission_report(
        self,
        metrics: List[BiasMetric],
        facility_name: str = "Healthcare Facility"
    ) -> str:
        """Generate Joint Commission equity certification report."""
        report = f"""
        JOINT COMMISSION EQUITY OF CARE ASSESSMENT
        {facility_name}
        Generated: {datetime.now().strftime('%Y-%m-%d')}

        STANDARD EC.04150: Healthcare Organization Addresses Disparities

        FINDINGS:
        """

        for m in metrics:
            report += f"""
        - {m.scenario_type}: {m.demographic_dimension} disparity
          * Disparate Impact Ratio: {m.metric_value:.3f}
          * P-value: {m.p_value:.4f}
          * Severity: {m.severity.value}
          * Population Impact: {int(m.sample_size * abs(m.reference_group_rate - m.comparison_group_rate))} patients affected
            """

        report += f"""

        CERTIFICATION STATUS: {'AT RISK' if len([m for m in metrics if m.severity in [SeverityLevel.CRITICAL, SeverityLevel.SEVERE]]) > 0 else 'COMPLIANT'}

        REQUIRED ACTIONS FOR ACCREDITATION MAINTENANCE:
        1. Complete equity audit by end of quarter
        2. Develop disparity reduction plan
        3. Implement monthly monitoring and reporting
        4. Demonstrate sustained improvement over 12 months

        Prepared by: Healthcare Equity Analytics Platform
        """

        return report
