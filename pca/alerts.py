from abc import ABC, abstractmethod
from smtplib import SMTP
from email.mime.text import MIMEText

from django.template import loader
from django.conf import settings

from twilio.rest import Client


class Alert(ABC):
    def __init__(self, template, reg):
        t = loader.get_template(template)
        self.text = t.render({
            'course': reg.section.normalized,
            'signup_url': reg.resub_url,
            'brand': 'Penn Course Alert'
        })
        self.registration = reg

    @abstractmethod
    def send_alert(self):
        pass


class Email(Alert):
    def __init__(self, reg):
        super().__init__('email_alert.html', reg)

    def send_alert(self):
        if self.registration.email is None:
            return False

        msg = MIMEText(self.text, 'html')
        msg['Subject'] = '%s is now open!' % self.registration.section.normalized
        msg['From'] = 'Penn Course Alert <team@penncoursealert.com>'
        msg['To'] = self.registration.email
        with SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
            return True


class Text(Alert):
    def __init__(self, reg):
        super().__init__('text_alert.txt', reg)

    def send_alert(self):
        if self.registration.phone is None:
            return False

        client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            to=self.registration.phone,
            from_=settings.TWILIO_NUMBER,
            body=self.text
        )
        if msg.sid is not None:
            return True

