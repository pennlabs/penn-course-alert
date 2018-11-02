import logging
from celery import shared_task

from .models import *
from pca import api
from options.models import get_value, get_bool

logger = logging.getLogger(__name__)


@shared_task(name='pca.tasks.load_courses')
def load_courses(query='', semester=None):
    if semester is None:
        semester = get_value('SEMESTER')

    logger.info('load in courses with prefix %s from %s' % (query, semester))
    results = api.get_courses(query, semester)

    for course in results:
        upsert_course_from_opendata(course, semester)


@shared_task(name='pca.tasks.send_alert')
def send_alert(registration):
    result = registration.alert()
    return {
        'result': result,
        'task': 'pca.tasks.send_alert'
    }


@shared_task(name='pca.tasks.send_alerts_for')
def send_alerts_for(section_code, registrations, semester):
    new_data = api.get_course(section_code, semester)  # THIS IS A SLOW API CALL
    course, section = get_course_and_section(section_code, semester)
    was_open = section.is_open
    if new_data is not None:
        upsert_course_from_opendata(new_data, semester)
        now_open = section.is_open
        if now_open and not was_open:  # is this python or pseudocode ;)?
            for reg in registrations:
                send_alert.delay(reg)  # This is a


@shared_task(name='pca.tasks.prepare_alerts')
def prepare_alerts(semester=None):
    if semester is None:
        semester = get_value('SEMESTER')

    if not get_bool('SEND_ALERTS', False):
        return {'task': 'pca.tasks.prepare_alerts', 'result': 'aborted -- SEND_ALERTS=False'}

    alerts = {}
    for reg in Registration.objects.filter(section__course__semester=semester, notification_sent=False):
        # Group registrations into buckets based on their associated section
        sect = reg.section.normalized
        if sect in alerts:
            alerts[sect].append(reg)
        else:
            alerts[sect] = [reg]

    for section_code, registrations in alerts.items():
        send_alerts_for.delay(section_code, registrations, semester)

    return {'task': 'pca.tasks.prepare_alerts', 'result': 'complete'}
