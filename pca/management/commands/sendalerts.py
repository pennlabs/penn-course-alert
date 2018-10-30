from django.core.management.base import BaseCommand, CommandError

from pca.models import *
from pca import api


def send_alerts(section_code, registrations, semester, should_send=False):
    new_data = api.get_course(section_code, semester)
    course, section = get_course_and_section(section_code, semester)
    was_open = section.is_open
    if new_data is not None:
        upsert_course_from_opendata(new_data, semester)
        now_open = section.is_open
        if now_open and not was_open:  # is this python or pseudocode ;)?
            for reg in registrations:
                if should_send:
                    reg.alert()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--noMock', action="store_true", help='actually send alerts')

    def handle(self, *args, **options):
        should_send = options['noMock']
        semester = get_current_semester()
        alerts = {}
        for reg in Registration.objects.filter(section__course__semester=semester, notification_sent=False):
            # Group registrations into buckets based on their associated section
            sect = reg.section.normalized
            if sect in alerts:
                alerts[sect].append(reg)
            else:
                alerts[sect] = [reg]

        for section_code, registrations in alerts.items():
            send_alerts(section_code, registrations, semester, should_send)
