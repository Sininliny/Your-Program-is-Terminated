import os
import sys
import signal
import smtplib
import traceback
import socket
import socks
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from types import FrameType
from typing import Optional, Any

class SimpleEmailServer:
    """
    A simple wrapper client to handle SMTP connections and sending emails.
    """
    def __init__(self, smtp_host: str, smtp_port: int, sender_email: str, sender_password: str, http_proxy: str = None, https_proxy: str = None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.http_proxy = http_proxy
        self.https_proxy = https_proxy
        self.proxy_info = None
        if self.http_proxy:
            self.proxy_info = self._parse_proxy(self.http_proxy)
        elif self.https_proxy:
            self.proxy_info = self._parse_proxy(self.https_proxy)

    def _parse_proxy(self, proxy_url: str):
        from urllib.parse import urlparse
        parsed = urlparse(proxy_url)
        return {
            'type': 'http' if parsed.scheme in ['http', 'https'] else 'socks5',
            'host': parsed.hostname,
            'port': parsed.port or 8080
        }

    def send(self, recipient: str, subject: str, body: str) -> bool:
        """
        Connects to the SMTP server and sends the email.
        """
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            print(f"[TERMINATION_MONITOR] Connecting to SMTP server {self.smtp_host}:{self.smtp_port}...")
            # Set proxy if configured
            if self.proxy_info:
                if self.proxy_info['type'] == 'http':
                    socks.setdefaultproxy(socks.PROXY_TYPE_HTTP, self.proxy_info['host'], self.proxy_info['port'])
                else:
                    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, self.proxy_info['host'], self.proxy_info['port'])
                socket.socket = socks.socksocket
            # Establish secure connection
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls() # Upgrade to secure connection

            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, recipient, msg.as_string())
            server.quit()
            print("[TERMINATION_MONITOR] Email notification sent successfully.")
            return True
        except Exception as e:
            print(f"[TERMINATION_MONITOR] Failed to send email. Error: {e}")
            return False

class termination_monitor:
    """
    The main monitoring class. Use it as a Context Manager (with statement).
    It captures exceptions, interrupts (Ctrl+C), and termination signals.
    """
    def __init__(self, 
                 recipient_email: Optional[str] = None, 
                 smtp_host: Optional[str] = None,
                 smtp_port: Optional[int] = None,
                 sender_email: Optional[str] = None,
                 sender_password: Optional[str] = None):
        
        # 1. Configuration Priority: Instance Argument > System Environment Variable
        self.recipient_email = recipient_email or os.getenv('TERMINATION_MONITOR_RECIPIENT_EMAIL')
        self.smtp_host = smtp_host or os.getenv('TERMINATION_MONITOR_SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(smtp_port or os.getenv('TERMINATION_MONITOR_SMTP_PORT', 587))
        self.sender_email = sender_email or os.getenv('TERMINATION_MONITOR_SENDER_EMAIL')
        self.sender_password = sender_password or os.getenv('TERMINATION_MONITOR_SENDER_PASSWORD')
        self.http_proxy = os.getenv('TERMINATION_MONITOR_HTTP_PROXY')
        self.https_proxy = os.getenv('TERMINATION_MONITOR_HTTPS_PROXY')

        self.mailer = None
        if self.sender_email and self.sender_password and self.recipient_email:
            self.mailer = SimpleEmailServer(self.smtp_host, self.smtp_port, self.sender_email, self.sender_password, http_proxy=self.http_proxy, https_proxy=self.https_proxy)
        else:
            print("[TERMINATION_MONITOR] Warning: Email configuration incomplete. Email alerts will be disabled.")

        self._original_sigint = None
        self._original_sigterm = None

    def __enter__(self):
        start_time = datetime.now()
        print(f"[TERMINATION_MONITOR] Monitoring started at {start_time}...")
        
        # Capture SIGTERM (Termination signal, like 'kill' command)
        self._original_sigterm = signal.signal(signal.SIGTERM, self._handle_signal)
        # Capture SIGINT (Ctrl+C) - usually handled by KeyboardInterrupt, but explicit is safe
        self._original_sigint = signal.signal(signal.SIGINT, self._handle_signal)
        
        # Send "Activated" Email ---
        if self.mailer:
            hostname = socket.gethostname()
            subject = "[INFO] Monitoring Activated: Your Program Started"
            body = (
                f"Program monitoring has started successfully.\n\n"
                f"Host Machine: {hostname}\n"
                f"Start Time: {start_time}\n"
                f"----------------------------------------\n"
                f"You will receive another email when the program terminates (success or failure).\n"
            )
            print("[TERMINATION_MONITOR] Sending start-up notification...")
            self.mailer.send(self.recipient_email, subject, body)
        # --------------------------------------------

        return self
    
    def __exit__(self, exc_type, exc_value, tb):
        """
        This method is called when the code block finishes, either successfully or with an error.
        """
        end_time = datetime.now()
        status = "Success"
        error_details = "None"
        
        # Restore original signal handlers
        signal.signal(signal.SIGTERM, self._original_sigterm)
        signal.signal(signal.SIGINT, self._original_sigint)

        # Check if an exception occurred
        if exc_type:
            status = "Crashed / Terminated"
            # Format the traceback
            error_details = "".join(traceback.format_exception(exc_type, exc_value, tb))
            print(f"\n[TERMINATION_MONITOR] Exception detected:\n{error_details}")
            
            # If it is a KeyboardInterrupt or our custom Signal Exit, handle gracefully
            if exc_type is KeyboardInterrupt:
                status = "Interrupted by User (Ctrl+C)"
                error_details = "User manually stopped the program."

        self._trigger_alert(status, error_details, end_time)
        
        # Return False to propagate the exception (so the program actually crashes/stops), 
        # or True to suppress it. We propagate it.
        return False 

    def _handle_signal(self, signum: int, frame: FrameType):
        """
        Custom signal handler to translate system signals into Python exceptions 
        so __exit__ can catch them.
        """
        sig_name = signal.Signals(signum).name
        print(f"\n[TERMINATION_MONITOR] Signal received: {sig_name}")
        # Raising SystemExit ensures __exit__ is called
        sys.exit(f"Process terminated by signal {sig_name}")

    def _trigger_alert(self, status: str, details: str, time: datetime):
        if not self.mailer:
            print("[TERMINATION_MONITOR] No email configuration. Skipping alert.")
            return

        print("[TERMINATION_MONITOR] Preparing termination report...")
        
        hostname = socket.gethostname()
        subject = f"[ALERT] Your Program is Terminated: {status}"
        
        body = (
            f"Your program monitoring report:\n\n"
            f"Host Machine: {hostname}\n"
            f"Status: {status}\n"
            f"Time: {time}\n"
            f"----------------------------------------\n"
            f"Error Logs / Traceback:\n"
            f"{details}\n"
            f"----------------------------------------\n"
            f"This is an automated message from Your_Program_is_Terminated library."
        )

        self.mailer.send(self.recipient_email, subject, body)
