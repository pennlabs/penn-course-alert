from django.core.management.base import BaseCommand, CommandError

from pca.models import *
from pca import api
from pca.tasks import prepare_alerts


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
        prepare_alerts.delay()
