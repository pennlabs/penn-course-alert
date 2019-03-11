import re

from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from django.urls import reverse

from .models import *
from .tasks import generate_course_json, send_course_alerts
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

        res = register_for_course(course_code, email_address, phone)

        if res == RegStatus.SUCCESS:
            return homepage_with_msg(request,
                                     'success',
                                     'Your registration for %s was successful!' % course_code)
        elif res == RegStatus.OPEN_REG_EXISTS:
            return homepage_with_msg(request,
                                     'warning',
                                     "You've already registered to get alerts for %s!" % course_code)
        elif res == RegStatus.NO_CONTACT_INFO:
            return homepage_with_msg(request,
                                     'danger',
                                     'Please enter either a phone number or an email address.')
        else:
            return homepage_with_msg(request,
                                     'warning',
                                     'There was an error on our end. Please try again!')
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


course_id_re = re.compile(r'([A-Z]{3,4})(\d{3})(\d{3})')


def normalize_course_id(c):
    m = course_id_re.match(c)
    if m:
        return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    else:
        return None


def alert_for_course(c_id):
    send_course_alerts.delay(c_id)


def accept_webhook(request):
    if request.method != 'POST':
        return HttpResponse('Methods other than POST are not allowed', status=405)

    if 'json' not in request.content_type.lower():
        return HttpResponse('Request expected in JSON', status=415)

    app_id = request.META.get('Authorization-Bearer', request.META.get('HTTP_AUTHORIZATION_BEARER'))
    app_secret = request.META.get('Authorization-Token', request.META.get('HTTP_AUTHORIZATION_TOKEN'))

    if app_id != settings.WEBHOOK_USERNAME or \
            app_secret != settings.WEBHOOK_PASSWORD:
        return HttpResponse('''Your credentials cannot be verified. 
        They should be placed in the header as &quot;Authorization-Bearer&quot;,  
        YOUR_APP_ID and &quot;Authorization-Token&quot; , YOUR_TOKEN"''', status=401)

    data = json.loads(request.body)
    course_id_normalized = normalize_course_id(data['result_data'][0]['course_section'])

    if get_bool('SEND_FROM_WEBHOOK', False):
        alert_for_course(course_id_normalized)
        return JsonResponse({'message': 'webhook recieved, alerts sent'})
    else:
        return JsonResponse({'message': 'webhook recieved'})
