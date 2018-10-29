from smtplib import SMTP
from email.mime.text import MIMEText

from django.template import loader
from django.conf import settings


def send_alert(registration):
    template = loader.get_template('email_alert.html')

    msg = MIMEText(template.render({
        'course': registration.section.normalized,
        'signup_url': registration.resub_url,
        'brand': 'Penn Course Alert'
    }), 'html')

    msg['Subject'] = '%s is now open!' % registration.section.normalized
    msg['From'] = 'Penn Course Alert <team@penncoursealert.com>'
    msg['To'] = registration.email
    with SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
