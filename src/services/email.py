"""
Email service for newsletter delivery.
Supports Gmail SMTP and SendGrid.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from src.models.article import ContentItem

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending newsletters via email (Gmail SMTP or SendGrid)."""

    def __init__(self, config):
        self.config = config
        self.from_email = config.EMAIL_FROM
        self.to_email = config.EMAIL_TO

        # Determine which service to use
        self.use_gmail = bool(config.GMAIL_APP_PASSWORD)
        self.use_sendgrid = bool(config.SENDGRID_API_KEY) and not self.use_gmail

    def send_newsletter(
        self,
        executive_summary: str,
        items: List[ContentItem],
        date_str: str
    ) -> bool:
        """
        Send the newsletter via email.

        Args:
            executive_summary: The executive summary text
            items: List of top ContentItem objects
            date_str: Formatted date string for the subject

        Returns:
            True if successful, False otherwise
        """
        subject = f"Mortgage AI Briefing - {date_str}"
        html_content = self._format_html(executive_summary, items)
        plain_content = self._format_plain(executive_summary, items)

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

    def _format_html(self, summary: str, items: List[ContentItem]) -> str:
        """Format the newsletter as HTML email."""
        items_html = ""
        for i, item in enumerate(items, 1):
            # Get summary sentences
            if item.summary:
                sentences = self._split_sentences(item.summary)
                what = sentences[0] if sentences else ""
                action = sentences[1] if len(sentences) > 1 else ""
            else:
                what = item.description[:200] if item.description else ""
                action = ""

            items_html += f"""
            <tr>
                <td style="padding: 20px 0; border-bottom: 1px solid #e0e0e0;">
                    <h3 style="margin: 0 0 8px 0; color: #1a1a1a; font-size: 16px;">
                        {i}. {self._escape_html(item.title)}
                    </h3>
                    <p style="margin: 0 0 12px 0; color: #666; font-size: 13px;">
                        {self._escape_html(item.source)}
                    </p>
                    <p style="margin: 0 0 8px 0; color: #333; font-size: 14px; line-height: 1.5;">
                        {self._escape_html(what)}
                    </p>
                    {"<p style='margin: 0 0 12px 0; color: #0066cc; font-size: 14px; font-weight: 500;'>→ " + self._escape_html(action) + "</p>" if action else ""}
                    <a href="{item.url}" style="color: #0066cc; font-size: 13px; text-decoration: none;">
                        Read more →
                    </a>
                </td>
            </tr>
            """

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%); padding: 30px 40px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">
                                Mortgage AI Briefing
                            </h1>
                            <p style="margin: 8px 0 0 0; color: #a0c4ff; font-size: 14px;">
                                Workflow • Leads • Clean Files
                            </p>
                        </td>
                    </tr>

                    <!-- Executive Summary -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f8fafc;">
                            <h2 style="margin: 0 0 12px 0; color: #1a365d; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">
                                Strategic Summary
                            </h2>
                            <p style="margin: 0; color: #333; font-size: 15px; line-height: 1.6;">
                                {self._escape_html(summary)}
                            </p>
                        </td>
                    </tr>

                    <!-- Items -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <h2 style="margin: 0 0 20px 0; color: #1a365d; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">
                                Top 5 Actionable Items
                            </h2>
                            <table width="100%" cellpadding="0" cellspacing="0">
                                {items_html}
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #f8fafc; text-align: center;">
                            <p style="margin: 0; color: #666; font-size: 12px;">
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

    def _format_plain(self, summary: str, items: List[ContentItem]) -> str:
        """Format the newsletter as plain text."""
        lines = [
            "MORTGAGE AI BRIEFING",
            "=" * 40,
            "",
            "STRATEGIC SUMMARY",
            "-" * 20,
            summary,
            "",
            "=" * 40,
            "TOP 5 ACTIONABLE ITEMS",
            "=" * 40,
            ""
        ]

        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item.title}")
            lines.append(f"   [{item.source}]")
            lines.append("")

            if item.summary:
                sentences = self._split_sentences(item.summary)
                for j, sentence in enumerate(sentences[:2]):
                    if sentence.strip():
                        prefix = ">" if j == 0 else "→"
                        lines.append(f"   {prefix} {sentence.strip()}")

            lines.append("")
            lines.append(f"   {item.url}")
            lines.append("")
            lines.append("-" * 40)
            lines.append("")

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
