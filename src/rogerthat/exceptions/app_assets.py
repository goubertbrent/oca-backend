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

from rogerthat.rpc.service import ServiceApiException


class AppAssetNotFoundException(ServiceApiException):
    def __init__(self, asset_id):
        code = ServiceApiException.BASE_CODE_APP + 100
        data = {
            'asset_id': asset_id
        }
        super(AppAssetNotFoundException, self).__init__(code, 'app_asset_not_found', data)


class CannotDeleteDefaultAppAssetException(ServiceApiException):
    def __init__(self):
        code = ServiceApiException.BASE_CODE_APP + 101
        super(CannotDeleteDefaultAppAssetException, self).__init__(code, 'cannot_delete_default_app_asset')
