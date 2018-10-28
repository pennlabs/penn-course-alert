from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from pca import api, models


class Command(BaseCommand):
    help = 'Load in class data to the database'

    def add_arguments(self, parser):
        parser.add_argument('semester',
                            nargs='?',
                            type=str,
                            default=models.get_current_semester())
        parser.add_argument('query',
                            nargs='?',
                            type=str,
                            default='CIS')

    def handle(self, *args, **options):
        semester = options['semester'].split('=')[-1]
        query = options['query'].split('=')[-1]

        self.stdout.write('load in courses with prefix %s from %s' % (query, semester))
        results = api.get_courses(query, semester)

        for course in results:
            models.upsert_course_from_opendata(course, semester)
