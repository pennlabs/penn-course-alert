import redis
import json
import logging
from celery import shared_task

from .models import *
from pca import api
from options.models import get_value, get_bool

from django.conf import settings

logger = logging.getLogger(__name__)
r = redis.Redis.from_url(settings.REDIS_URL)


def generate_course_json(semester=None, use_cache=True):
    if semester is None:
        semester = get_value('SEMESTER')

    if use_cache:
        sections = r.get('sections')
        if sections is not None:
            return json.loads(sections)

    sections = []
    for section in Section.objects.filter(course__semester=semester):
        # {'section_id': section_id, 'course_title': course_title, 'instructors': instructors,
        #  'meeting_days': meeting_days}
        # meetings = json.loads('{"meetings": "%s"}' % section.meeting_times)['meetings']
        if section.meeting_times is not None and len(section.meeting_times) > 0:
            meetings = json.loads(section.meeting_times)
        else:
            meetings = []
        sections.append({
            'section_id': section.normalized,
            'course_title': section.course.title,
            'instructors': list(map(lambda i: i.name, section.instructors.all())),
            'meeting_days': meetings
        })

    serialized_sections = json.dumps(sections)
    r.set('sections', serialized_sections)
    return sections


@shared_task(name='pca.tasks.demo_alert')
def demo_alert():
    return {'result': 'executed', 'name': 'pca.tasks.demo_alert'}


@shared_task(name='pca.tasks.demo_task')
def demo_task():
    return {'result': 'executed', 'name': 'pca.tasks.demo_task'}


@shared_task(name='pca.tasks.load_courses')
def load_courses(query='', semester=None):
    if semester is None:
        semester = get_value('SEMESTER')

    logger.info('load in courses with prefix %s from %s' % (query, semester))
    results = api.get_courses(query, semester)

    for course in results:
        upsert_course_from_opendata(course, semester)

    return {'result': 'succeeded', 'name': 'pca.tasks.load_courses'}


@shared_task(name='pca.tasks.send_alert')
def send_alert(reg_id):
    print("id: " + str(reg_id))
    result = Registration.objects.get(id=reg_id).alert()
    return {
        'result': result,
        'task': 'pca.tasks.send_alert'
    }


# current API is rate-limited to 100/minute, so only spin off a single
@shared_task(name='pca.tasks.send_alerts_for', rate_limit='100/m')
def send_alerts_for(section_code, registrations, semester):
    new_data = api.get_course(section_code, semester)  # THIS IS A SLOW API CALL
    _, section = get_course_and_section(section_code, semester)
    was_open = section.is_open
    if new_data is not None:
        upsert_course_from_opendata(new_data, semester)
        now_open = is_section_open(new_data)
        print("was_open:" + str(was_open) + " | now_open:"+str(now_open))
        if now_open and not was_open:  # is this python or pseudocode ;)?
            for reg_id in registrations:
                send_alert.delay(reg_id)  # This is a


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
            alerts[sect].append(reg.id)
        else:
            alerts[sect] = [reg.id]

    for section_code, registrations in alerts.items():
        send_alerts_for.delay(section_code, registrations, semester)

    return {'task': 'pca.tasks.prepare_alerts', 'result': 'complete'}
