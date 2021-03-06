# -*- coding: utf-8 -*-
#
# This file is part of the jabber.at homepage (https://github.com/jabber-at/hp).
#
# This project is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with this project. If not, see
# <http://www.gnu.org/licenses/>.

import json
import logging
from urllib.parse import urlsplit

from ua_parser import user_agent_parser

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.db import transaction
from django.http import HttpResponseRedirect
from django.http.request import split_domain_port
from django.http.request import validate_host
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _

from xmpp_backends.base import BackendError

from .exceptions import HttpResponseException
from .models import CachedMessage
from .models import MenuItem

log = logging.getLogger(__name__)

_KNOWN_OS = ['osx', 'ios', 'android', 'linux', 'windows', 'any', 'browser', 'console']


class HomepageMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        self.default_site = settings.XMPP_HOSTS[settings.DEFAULT_XMPP_HOST]

    def get_os(self, request):
        if 'os' in request.GET:
            os = request.GET['os']

            # Only allow known OS, otherwise this might open us to XSS attacks
            if os in _KNOWN_OS:
                return os

        ua_parsed = user_agent_parser.ParseOS(request.META.get('HTTP_USER_AGENT', ''))
        os = ua_parsed['family'].lower().strip()
        if os == 'mac os x':
            return 'osx'
        elif os == 'ios':
            return 'ios'
        elif os == 'android':
            return 'android'
        elif os == 'linux':
            return 'linux'
        elif os.startswith('windows'):
            return 'win'

        return 'any'

    def __call__(self, request):
        host = request._get_raw_host()
        domain, port = split_domain_port(host)

        # Set request.site
        request.site = self.default_site
        for name, config in settings.XMPP_HOSTS.items():
            if validate_host(domain, config.get('ALLOWED_HOSTS', [])):
                request.site = config

        # Attach any messages from the database to the messages system
        # These messages usually come from asynchronous tasks (-> Celery)
        if request.user.is_anonymous is False:
            with transaction.atomic():
                stored_msgs = CachedMessage.objects.filter(user=request.user)
                for msg in stored_msgs:
                    messages.add_message(request, msg.level, _(msg.message) % json.loads(msg.payload))

                stored_msgs.delete()

        # Attach OS information to request
        request.os = self.get_os(request)
        request.os_mobile = request.os in ['android', 'ios', 'any']

        # Get data that is used with every request and requires database access and cache it
        cache_key = 'request_context'
        cached = cache.get(cache_key)
        if cached is None:
            cached = {
                'menuitems': MenuItem.objects.all(),
            }
            for item in cached['menuitems']:
                item.cached_data  # touch cached_data to make sure that all properties serialized

            cache.set(cache_key, cached)
        request.hp_request_context = cached

        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Handle translated paths."""

        match = request.resolver_match
        if getattr(match.func, 'translated_match', False):
            url_name = match.url_name  # "name" parameter in the URL config
            if match.namespace:
                url_name = '%s:%s' % (match.namespace, url_name)

            return HttpResponseRedirect(reverse(url_name))

    def process_exception(self, request, exception):
        """Process homepage-specific exceptions."""

        if isinstance(exception, HttpResponseException):
            log.exception(exception)
            return exception.get_response(request)
        if isinstance(exception, BackendError):
            log.exception(exception)
            return TemplateResponse(request, template='core/errors/xmpp_backend.html', status=503)


def security_headers_middleware(get_response):
    """Middleware to add security headers in development that normally would be set by the webserver."""

    def middleware(request):
        response = get_response(request)

        # Do nothing if DEBUG = False or if status_code != 200 (for Django tracebacks)
        if settings.DEBUG is False or response.status_code != 200:
            return response

        csp = 'default-src \'self\';'

        # If we have conversejs configured, we add the bosh service url as connect-src.
        if request.resolver_match.app_name == 'conversejs':
            csp += " img-src data: 'self';"
            bosh_url = settings.CONVERSEJS_CONFIG.get('bosh_service_url', '')
            if bosh_url:
                bosh_url = urlsplit(bosh_url)._replace(path='').geturl()
                csp += " connect-src 'self' %s;" % bosh_url

        response['Content-Security-Policy'] = csp
        response['Referrer-Policy'] = 'strict-origin'
        response['X-Frame-Options'] = 'deny'
        response['X-XSS-Protection'] = '1; mode=block'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    return middleware
