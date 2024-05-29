# your_project/middleware.py

from django.conf import settings
from django.urls import set_urlconf
from django.http import HttpResponseNotFound

class SubdomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]  # Obtiene el host sin el puerto

        if host == 'geniuspro.pythonanywhere.com':
            settings.ROOT_URLCONF = 'academia.urls'
        elif host == 'geniuspro.pythonanywhere.com':
            settings.ROOT_URLCONF = 'administrativo.urls'
        else:
            return HttpResponseNotFound('Domain not found')

        response = self.get_response(request)
        return response
