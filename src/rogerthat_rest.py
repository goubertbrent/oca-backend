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

from mcfw.restapi import rest_functions
from rogerthat.pages.mfd import SaveWiringHandler, LoadWiringHandler, DeleteWiringHandler, DownloadAsXMLHandler
from rogerthat.restapi import friends, mobile, profile, messaging, service_panel, location, registration, \
    services, web, roles, system
from rogerthat.wsgi import AuthenticatedRogerthatWSGIApplication

handlers = list()
handlers.extend(rest_functions(friends))
handlers.extend(rest_functions(mobile))
handlers.extend(rest_functions(system))
handlers.extend(rest_functions(web))
handlers.extend(rest_functions(profile))
handlers.extend(rest_functions(messaging))
handlers.extend(rest_functions(service_panel))
handlers.extend(rest_functions(services))
handlers.extend(rest_functions(location))
handlers.extend(rest_functions(registration))
handlers.extend(rest_functions(roles))

handlers.append(('/mobi/rest/services/mfd/save', SaveWiringHandler))
handlers.append(('/mobi/rest/services/mfd/load', LoadWiringHandler))
handlers.append(('/mobi/rest/services/mfd/delete', DeleteWiringHandler))
handlers.append(('/mobi/rest/services/mfd/download', DownloadAsXMLHandler))

app = AuthenticatedRogerthatWSGIApplication(handlers, redirect_login_required=False, name="main_rest")
