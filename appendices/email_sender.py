import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
from datetime import datetime

class EmailSender:
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = os.getenv("EMAIL_USER")
        self.sender_password = os.getenv("EMAIL_PASSWORD")

    def send_violation_notification(self, recipient_email, speed, timestamp, image_path):
        """Send violation notification email"""
        if not all([self.sender_email, self.sender_password]):
            print("Email credentials not configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = "Speed Violation Notice"

            # Format timestamp
            violation_time = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            formatted_time = violation_time.strftime("%Y-%m-%d %H:%M:%S")

            # Create email body
            body = f"""
            Dear Driver,

            This is an automated notification regarding a speed violation detected on {formatted_time}.

            Details of the violation:
            - Speed: {speed:.1f} m/s
            - Time: {formatted_time}

            Please find attached the violation image for your reference.

            This is an automated system. If you believe this is an error, please contact the traffic department.

            Best regards,
            Traffic Monitoring System
            """

            msg.attach(MIMEText(body, 'plain'))

            # Attach violation image
            with open(image_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment', 
                             filename=os.path.basename(image_path))
                msg.attach(img)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            print(f"Violation notification sent to {recipient_email}")
            return True

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False 