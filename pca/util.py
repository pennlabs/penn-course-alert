import requests

from django.conf import settings


def shorten_url(url):
    r = requests.post('https://www.googleapis.com/urlshortener/v1/url',
                      params={'key': settings.URL_SHORTENER_KEY},
                      json={'longUrl': url})
    if r.status_code == requests.codes.ok:
        return r.json()['id']
