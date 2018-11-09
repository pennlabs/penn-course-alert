import redis

from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.urls import reverse
from django.template import loader
from .models import *
from .tasks import generate_course_json
from options.models import get_bool


# Helper function to return the homepage with a banner message.
def homepage_with_msg(request, type_, msg):
    return render(request, 'index.html', {
        'notification': {
            'type': type_,
            'text': msg
        }
    })


def homepage_closed(request):
    return homepage_with_msg(request,
                             'danger',
                             "We're currently closed for signups. Come back after schedules have been released!")


def index(request):
    if not get_bool('REGISTRATION_OPEN', True):
        return homepage_closed(request)

    return render(request, 'index.html')


def register(request):
    if not get_bool('REGISTRATION_OPEN', True):
        return HttpResponseRedirect(reverse('index'))

    if request.method == 'POST':
        course_code = request.POST.get('course', None)
        email_address = request.POST.get('email', None)
        phone = request.POST.get('phone', None)

        course, section = get_course_and_section(course_code, get_current_semester())
        registration = Registration(section=section, email=email_address, phone=phone)
        registration.validate_phone()

        if Registration.objects.filter(section=section,
                                       email=email_address,
                                       phone=registration.phone,
                                       notification_sent=False).exists():
            return homepage_with_msg(request,
                                     'warning',
                                     "You've already registered to get alerts for %s!" % section.normalized)

        registration.save()
        return homepage_with_msg(request,
                                 'success',
                                 'Your registration for %s was successful!' % section.normalized)
    else:
        raise Http404('GET not accepted')


def resubscribe(request, id_):
    if not Registration.objects.filter(id=id_).exists():
        raise Http404('No registration found')
    else:
        old_reg = Registration.objects.get(id=id_)
        new_reg = old_reg.resubscribe()
        return homepage_with_msg(request,
                                 'info',
                                 'You have been resubscribed for alerts to %s!' % new_reg.section.normalized)


def get_sections(request):
    sections = generate_course_json()
    return JsonResponse(sections, safe=False)
