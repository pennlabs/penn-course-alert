import requests

from django.conf import settings


def get_headers():
    """This will have a rotation of API keys eventually"""
    return {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization-Bearer': settings.API_KEY,
        'Authorization-Token': settings.API_SECRET
    }


def get_courses(query, semester):
    headers = get_headers()

    params = {
        'course_id': query,
        'term': semester,
        'page_number': 1,
        'number_of_results_per_page': 200
    }

    results = []

    print(headers)
    while True:
        r = requests.get(settings.API_URL,
                         params=params,
                         headers=headers)
        if r.status_code == requests.codes.ok:
            data = r.json()
            next_page = data['service_meta']['next_page_number']
            # print(data)
            results.extend(data['result_data'])
            if int(next_page) <= params['page_number']:
                break
            params['page_number'] = next_page
        else:
            print(r.text) # log API error
            break

    return results

