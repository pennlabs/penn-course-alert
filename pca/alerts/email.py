import smtplib
from email.mime.text import MIMEText

from django.template import loader


def send_alert(registration):
    template = loader.get_template('email_alert.html')
    msg = MIMEText(template.render({
        'course': registration.section.query_string
    }))
