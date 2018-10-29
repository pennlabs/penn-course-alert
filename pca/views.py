from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404
from django.template import loader
from .models import *


def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render({}, request))


def register(request):
    if request.method == 'POST':
        course_code = request.POST.get('course', None)
        email_address = request.POST.get('email', None)
        carrier = request.POST.get('carrier', None)
        phone = request.POST.get('phone', None)

        course, section = get_course_and_section(course_code, get_current_semester())
        registration = Registration(section=section, email=email_address, phone=phone)
        registration.save()

        return JsonResponse({
            'course': course.__str__(),
            'section': section.__str__(),
            'registration': registration.__str__()
        })
    else:
        raise Http404('GET not accepted')
