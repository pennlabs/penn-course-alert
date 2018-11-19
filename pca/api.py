import requests
import logging

from django.conf import settings
logger = logging.getLogger(__name__)


def get_headers(primary=True):
    """This will have a rotation of API keys eventually"""
    return {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization-Bearer': settings.API_KEY if primary else settings.API_KEY_SECONDARY,
        'Authorization-Token': settings.API_SECRET if primary else settings.API_SECRET_SECONDARY
    }


def make_api_request(params, headers):
    if headers is None:
        headers = get_headers()

    r = requests.get(settings.API_URL,
                     params=params,
                     headers=headers)

    if r.status_code == requests.codes.ok:
        return r.json(), None
    else:
        return None, r.text


def get_courses(query, semester):
    headers = get_headers()

    params = {
        'course_id': query,
        'term': semester,
        'page_number': 1,
        'number_of_results_per_page': 200
    }

    results = []
    while True:
        logger.info('making request for page #%d' % params['page_number'])
        data, err = make_api_request(params, headers)
        if data is not None:
            next_page = data['service_meta']['next_page_number']
            results.extend(data['result_data'])
            if int(next_page) <= params['page_number']:
                break
            params['page_number'] = next_page
        else:
            logger.error(err)  # log API error
            break

    return results


def first(lst):
    if len(lst) > 0:
        return lst[0]


def get_course(query, semester, primary=True):
    params = {
        'course_id': query,
        'term': semester
    }
    headers = get_headers(primary)
    data, err = make_api_request(params, headers)
    if err is None and data is not None:
        return first(data['result_data'])
    else:
        logger.error(err)
        return None
