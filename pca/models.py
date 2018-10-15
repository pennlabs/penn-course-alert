from django.db import models


def get_current_semester():
    return '2018C'


class Course(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    department = models.CharField(max_length=8)
    course_code = models.CharField(max_length=8)
    semester = models.CharField(max_length=5)

    title = models.TextField()
    description = models.TextField(blank=True)

    def __str__(self):
        return '%s %s' % (self.course_id, self.semester)

    @property
    def course_id(self):
        return '%s-%s' % (self.department, self.course_code)


class Section(models.Model):
    class Meta:
        unique_together = (('section_code', 'course'), )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    section_code = models.CharField(max_length=16)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    capacity = models.IntegerField(default=0)

    def __str__(self):
        return '%s-%s %s' % (self.course.course_id, self.section_code, self.course.semester)


class Email(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.EmailField()

    def __str__(self):
        return self.address


class Registration(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    emails = models.ManyToManyField(Email)
    # section that the user registered to be notified about
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    # change to True once notification email has been sent out
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(blank=True, null=True)
    # change to True if the user resubscribes from the notification associated with this registration
    resubscribed = models.BooleanField(default=False)
    resubscribed_at = models.DateTimeField(blank=True, null=True)


def separate_course_code(course_code):
    return list(map(lambda s: s.strip().upper(), course_code.split('-')))


def get_course_and_section(course_code, semester):
    pieces = separate_course_code(course_code)
    dept_code = pieces[0]
    course_code = pieces[1]
    section_id = pieces[2]
    course, created = Course.objects.get_or_create(department=dept_code,
                                                   course_code=course_code,
                                                   semester=semester)
    section, created = Section.objects.get_or_create(course=course, section_code=section_id)

    return course, section
