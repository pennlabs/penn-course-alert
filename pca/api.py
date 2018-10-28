import requests

from django.conf import settings


def get_headers():
    """This will have a rotation of API keys eventually"""
    return {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization-Bearer': settings.API_KEY,
        'Authorization-Token': settings.API_SECRET
    }


def make_api_request(params, headers=None):
    if headers is None:
        headers = get_headers()

    r = requests.get(settings.API_URL,
                     params=params,
                     headers=headers)

    if r.status_code == requests.codes.ok:
        return r.json(), None
    else:
        return None, r.text()


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
        data, err = make_api_request(params, headers)
        if data is not None:
            next_page = data['service_meta']['next_page_number']
            results.extend(data['result_data'])
            if int(next_page) <= params['page_number']:
                break
            params['page_number'] = next_page
        else:
            print(err)  # log API error
            break

    return results


def first(lst):
    if len(lst) > 0:
        return lst[0]


def get_course(query, semester):
    params = {
        'course_id': query,
        'term': semester
    }
    data, err = make_api_request(params)
    if data is not None:
        return first(data['result_data'])
    else:
        print(err)
