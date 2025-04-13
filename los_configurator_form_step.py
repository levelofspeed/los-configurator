
# los_configurator_form_step.py (примерная структура, упрощённо)

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import os

EMAIL_ADDRESS = "levelofspeed@gmail.com"
EMAIL_PASSWORD = "wjfr vzzl kezg mikh"  # App Password

def send_email_with_pdf(receiver_email, pdf_file_path):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = receiver_email
    msg["Subject"] = "Your Level of Speed Chiptuning Result"

    body = "Attached is your personalized chiptuning result from Level of Speed."
    msg.attach(MIMEText(body, "plain"))

    with open(pdf_file_path, "rb") as f:
        pdf = MIMEApplication(f.read(), _subtype="pdf")
        pdf.add_header("Content-Disposition", "attachment", filename=os.path.basename(pdf_file_path))
        msg.attach(pdf)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# Пример вызова:
# send_email_with_pdf("client@example.com", "result.pdf")
