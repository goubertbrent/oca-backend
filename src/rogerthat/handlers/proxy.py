# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @@license_version:1.6@@

import httplib
import logging
import urllib

import webapp2
from google.appengine.api import urlfetch

from rogerthat.consts import DEBUG
from solution_server_settings import get_solution_server_settings


def _exec_request(path, method, headers, body, validate_certificate):
    # type: (str, str, dict, str, bool) -> urlfetch._URLFetchResult
    settings = get_solution_server_settings()
    headers['X-Bob-Api-Secret'] = settings.bob_api_secret.encode('utf-8')
    url = settings.appcfg_server_url + path
    return urlfetch.fetch(url, body, method, headers, deadline=30, validate_certificate=validate_certificate,
                          follow_redirects=False)


def _do_proxy(url, request, response, validate_certificate=True, write_result=True):
    """
    When issuing a request to another App Engine app, your App Engine app must assert its identity by adding the header
     X-Appengine-Inbound-Appid to the request. If you instruct the URL Fetch service to not follow redirects, App
     Engine will add this header to requests automatically.
    Args:
        url (unicode)
        request (webapp2.Request)
        response (webapp2.Response)
    """
    headers = request.headers
    content = None
    if 'Cookie' in headers:
        del headers['Cookie']
    if 'Host' in headers:
        del headers['Host']
    if 'Content-Length' in headers:
        del headers['Content-Length']
    logging.info('Proxying request to %s\nHeaders:%s\nData:%s', url, headers, request.body)
    try:
        query_params = urllib.urlencode(request.GET)
        if query_params:
            url = '%s?%s' % (url, query_params)
        result = _exec_request(url, request.method, headers, request.body, validate_certificate)
        status_code, content, headers = result.status_code, result.content, result.headers
    except urlfetch.DeadlineExceededError:
        # Took more than 30 seconds
        status_code = httplib.GATEWAY_TIMEOUT
    except urlfetch.DownloadError as error:
        # server down/unreachable
        logging.error(error)
        status_code = httplib.BAD_GATEWAY
    except urlfetch.Error as error:
        logging.error(error)
        status_code = httplib.INTERNAL_SERVER_ERROR
    status_str = str(status_code)
    if not content and (status_str.startswith('5') or status_str.startswith('4')):
        content = httplib.responses[status_code]
    if write_result:
        response.headers = headers
        response.set_status(status_code)
        response.out.write(content)
    if headers.get('Content-Type', '').lower() == 'application/json':
        logged_content = content
    else:
        logged_content = '[%s content omitted]' % headers.get('Content-Type', '') if content else None
    logging.info('Response: %s\nHeaders: %s\nContent: %s', status_code, headers, logged_content)
    return status_code, content, headers


class ProxyHandlerConfigurator(webapp2.RequestHandler):
    def _handle_request(self, kwargs, write_result=True):
        """
        Proxies requests incoming on /console-api/proxy to the app configurator server
        The url of this server must be set in the configuration
        Args:
            kwargs (dict): url parameters
        """
        from shop.view import authorize_manager
        if not authorize_manager():
            self.abort(403)
        path = urllib.quote(kwargs['route'])
        if DEBUG:
            # Pretty print in debug
            self.request.headers['Accept'] = 'application/json; indent=2'
        return _do_proxy(path, self.request, self.response, validate_certificate=True, write_result=write_result)

    def get(self, *args, **kwargs):
        self._handle_request(kwargs)

    def post(self, *args, **kwargs):
        self._handle_request(kwargs)

    def put(self, *args, **kwargs):
        self._handle_request(kwargs)

    def delete(self, *args, **kwargs):
        self._handle_request(kwargs)

    def patch(self, *args, **kwargs):
        self._handle_request(kwargs)

    def head(self, *args, **kwargs):
        self._handle_request(kwargs)
