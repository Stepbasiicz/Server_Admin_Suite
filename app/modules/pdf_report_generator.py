# -*- coding: utf-8 -*-
"""
Executive Server Audit & Security Compliance PDF Report Generator.
Generates publication-quality PDF reports with pass/fail badges,
resource utilization, and remediation action items using ReportLab.
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)


class PDFReportGenerator:
    """Generates comprehensive PDF security audit reports."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def generate_audit_report(
        self,
        server_name: str,
        host: str,
        linux_audit: Optional[Dict[str, Any]] = None,
        mysql_audit: Optional[Dict[str, Any]] = None,
        net_audit: Optional[Dict[str, Any]] = None,
        port_audit: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Builds and saves the complete audit PDF report.
        Returns the absolute filepath of the generated PDF.
        """
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_host = host.replace(".", "_").replace(":", "_")
        filename = f"Server_Audit_{safe_host}_{timestamp_str}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1A365D"),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#4A5568"),
            spaceAfter=12
        )
        sec_heading = ParagraphStyle(
            "SecHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#2B6CB0"),
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#2D3748")
        )
        body_bold = ParagraphStyle(
            "BodyBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1A202C")
        )
        badge_pass = ParagraphStyle(
            "BadgePass",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#22543D")
        )
        badge_warn = ParagraphStyle(
            "BadgeWarn",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#744210")
        )
        badge_fail = ParagraphStyle(
            "BadgeFail",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#742A2A")
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("SERVER HEALTH & SECURITY AUDIT REPORT", title_style))
        story.append(Paragraph("Enterprise Infrastructure Governance & Compliance Assessment", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=10))

        # 2. Server Metadata Table
        os_info = linux_audit.get("os_info", {}) if linux_audit else {}
        meta_data = [
            [
                Paragraph("<b>Server Name:</b>", body_style),
                Paragraph(server_name or "Target Host", body_style),
                Paragraph("<b>Audit Date:</b>", body_style),
                Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), body_style),
            ],
            [
                Paragraph("<b>Target Host / IP:</b>", body_style),
                Paragraph(host, body_bold),
                Paragraph("<b>Auditor System:</b>", body_style),
                Paragraph("Soft4U Enterprise Suite", body_style),
            ],
            [
                Paragraph("<b>OS Distribution:</b>", body_style),
                Paragraph(os_info.get("distro", "N/A"), body_style),
                Paragraph("<b>Kernel & Arch:</b>", body_style),
                Paragraph(f"{os_info.get('kernel', 'N/A')} ({os_info.get('arch', 'N/A')})", body_style),
            ]
        ]
        meta_table = Table(meta_data, colWidths=[110, 150, 100, 160])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # 3. Overall Security Scorecard
        score = linux_audit.get("security_score", 100) if linux_audit else 100
        grade = linux_audit.get("security_grade", "A") if linux_audit else "A"
        grade_color = "#38A169" if score >= 85 else "#D69E2E" if score >= 70 else "#E53E3E"

        scorecard_data = [
            [
                Paragraph(f"<b>Overall Security Score: <font color='{grade_color}' size=14>{score}/100 (Grade {grade})</font></b>", body_bold),
                Paragraph(
                    "<b>Assessment Verdict:</b> " + (
                        "<font color='#38A169'><b>SECURE & COMPLIANT</b></font>" if score >= 85
                        else "<font color='#D69E2E'><b>ATTENTION REQUIRED</b></font>" if score >= 70
                        else "<font color='#E53E3E'><b>CRITICAL RISKS DETECTED</b></font>"
                    ),
                    body_style
                )
            ]
        ]
        score_table = Table(scorecard_data, colWidths=[260, 260])
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(grade_color)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 12))

        # 4. Section: Security Baseline Findings (Firewall, Patch, Hardening)
        story.append(Paragraph("1. Security Baseline & Hardening Findings", sec_heading))
        findings = []
        if linux_audit and "security_findings" in linux_audit:
            findings.extend(linux_audit["security_findings"])
        if mysql_audit and "security_checks" in mysql_audit:
            for c in mysql_audit["security_checks"]:
                findings.append({"category": f"MySQL: {c['check']}", "status": c["status"], "desc": c["desc"]})

        if findings:
            find_rows = [
                [
                    Paragraph("<b>Category</b>", body_bold),
                    Paragraph("<b>Status</b>", body_bold),
                    Paragraph("<b>Finding & Assessment Details</b>", body_bold),
                ]
            ]
            for f in findings:
                stat = f.get("status", "PASS")
                if stat == "PASS":
                    st_p = Paragraph("<font color='#22543D'><b>[ PASS ]</b></font>", badge_pass)
                    bg = colors.HexColor("#F0FFF4")
                elif stat == "WARNING":
                    st_p = Paragraph("<font color='#B7791F'><b>[ WARNING ]</b></font>", badge_warn)
                    bg = colors.HexColor("#FFFFF0")
                else:
                    st_p = Paragraph("<font color='#E53E3E'><b>[ CRITICAL ]</b></font>", badge_fail)
                    bg = colors.HexColor("#FFF5F5")

                find_rows.append([
                    Paragraph(f.get("category", ""), body_style),
                    st_p,
                    Paragraph(f.get("desc", ""), body_style)
                ])

            find_table = Table(find_rows, colWidths=[120, 80, 320])
            find_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(find_table)
        else:
            story.append(Paragraph("No security findings recorded.", body_style))
        story.append(Spacer(1, 12))

        # 5. Section: Linux System Health & Resources
        if linux_audit and linux_audit.get("success"):
            story.append(Paragraph("2. Linux System Resources & Storage Health", sec_heading))
            res = linux_audit.get("resources", {})
            up = linux_audit.get("uptime_load", {})
            fw = linux_audit.get("firewall", {})
            pt = linux_audit.get("patches", {})

            res_data = [
                [
                    Paragraph("<b>CPU Cores:</b>", body_style),
                    Paragraph(f"{res.get('cpu_cores', 1)} Cores", body_style),
                    Paragraph("<b>Load Average:</b>", body_style),
                    Paragraph(f"{up.get('load_1m', 0.0)} / {up.get('load_5m', 0.0)} / {up.get('load_15m', 0.0)}", body_style),
                ],
                [
                    Paragraph("<b>Memory Usage:</b>", body_style),
                    Paragraph(f"{res.get('ram_used_mb', 0):,} MB / {res.get('ram_total_mb', 0):,} MB ({res.get('ram_pct', 0)}%)", body_style),
                    Paragraph("<b>Swap Usage:</b>", body_style),
                    Paragraph(f"{res.get('swap_used_mb', 0):,} MB / {res.get('swap_total_mb', 0):,} MB ({res.get('swap_pct', 0)}%)", body_style),
                ],
                [
                    Paragraph("<b>Firewall Status:</b>", body_style),
                    Paragraph(
                        f"<font color='{'#22543D' if fw.get('is_active') else '#E53E3E'}'><b>{fw.get('status_detail', 'N/A')}</b></font>",
                        body_style
                    ),
                    Paragraph("<b>Pending Patches:</b>", body_style),
                    Paragraph(f"Total: {pt.get('total_upgrades', 0)} (Security: {pt.get('security_upgrades', 0)})", body_style),
                ]
            ]
            res_table = Table(res_data, colWidths=[110, 150, 110, 150])
            res_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#EDF2F7")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(res_table)
            story.append(Spacer(1, 8))

            # Disk Partition Breakdown
            disks = linux_audit.get("disks", [])
            if disks:
                d_rows = [
                    [
                        Paragraph("<b>Filesystem</b>", body_bold),
                        Paragraph("<b>Mount</b>", body_bold),
                        Paragraph("<b>Size</b>", body_bold),
                        Paragraph("<b>Used</b>", body_bold),
                        Paragraph("<b>Available</b>", body_bold),
                        Paragraph("<b>Usage %</b>", body_bold),
                    ]
                ]
                for d in disks:
                    pct = d.get("use_pct", 0)
                    color_tag = "#E53E3E" if pct >= 90 else "#D69E2E" if pct >= 80 else "#2D3748"
                    d_rows.append([
                        Paragraph(d.get("filesystem", ""), body_style),
                        Paragraph(d.get("mount", ""), body_style),
                        Paragraph(d.get("size", ""), body_style),
                        Paragraph(d.get("used", ""), body_style),
                        Paragraph(d.get("avail", ""), body_style),
                        Paragraph(f"<font color='{color_tag}'><b>{pct}%</b></font>", body_style)
                    ])

                d_table = Table(d_rows, colWidths=[110, 100, 70, 70, 70, 100])
                d_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]))
                story.append(d_table)
            story.append(Spacer(1, 12))

        # 6. Section: MySQL Database Audit
        if mysql_audit and mysql_audit.get("success"):
            story.append(Paragraph("3. MySQL / MariaDB Health & Storage", sec_heading))
            db_data = [
                [
                    Paragraph("<b>MySQL Version:</b>", body_style),
                    Paragraph(mysql_audit.get("version", "N/A"), body_style),
                    Paragraph("<b>Buffer Pool:</b>", body_style),
                    Paragraph(f"{mysql_audit.get('buffer_pool_mb', 0)} MB", body_style),
                ],
                [
                    Paragraph("<b>Threads Connected:</b>", body_style),
                    Paragraph(f"{mysql_audit.get('threads_connected', 0)} / {mysql_audit.get('max_connections', 151)}", body_style),
                    Paragraph("<b>Uptime:</b>", body_style),
                    Paragraph(f"{mysql_audit.get('uptime_seconds', 0) // 3600} hours", body_style),
                ]
            ]
            db_table = Table(db_data, colWidths=[110, 150, 110, 150])
            db_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(db_table)
            story.append(Spacer(1, 6))

            # Database Schemas Table
            schemas = mysql_audit.get("schemas", [])[:6]
            if schemas:
                sch_rows = [
                    [
                        Paragraph("<b>Database Schema</b>", body_bold),
                        Paragraph("<b>Tables</b>", body_bold),
                        Paragraph("<b>Size (MB)</b>", body_bold),
                    ]
                ]
                for s in schemas:
                    sch_rows.append([
                        Paragraph(str(s.get("schema_name", "")), body_style),
                        Paragraph(str(s.get("table_count", 0)), body_style),
                        Paragraph(f"{float(s.get('size_mb', 0.0)):,.2f} MB", body_style),
                    ])
                sch_table = Table(sch_rows, colWidths=[220, 100, 200])
                sch_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]))
                story.append(sch_table)
            story.append(Spacer(1, 12))

        # 7. Section: Network Diagnostic & Port Scanner
        if net_audit or port_audit:
            story.append(Paragraph("4. Network & Port Exposure Analysis", sec_heading))
            if net_audit:
                ping_txt = f"Latency Avg: {net_audit.get('avg_ms', 0)} ms | Packet Loss: {net_audit.get('packet_loss_pct', 0)}% ({net_audit.get('status_text', '')})"
                story.append(Paragraph(f"<b>ICMP Ping Test:</b> {ping_txt}", body_style))
                story.append(Spacer(1, 6))

            if port_audit:
                open_ports = [p for p in port_audit if p.get("status") == "OPEN"]
                p_rows = [
                    [
                        Paragraph("<b>Port</b>", body_bold),
                        Paragraph("<b>Service</b>", body_bold),
                        Paragraph("<b>Status</b>", body_bold),
                        Paragraph("<b>Exposure Risk Level</b>", body_bold),
                    ]
                ]
                for p in open_ports[:10]:
                    risk = p.get("risk", "Normal")
                    color_tag = "#E53E3E" if "High" in risk else "#D69E2E" if "Medium" in risk else "#2B6CB0"
                    p_rows.append([
                        Paragraph(str(p.get("port")), body_style),
                        Paragraph(p.get("service", ""), body_style),
                        Paragraph("<font color='#38A169'><b>OPEN</b></font>", body_style),
                        Paragraph(f"<font color='{color_tag}'><b>{risk}</b></font>", body_style)
                    ])

                if len(p_rows) > 1:
                    p_table = Table(p_rows, colWidths=[80, 140, 100, 200])
                    p_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]))
                    story.append(p_table)
                else:
                    story.append(Paragraph("No open ports found or all scanned ports are closed.", body_style))
            story.append(Spacer(1, 16))

        # 8. Auditor Sign-off block
        story.append(Spacer(1, 10))
        sign_data = [
            [
                Paragraph("<b>Audited By:</b> System Administrator", body_style),
                Paragraph("<b>Approved By:</b> IT Director / Security Officer", body_style),
            ],
            [
                Paragraph("Signature: __________________________", body_style),
                Paragraph("Signature: __________________________", body_style),
            ],
            [
                Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", body_style),
                Paragraph("Date: __________________________", body_style),
            ]
        ]
        sign_table = Table(sign_data, colWidths=[260, 260])
        sign_table.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(KeepTogether(sign_table))

        # Build document
        doc.build(story)
        return os.path.abspath(filepath)
