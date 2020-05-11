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
import json

import webapp2

from mcfw.exceptions import HttpBadRequestException, HttpNotFoundException, HttpException
from mcfw.restapi import validate_request_authentication
from mcfw.rpc import serialize_complex_value, ErrorResponse
from rogerthat.bizz.app_assets import process_uploaded_assets
from rogerthat.bizz.authentication import Scopes
from rogerthat.bizz.default_brandings import save_default_branding
from rogerthat.exceptions.app_assets import AppAssetNotFoundException
from rogerthat.rpc.service import BusinessException
from rogerthat.to.app import AppAssetFullTO, DefaultBrandingTO


class UploadAppAssetHandler(webapp2.RequestHandler):
    def post(self, app_id, asset_type):
        validate_request_authentication(self, Scopes.APP_EDITOR, {'app_id': app_id})
        scale_x = float(self.request.get('scale_x'))
        file_data = self.request.POST.get('file')
        self.response.headers['Content-Type'] = 'application/json'
        try:
            asset = process_uploaded_assets(unicode(asset_type), file_data, False, [unicode(app_id)], scale_x)
            response_data = serialize_complex_value(AppAssetFullTO.from_model(asset), AppAssetFullTO, False)
        except BusinessException as exception:
            err = ErrorResponse(HttpBadRequestException(exception.message))
            response_data = serialize_complex_value(err, ErrorResponse, False)
            self.response.status = err.status_code
        self.response.write(json.dumps(response_data))


class UploadDefaultBrandingHandler(webapp2.RequestHandler):
    def post(self, app_id, branding_type):
        validate_request_authentication(self, Scopes.APP_EDITOR, {'app_id': app_id})
        file_data = self.request.POST.get('file')
        self.response.headers['Content-Type'] = 'application/json'
        if file_data is None:
            err = ErrorResponse(HttpBadRequestException('missing_file'))
            response_data = serialize_complex_value(err, ErrorResponse, False)
            self.response.status = httplib.BAD_REQUEST
        else:
            try:
                branding = save_default_branding(unicode(branding_type), file_data, False, [unicode(app_id)])
                response_data = serialize_complex_value(DefaultBrandingTO.from_model(branding), DefaultBrandingTO,
                                                        False)
            except BusinessException as exception:
                err = ErrorResponse(HttpBadRequestException(exception.message))
                response_data = serialize_complex_value(err, ErrorResponse, False)
                self.response.status = err.status_code
            except HttpException as e:
                response_data = serialize_complex_value(ErrorResponse(e), ErrorResponse, False)
                self.response.status = e.http_code

        self.response.write(json.dumps(response_data))


class UploadGlobalAppAssetHandler(webapp2.RequestHandler):
    def handle(self, asset_id):
        validate_request_authentication(self, Scopes.BACKEND_EDITOR, {})
        scale_x = float(self.request.get('scale_x'))
        app_ids = [a for a in self.request.get('app_ids', '').split(',') if a]
        default = self.request.get('is_default') == 'true'
        asset_type = unicode(self.request.get('asset_type'))
        file_data = self.request.POST.get('file')
        try:
            asset = process_uploaded_assets(asset_type, file_data, default, app_ids, scale_x, asset_id)
            response_data = serialize_complex_value(AppAssetFullTO.from_model(asset), AppAssetFullTO, False)
        except AppAssetNotFoundException as exception:
            err = ErrorResponse(HttpNotFoundException(exception.message))
            response_data = serialize_complex_value(err, ErrorResponse, False)
            self.response.status = err.status_code
        except BusinessException as exception:
            err = ErrorResponse(HttpBadRequestException(exception.message))
            response_data = serialize_complex_value(err, ErrorResponse, False)
            self.response.status = err.status_code
        self.response.write(json.dumps(response_data))

    def post(self):
        self.handle(None)

    def put(self, asset_id):
        self.handle(asset_id)


class UploadGlobalBrandingHandler(webapp2.RequestHandler):
    def handle(self, branding_id):
        validate_request_authentication(self, Scopes.BACKEND_EDITOR, {})
        default = self.request.get('is_default') == 'true'
        app_ids = [a for a in self.request.get('app_ids', '').split(',') if a]
        file_data = self.request.POST.get('file')
        branding_type = self.request.POST.get('branding_type')
        try:
            branding = save_default_branding(branding_type, file_data, default, app_ids, branding_id)
            response_data = serialize_complex_value(DefaultBrandingTO.from_model(branding), DefaultBrandingTO, False)
        except AppAssetNotFoundException as exception:
            err = ErrorResponse(HttpNotFoundException(exception.message))
            response_data = serialize_complex_value(err, ErrorResponse, False)
            self.response.status = err.status_code
        except BusinessException as exception:
            err = ErrorResponse(HttpBadRequestException(exception.message))
            response_data = serialize_complex_value(err, ErrorResponse, False)
            self.response.status = err.status_code
        self.response.write(json.dumps(response_data))

    def post(self):
        self.handle(None)

    def put(self, branding_id):
        self.handle(unicode(branding_id))
