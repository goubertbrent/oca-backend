# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley Belgium NV
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
# @@license_version:1.7@@

import httplib
import inspect
import json
import logging
import threading
from collections import defaultdict
from types import NoneType
from urllib import unquote

import webapp2

from mcfw.consts import AUTHENTICATED, NOT_AUTHENTICATED, REST_TYPE_NORMAL, REST_TYPE_TO
from mcfw.exceptions import HttpException, HttpBadRequestException, HttpInternalServerErrorException, \
    HttpForbiddenException
from mcfw.rpc import run, parse_parameters, serialize_complex_value, ErrorResponse, parse_complex_value, \
    MissingArgumentException
from rogerthat.consts import DEBUG

_rest_handlers = defaultdict(dict)
_precall_hooks = []
_postcall_hooks = []


class InjectedFunctions(object):

    def __init__(self):
        self._get_session_function = None

    @property
    def get_current_session(self):
        return self._get_session_function

    @get_current_session.setter
    def get_current_session(self, function):
        self._get_session_function = function


INJECTED_FUNCTIONS = InjectedFunctions()
del InjectedFunctions


def register_precall_hook(callable_):
    _precall_hooks.append(callable_)


def register_postcall_hook(callable_):
    _postcall_hooks.append(callable_)


def rest(uri, method, authenticated=True, silent=False, silent_result=False, read_only_access=False, type=None):
    if method not in ('get', 'post', 'put', 'delete'):
        ValueError('method')
    if type not in (REST_TYPE_NORMAL, REST_TYPE_TO,):
        type = REST_TYPE_NORMAL

    if DEBUG:
        if uri.startswith(' ') or uri.endswith(' '):
            raise ValueError('Remove the trailing or leading spaces from api call %s %s' % (method, uri))

    def wrap(f):
        if not inspect.isfunction(f):
            raise ValueError("f is not of type function!")

        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)

        wrapped.__name__ = f.__name__
        wrapped.meta = {"rest": True, "uri": uri, "method": method, "authenticated": authenticated, "silent": silent,
                        "silent_result": silent_result, "read_only_access": read_only_access, 'flavor': type}
        if hasattr(f, "meta"):
            wrapped.meta.update(f.meta)
        return wrapped

    return wrap


class ResponseTracker(threading.local):

    def __init__(self):
        self.current_response = None
        self.current_request = None


_current_reponse_tracker = ResponseTracker()
del ResponseTracker


class GenericRESTRequestHandler(webapp2.RequestHandler):

    @staticmethod
    def getCurrentResponse():
        return _current_reponse_tracker.current_response

    @staticmethod
    def getCurrentRequest():
        # type: () -> webapp2.Request
        return _current_reponse_tracker.current_request

    @staticmethod
    def clearCurrent():
        _current_reponse_tracker.current_response = None

    @staticmethod
    def setCurrent(request, response):
        _current_reponse_tracker.current_request = request
        _current_reponse_tracker.current_response = response

    def ctype(self, type_, value):
        if not isinstance(type_, (list, tuple)):
            if type_ == bool:
                return bool(value) and value.lower() == 'true'
            return type_(value)
        elif isinstance(type_, list):
            return [self.ctype(type_[0], item) for item in value]
        elif type_ == (str, unicode):
            return unicode(value)
        elif type_ == (int, long):
            return long(value)
        elif type_ == (int, long, NoneType):
            return None if value is None or value == '' else long(value)
        raise NotImplementedError()

    def get_handler(self, method, route):
        """
        Returns the handler associated with the requested URL
         Returns None if no handler was found for this url or when the method is not implemented/allowed
        Args:
            method (string)
            route (webapp2.Route)
        Returns:
            function(callable)
        """
        if route.template in _rest_handlers:
            if method in _rest_handlers[route.template]:
                return _rest_handlers[route.template][method]
            else:
                self.response.set_status(httplib.METHOD_NOT_ALLOWED, httplib.responses[httplib.METHOD_NOT_ALLOWED])
        logging.debug('No rest handlers found for route %s', route.template)
        self.response.set_status(httplib.NOT_FOUND, httplib.responses[httplib.NOT_FOUND])

    def update_kwargs(self, func, kwargs):
        for name, type_ in func.meta['kwarg_types'].iteritems():
            if name in self.request.GET:
                if isinstance(type_, list):
                    # Support both &param=1&param=2 and &param=1,2
                    items = self.request.GET.getall(name)
                    if len(items) == 1 and ',' in items[0]:
                        items = items[0].split(',')
                    kwargs[name] = self.ctype(type_, [unquote(p) for p in items])
                else:
                    kwargs[name] = self.ctype(type_, unquote(self.request.GET.get(name)))
            elif name in kwargs:
                kwargs[name] = self.ctype(type_, kwargs[name])

    def write_result(self, result):
        self.response.headers.update({
            'Content-Type': 'application/json'
        })
        if result is not None:
            if isinstance(result, ErrorResponse):
                self.response.set_status(result.status_code)
                result = serialize_complex_value(result, ErrorResponse, False)
            if DEBUG:
                self.response.out.write(json.dumps(result, indent=2, sort_keys=True))
            else:
                self.response.out.write(json.dumps(result))
        else:
            self.response.set_status(httplib.NO_CONTENT)

    def get(self, *args, **kwargs):
        GenericRESTRequestHandler.setCurrent(self.request, self.response)
        f = self.get_handler('get', self.request.route)
        if not f:
            return
        self.update_kwargs(f, kwargs)
        self.write_result(self.run(f, args, kwargs))

    def post(self, *args, **kwargs):
        """
        2 possibilities for parameters here:
        - Every property of the json data is an argument
        - A 'data' argument is specified. This should have the correct type in @arguments
        Args:
            *args (tuple): positional arguments. These are unnamed variables in routes.
            **kwargs (dict): keyword arguments. These are named variables in routes.
        """
        GenericRESTRequestHandler.setCurrent(self.request, self.response)
        f = self.get_handler('post', self.request.route)
        if not f:
            return
        self.update_kwargs(f, kwargs)
        if self.request.headers.get('Content-Type', '').startswith('application/json'):
            if f.meta['flavor'] == REST_TYPE_TO:
                parameters = {'data': json.loads(self.request.body) if self.request.body else {}}
            else:
                parameters = json.loads(self.request.body) if self.request.body else {}
        else:
            parameters = json.loads(self.request.POST['data']) if 'data' in self.request.POST else {}
        # Backwards compatibility
        params = parse_parameters(f, parameters)
        params.update(kwargs)
        self.write_result(self.run(f, args, params))

    def put(self, *args, **kwargs):
        GenericRESTRequestHandler.setCurrent(self.request, self.response)
        f = self.get_handler('put', self.request.route)
        if not f:
            return
        self.update_kwargs(f, kwargs)
        post_data_type = f.meta['kwarg_types'].get('data')
        if post_data_type:
            is_list = type(post_data_type) is list
            if is_list:
                post_data_type = post_data_type[0]
            post_data = json.loads(self.request.body) if self.request.body else {}
            kwargs['data'] = parse_complex_value(post_data_type, post_data, is_list)
        self.write_result(self.run(f, args, kwargs))

    def delete(self, *args, **kwargs):
        GenericRESTRequestHandler.setCurrent(self.request, self.response)
        f = self.get_handler('delete', self.request.route)
        if not f:
            return
        self.update_kwargs(f, kwargs)
        self.write_result(self.run(f, args, kwargs))

    def run(self, f, args, kwargs):
        """
        Args:
            f (any)
            args (tuple)
            kwargs (dict)
        Returns: callable
        """
        if f.meta['authorized_function']:
            if not f.meta['authorized_function']():
                self.abort(httplib.UNAUTHORIZED)
                return
        if f.meta['authenticated']:
            session = INJECTED_FUNCTIONS.get_current_session()
            if session and session.read_only and not f.meta["read_only_access"]:
                self.abort(httplib.UNAUTHORIZED)
                return
            service_email = self.request.headers.get('X-Logged-In-As')
            if service_email and session:
                if session.service_identity_user:
                    current_user_email = session.service_identity_user.email()
                else:
                    current_user_email = session.user.email()
                if '/' in current_user_email:
                    current_user_email = current_user_email.split('/')[0]
                if service_email != current_user_email:
                    logging.warning('X-Logged-In-As: %s != %s', service_email, current_user_email)
                    return ErrorResponse(HttpForbiddenException('You are logged in as another user'))
        for hook in _precall_hooks:
            hook(f, *args, **kwargs)
        try:
            result = run(f, args, kwargs)
        except HttpException as http_exception:
            return ErrorResponse(http_exception)
        except MissingArgumentException as e:
            logging.debug(e)
            return ErrorResponse(HttpBadRequestException(e.message))
        except Exception as e:
            for hook in _postcall_hooks:
                hook(f, False, kwargs, e)
            logging.exception(e)
            return ErrorResponse(HttpInternalServerErrorException())
        for hook in _postcall_hooks:
            hook(f, True, kwargs, result)
        return result


def rest_functions(module, authentication=AUTHENTICATED, authorized_function=None):
    if authentication not in (AUTHENTICATED, NOT_AUTHENTICATED):
        raise ValueError(authentication)
    for f in (function for (name, function) in inspect.getmembers(module, lambda x: inspect.isfunction(x))):
        if hasattr(f, 'meta') and f.meta.get('rest', False):
            meta_uri = f.meta['uri']
            meta_method = f.meta['method']
            f.meta['authentication'] = authentication
            f.meta["authorized_function"] = authorized_function
            for uri in (meta_uri if isinstance(meta_uri, (list, tuple)) else (meta_uri,)):
                _rest_handlers[uri][meta_method] = f
                yield webapp2.Route(uri, GenericRESTRequestHandler)
