from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.template import loader
from .models import *


def index(request):
    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        course_code = request.POST.get('course', None)
        email_address = request.POST.get('email', None)
        carrier = request.POST.get('carrier', None)
        phone = request.POST.get('phone', None)

        course, section = get_course_and_section(course_code, get_current_semester())
        registration = Registration(section=section, email=email_address, phone=phone)
        registration.validate_phone()

        if Registration.objects.filter(section=section, email=email_address, phone=registration.phone, notification_sent=False).exists():
            return render(request, 'index.html', {
                'notification': {
                    'type': 'warning',
                    'text': "You've already registered to get alerts for %s!" % section.normalized
                }
            })

        registration.save()
        return homepage(request,
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
        return homepage(request,
                        'info',
                        'You have been resubscribed for alerts to %s!' % new_reg.section.normalized)


def homepage(request, type_, msg):
    return render(request, 'index.html', {
        'notification': {
            'type': type_,
            'text': msg
        }
    })
