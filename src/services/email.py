"""
Email service for newsletter delivery.
Supports Gmail SMTP and SendGrid.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from src.models.article import ContentItem, Category

logger = logging.getLogger(__name__)

# Category styling
CATEGORY_CONFIG = {
    Category.WORKFLOW: {"label": "WORKFLOW", "color": "#2563eb", "icon": "⚙️", "bg": "#eff6ff"},
    Category.LEADS: {"label": "LEADS", "color": "#16a34a", "icon": "📈", "bg": "#f0fdf4"},
    Category.FILES: {"label": "FILES", "color": "#9333ea", "icon": "📄", "bg": "#faf5ff"},
}


class EmailService:
    """Service for sending newsletters via email (Gmail SMTP or SendGrid)."""

    def __init__(self, config):
        self.config = config
        self.from_email = config.EMAIL_FROM
        self.to_email = config.EMAIL_TO
        self.use_gmail = bool(config.GMAIL_APP_PASSWORD)
        self.use_sendgrid = bool(config.SENDGRID_API_KEY) and not self.use_gmail

    def send_newsletter(
        self,
        executive_summary: str,
        items: List[ContentItem],
        tldr: List[str],
        date_str: str
    ) -> bool:
        """Send the newsletter via email."""
        subject = f"Mortgage AI Briefing - {date_str}"
        html_content = self._format_html(executive_summary, items, tldr)
        plain_content = self._format_plain(executive_summary, items, tldr)

        if self.use_gmail:
            return self._send_gmail(subject, plain_content, html_content)
        elif self.use_sendgrid:
            return self._send_sendgrid(subject, plain_content, html_content)
        else:
            logger.error("No email service configured")
            return False

    def _send_gmail(self, subject: str, plain: str, html: str) -> bool:
        """Send via Gmail SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Mortgage AI Newsletter <{self.from_email}>"
            msg["To"] = self.to_email

            msg.attach(MIMEText(plain, "plain"))
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.from_email, self.config.GMAIL_APP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Newsletter email sent via Gmail to {self.to_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("Gmail authentication failed - check EMAIL_FROM and GMAIL_APP_PASSWORD")
            return False
        except Exception as e:
            logger.error(f"Gmail send failed: {e}")
            return False

    def _send_sendgrid(self, subject: str, plain: str, html: str) -> bool:
        """Send via SendGrid API."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content, MimeType

            message = Mail(
                from_email=Email(self.from_email, "Mortgage AI Newsletter"),
                to_emails=To(self.to_email),
                subject=subject
            )
            message.content = [
                Content(MimeType.text, plain),
                Content(MimeType.html, html)
            ]

            sg = SendGridAPIClient(self.config.SENDGRID_API_KEY)
            response = sg.send(message)

            if response.status_code in (200, 201, 202):
                logger.info(f"Newsletter email sent via SendGrid to {self.to_email}")
                return True
            else:
                logger.error(f"SendGrid error: status {response.status_code}")
                return False

        except ImportError:
            logger.error("SendGrid library not installed")
            return False
        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            return False

    def _format_html(self, summary: str, items: List[ContentItem], tldr: List[str]) -> str:
        """Format the newsletter as HTML email with categories and TL;DR."""

        # Build TL;DR section
        tldr_html = ""
        for bullet in tldr:
            tldr_html += f'<li style="margin-bottom: 8px; color: #1a1a1a; font-size: 14px;">{self._escape_html(bullet)}</li>'

        # Group items by category
        grouped = {Category.WORKFLOW: [], Category.LEADS: [], Category.FILES: []}
        for item in items:
            cat = item.category or Category.WORKFLOW
            grouped[cat].append(item)

        # Build category sections
        sections_html = ""
        for category in [Category.WORKFLOW, Category.LEADS, Category.FILES]:
            cat_items = grouped[category]
            if not cat_items:
                continue

            config = CATEGORY_CONFIG[category]
            items_html = ""

            for item in cat_items:
                sentences = self._split_sentences(item.summary) if item.summary else []
                what = sentences[0] if sentences else (item.description[:200] if item.description else "")
                action = sentences[1] if len(sentences) > 1 else ""

                items_html += f"""
                <div style="padding: 16px 0; border-bottom: 1px solid #e5e7eb;">
                    <h4 style="margin: 0 0 6px 0; color: #1a1a1a; font-size: 15px; font-weight: 600;">
                        {self._escape_html(item.title[:80])}
                    </h4>
                    <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 12px;">
                        {self._escape_html(item.source)}
                    </p>
                    <p style="margin: 0 0 6px 0; color: #374151; font-size: 14px; line-height: 1.5;">
                        {self._escape_html(what)}
                    </p>
                    {"<p style='margin: 0 0 10px 0; color: " + config['color'] + "; font-size: 14px; font-weight: 500;'>→ " + self._escape_html(action) + "</p>" if action else ""}
                    <a href="{item.url}" style="color: {config['color']}; font-size: 13px; text-decoration: none;">
                        Read more →
                    </a>
                </div>
                """

            sections_html += f"""
            <div style="margin-bottom: 24px;">
                <div style="display: inline-block; background-color: {config['bg']}; color: {config['color']}; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">
                    {config['icon']} {config['label']}
                </div>
                {items_html}
            </div>
            """

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 24px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%); padding: 32px 40px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 700;">
                                Mortgage AI Briefing
                            </h1>
                            <p style="margin: 6px 0 0 0; color: #93c5fd; font-size: 14px;">
                                ⚙️ Workflow &nbsp;•&nbsp; 📈 Leads &nbsp;•&nbsp; 📄 Clean Files
                            </p>
                        </td>
                    </tr>

                    <!-- TL;DR Section -->
                    <tr>
                        <td style="padding: 28px 40px; background-color: #fefce8; border-bottom: 3px solid #fde047;">
                            <h2 style="margin: 0 0 14px 0; color: #854d0e; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;">
                                ⚡ TL;DR — 30 Second Scan
                            </h2>
                            <ul style="margin: 0; padding-left: 20px;">
                                {tldr_html}
                            </ul>
                        </td>
                    </tr>

                    <!-- Executive Summary -->
                    <tr>
                        <td style="padding: 28px 40px; background-color: #f8fafc;">
                            <h2 style="margin: 0 0 12px 0; color: #1e3a5f; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;">
                                Strategic Summary
                            </h2>
                            <p style="margin: 0; color: #374151; font-size: 15px; line-height: 1.6;">
                                {self._escape_html(summary)}
                            </p>
                        </td>
                    </tr>

                    <!-- Category Sections -->
                    <tr>
                        <td style="padding: 28px 40px;">
                            {sections_html}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #1e3a5f; text-align: center;">
                            <p style="margin: 0; color: #93c5fd; font-size: 12px;">
                                Curated daily for mortgage technology leaders
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    def _format_plain(self, summary: str, items: List[ContentItem], tldr: List[str]) -> str:
        """Format the newsletter as plain text."""
        lines = [
            "MORTGAGE AI BRIEFING",
            "=" * 50,
            "",
            "TL;DR — 30 SECOND SCAN",
            "-" * 30,
        ]

        for bullet in tldr:
            lines.append(f"• {bullet}")
        lines.append("")

        lines.extend([
            "STRATEGIC SUMMARY",
            "-" * 30,
            summary,
            "",
            "=" * 50,
        ])

        # Group by category
        grouped = {Category.WORKFLOW: [], Category.LEADS: [], Category.FILES: []}
        for item in items:
            cat = item.category or Category.WORKFLOW
            grouped[cat].append(item)

        for category in [Category.WORKFLOW, Category.LEADS, Category.FILES]:
            cat_items = grouped[category]
            if not cat_items:
                continue

            config = CATEGORY_CONFIG[category]
            lines.append("")
            lines.append(f"{config['icon']} {config['label']}")
            lines.append("-" * 30)

            for item in cat_items:
                lines.append(f"\n{item.title}")
                lines.append(f"[{item.source}]")

                if item.summary:
                    sentences = self._split_sentences(item.summary)
                    for j, sentence in enumerate(sentences[:2]):
                        if sentence.strip():
                            prefix = ">" if j == 0 else "→"
                            lines.append(f"{prefix} {sentence.strip()}")

                lines.append(item.url)
                lines.append("")

        lines.append("=" * 50)
        lines.append("Curated for mortgage tech leaders")

        return "\n".join(lines)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s for s in sentences if s.strip()]

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))
