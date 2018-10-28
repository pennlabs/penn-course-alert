import json

from django.db import models


def get_current_semester():
    return '2018C'


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

    capacity = models.IntegerField(default=0)
    activity = models.CharField(max_length=50, null=True, blank=True)
    meeting_times = models.TextField(blank=True)
    instructors = models.ManyToManyField(Instructor)

    def __str__(self):
        return '%s-%s %s' % (self.course.course_id, self.code, self.course.semester)


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

    course.title = info['course_title']
    course.description = info['course_description']
    course.save()

    section.is_open = info['course_status'] == 'O'
    section.capacity = int(info['max_enrollment'])
    section.activity = info['activity']
    section.meeting_times = json.dumps([meeting['meeting_days'] + ' '
                                        + meeting['start_time'] + ' - '
                                        + meeting['end_time'] for meeting in info['meetings']])
    for instructor in info['instructors']:
        i, created = Instructor.objects.get_or_create(name=instructor['name'])
        section.instructors.add(i)
    section.save()


class Email(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.EmailField()

    def __str__(self):
        return self.address


class Registration(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    emails = models.ManyToManyField(Email)
    phone = models.CharField(blank=True, max_length=100)
    # section that the user registered to be notified about
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    # change to True once notification email has been sent out
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(blank=True, null=True)
    # change to True if the user resubscribes from the notification associated with this registration
    resubscribed = models.BooleanField(default=False)
    resubscribed_at = models.DateTimeField(blank=True, null=True)
