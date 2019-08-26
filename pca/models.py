import json
from enum import Enum, auto
from urllib.parse import urlencode
import logging
from smtplib import SMTPRecipientsRefused
import re

from django.db import models
from django.conf import settings
from django.utils import timezone
from django import urls

from .alerts import Email, Text
from shortener.models import Url
from options.models import get_value, get_bool

import phonenumbers  # library for parsing and formatting phone numbers.

logger = logging.getLogger(__name__)


def get_current_semester():
    return get_value('SEMESTER', '2019A')


class Instructor(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.TextField()

    def __str__(self):
        return self.name


class Course(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    department = models.CharField(max_length=8)
    code = models.CharField(max_length=8)
    semester = models.CharField(max_length=5)

    title = models.TextField()
    description = models.TextField(blank=True)

    def __str__(self):
        return '%s %s' % (self.course_id, self.semester)

    @property
    def course_id(self):
        return '%s-%s' % (self.department, self.code)


class Section(models.Model):
    STATUS_CHOICES = (
        ('O', 'Open'),
        ('C', 'Closed'),
        ('X', 'Cancelled'),
        ('', 'Unlisted'),
    )

    class Meta:
        unique_together = (('code', 'course'), )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    code = models.CharField(max_length=16)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    status = models.CharField(max_length=4, choices=STATUS_CHOICES)

    capacity = models.IntegerField(default=0)
    activity = models.CharField(max_length=50, null=True, blank=True)
    meeting_times = models.TextField(blank=True)
    instructors = models.ManyToManyField(Instructor)

    def __str__(self):
        return '%s-%s %s' % (self.course.course_id, self.code, self.course.semester)

    @property
    def normalized(self):
        """String used for querying updates to this section with the Penn API"""
        return '%s-%s' % (self.course.course_id, self.code)

    @property
    def is_open(self):
        return self.status == 'O'


course_regexes = [
    re.compile(r'([A-Za-z]+) *(\d{3})(\d{3})'),
    re.compile(r'([A-Za-z]+) *-(\d{3})-(\d{3})'),
]


def separate_course_code(course_code):
    course_code = course_code.replace(' ', '').upper()
    for regex in course_regexes:
        m = regex.match(course_code)
        if m is not None:
            return m.group(1), m.group(2), m.group(3)

    msg = f'Course code could not be parsed: {course_code}'
    logger.exception(msg)
    raise ValueError(msg)


def get_course_and_section(course_code, semester):
    dept_code, course_id, section_id = separate_course_code(course_code)

    course, created = Course.objects.get_or_create(department=dept_code,
                                                   code=course_id,
                                                   semester=semester)
    section, created = Section.objects.get_or_create(course=course, code=section_id)

    return course, section


def is_section_open(info):
    return info['course_status'] == 'O'


def upsert_course_from_opendata(info, semester):
    course_code = info['section_id_normalized']
    course, section = get_course_and_section(course_code, semester)

    # https://stackoverflow.com/questions/11159118/incorrect-string-value-xef-xbf-xbd-for-column
    course.title = info['course_title'].replace('\uFFFD', '')
    course.description = info['course_description'].replace('\uFFFD', '')
    course.save()

    section.status = info['course_status']
    section.capacity = int(info['max_enrollment'])
    section.activity = info['activity']
    section.meeting_times = json.dumps([meeting['meeting_days'] + ' '
                                        + meeting['start_time'] + ' - '
                                        + meeting['end_time'] for meeting in info['meetings']])
    for instructor in info['instructors']:
        i, created = Instructor.objects.get_or_create(name=instructor['name'])
        section.instructors.add(i)
    section.save()


class RegStatus(Enum):
    SUCCESS = auto()
    OPEN_REG_EXISTS = auto()
    COURSE_OPEN = auto()
    COURSE_NOT_FOUND = auto()
    NO_CONTACT_INFO = auto()


class Registration(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(blank=True, null=True, max_length=100)
    # section that the user registered to be notified about
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    # change to True once notification email has been sent out
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(blank=True, null=True)
    METHOD_CHOICES = (
        ('', 'Unsent'),
        ('LEG', '[Legacy] Sequence of course API requests'),
        ('WEB', 'Webhook'),
        ('SERV', 'Course Status Service'),
        ('ADM', 'Admin Interface'),
    )
    notification_sent_by = models.CharField(max_length=16, choices=METHOD_CHOICES, default='', blank=True)

    # track resubscriptions
    resubscribed_from = models.OneToOneField('Registration',
                                             blank=True,
                                             null=True,
                                             on_delete=models.SET_NULL,
                                             related_name='resubscribed_to')

    def __str__(self):
        return '%s: %s' % (self.email or self.phone, self.section.__str__())

    def validate_phone(self):
        """Store phone numbers in the format recommended by Twilio."""
        try:
            phone_number = phonenumbers.parse(self.phone, 'US')
            self.phone = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.phonenumberutil.NumberParseException:
            # if the phone number is unparseable, don't include it.
            self.phone = None

    def save(self, *args, **kwargs):
        self.validate_phone()
        super().save(*args, **kwargs)

    @property
    def resub_url(self):
        """Get the resubscribe URL associated with this registration"""
        full_url = '%s%s' % (settings.BASE_URL, urls.reverse('resubscribe', kwargs={'id_': self.id}))
        return Url.objects.get_or_create(full_url).shortened

    def alert(self, forced=False, sent_by=''):
        if forced or not self.notification_sent:
            text_result = Text(self).send_alert()
            email_result = Email(self).send_alert()
            logging.debug('NOTIFICATION SENT FOR ' + self.__str__())
            self.notification_sent = True
            self.notification_sent_at = timezone.now()
            self.notification_sent_by = sent_by
            self.save()
            return email_result is not None and text_result is not None  # True if no error in email/text.
        else:
            return False

    def resubscribe(self):
        """
        Resubscribe for notifications. If the registration this is called on
        has had its notification sent, a new registration is made. If it hasn't,
        return the most recent registration in the resubscription chain which hasn't
        been used yet.

        Resubscription is idempotent. No matter how many times you call it (without
        alert() being called on the registration), only one Registration model will
        be created.
        :return: Registration object for the resubscription
        """
        most_recent_reg = self
        while hasattr(most_recent_reg, 'resubscribed_to'):  # follow the chain of resubscriptions to the most recent one.
            most_recent_reg = most_recent_reg.resubscribed_to

        if not most_recent_reg.notification_sent:  # if a notification hasn't been sent on this recent one,
            return most_recent_reg  # don't create duplicate registrations for no reason.

        new_registration = Registration(email=self.email,
                                        phone=self.phone,
                                        section=self.section,
                                        resubscribed_from=most_recent_reg)
        new_registration.save()
        return new_registration


def register_for_course(course_code, email_address, phone):
    if not email_address and not phone:
        return RegStatus.NO_CONTACT_INFO
    course, section = get_course_and_section(course_code, get_current_semester())
    registration = Registration(section=section, email=email_address, phone=phone)
    registration.validate_phone()

    if Registration.objects.filter(section=section,
                                   email=email_address,
                                   phone=registration.phone,
                                   notification_sent=False).exists():
        return RegStatus.OPEN_REG_EXISTS

    registration.save()
    return RegStatus.SUCCESS


class CourseUpdate(models.Model):
    STATUS_CHOICES = (
        ('O', 'Open'),
        ('C', 'Closed'),
        ('X', 'Cancelled'),
        ('', 'Unlisted')
    )
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    old_status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    new_status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    alert_sent = models.BooleanField()
    request_body = models.TextField()

    def __str__(self):
        d = dict(self.STATUS_CHOICES)
        return f'{self.section.__str__()} - {d[self.old_status]} to {d[self.new_status]}'


def record_update(section_id, semester, old_status, new_status, alerted, req):
    try:
        _, section = get_course_and_section(section_id, semester)
    except ValueError:
        return None
    u = CourseUpdate(section=section,
                     old_status=old_status,
                     new_status=new_status,
                     alert_sent=alerted,
                     request_body=req)
    u.save()
    return u


def update_course_from_record(update):
    if update is not None:
        section = update.section
        section.status = update.new_status
        section.save()

