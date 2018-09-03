from django.db import models


class Course(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    department = models.CharField(max_length=8)
    course_code = models.CharField(max_length=8)
    semester = models.CharField(max_length=5)

    title = models.TextField()
    description = models.TextField()


class Section(models.Model):
    class Meta:
        unique_together = (('section_code', 'course'), )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    section_code = models.CharField(max_length=16)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    capacity = models.IntegerField()


class Email(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.EmailField()


class Registration(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    emails = models.ManyToManyField(Email)
    # section that the user registered to be notified about
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    # change to True once notification email has been sent out
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(blank=True, null=True)
    # change to True if the user resubscribes from the notification attached to this registration
    resubscribed = models.BooleanField(default=False)
    resubscribed_at = models.DateTimeField(blank=True, null=True)
