import json
from urllib.parse import urlencode

from django.db import models
from django.conf import settings
from django.utils import timezone
from django import urls

from .alerts import Email, Text
from shortener.models import shorten
from options.models import get_value

import phonenumbers  # library for parsing and formatting phone numbers.


def get_current_semester():
    return get_value('SEMESTER', '2019C')


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
    class Meta:
        unique_together = (('code', 'course'), )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    code = models.CharField(max_length=16)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    is_open = models.BooleanField(default=False)
    is_open_updated_at = models.DateTimeField(blank=True, null=True)

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


def separate_course_code(course_code):
    return list(map(lambda s: s.strip().upper(), course_code.split('-')))


def get_course_and_section(course_code, semester):
    pieces = separate_course_code(course_code)
    dept_code = pieces[0]
    course_code = pieces[1]
    section_id = pieces[2]
    course, created = Course.objects.get_or_create(department=dept_code,
                                                   code=course_code,
                                                   semester=semester)
    section, created = Section.objects.get_or_create(course=course, code=section_id)

    return course, section


def upsert_course_from_opendata(info, semester):
    course_code = info['section_id_normalized']
    course, section = get_course_and_section(course_code, semester)

    course.title = info['course_title'].replace('\uFFFD', '')
    course.description = info['course_description'].replace('\uFFFD', '')
    course.save()

    section.is_open = info['course_status'] == 'O'
    section.is_open_updated_at = timezone.now()
    section.capacity = int(info['max_enrollment'])
    section.activity = info['activity']
    section.meeting_times = json.dumps([meeting['meeting_days'] + ' '
                                        + meeting['start_time'] + ' - '
                                        + meeting['end_time'] for meeting in info['meetings']])
    for instructor in info['instructors']:
        i, created = Instructor.objects.get_or_create(name=instructor['name'])
        section.instructors.add(i)
    section.save()


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

    # track resubscriptions
    resubscribed_from = models.OneToOneField('Registration',
                                             null=True,
                                             on_delete=models.SET_NULL,
                                             related_name='resubscribed_to')

    def __str__(self):
        return '%s: %s' % (self.email, self.section.__str__())

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
        return shorten(full_url).shortened

    def alert(self):
        # TODO: Exception handling on send_alert()
        email_result = Email(self).send_alert()
        text_result = Text(self).send_alert()
        self.notification_sent = True
        self.notification_sent_at = timezone.now()
        self.save()
        return email_result is not None and text_result is not None  # True if no error in email/text.

    def resubscribe(self):
        r = self
        while hasattr(r, 'resubscribed_to'):  # follow the chain of resubscriptions to the most recent one.
            r = r.resubscribed_to
        if not r.notification_sent:  # if a notification hasn't been sent on this recent one,
            return self  # don't create duplicate registrations for no reason.

        new_registration = Registration(email=self.email,
                                        phone=self.phone,
                                        section=self.section,
                                        resubscribed_from=self)
        new_registration.save()
        return new_registration
