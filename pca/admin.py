from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import *

# !!!IMPORTANT NOTE!!!: search_fields contains fields on related objects. This means search queries WILL PERFORM JOINS.
# If this gets too slow, REMOVE THE RELATED FIELDS FROM `search_fields`.


class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ('section_link', 'resubscribed_from', 'created_at')
    search_fields = ('email', 'phone', 'section__course__department', 'section__course__code', 'section__code')
    autocomplete_fields = ('section', )

    def section_link(self, instance):
        link = reverse('admin:pca_section_change', args=[instance.section.id])
        return format_html('<a href="{}">{}</a>', link, instance.section.__str__())


class CourseAdmin(admin.ModelAdmin):
    search_fields = ('department', 'code', 'semester')


class SectionAdmin(admin.ModelAdmin):
    search_fields = ('course__department', 'course__code', 'code', 'course__semester')
    readonly_fields = ('course_link',)
    autocomplete_fields = ('instructors', 'course')

    def course_link(self, instance):
        link = reverse('admin:pca_course_change', args=[instance.course.id])
        return format_html('<a href="{}">{}</a>', link, instance.course.__str__())


class InstructorAdmin(admin.ModelAdmin):
    search_fields = ('name', )


admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Registration, RegistrationAdmin)
admin.site.register(CourseUpdate)
