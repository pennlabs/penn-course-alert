from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from pca import api, models
from pca.tasks import load_courses


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

        load_courses(query, semester)
