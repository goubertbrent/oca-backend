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

import json
import logging
import pprint

from mcfw.rpc import returns, arguments
from rogerthat.dal.app import get_app_by_id
from rogerthat.models import Report
from rogerthat.rpc import users
from rogerthat.rpc.rpc import expose
from rogerthat.settings import get_server_settings
from rogerthat.to.activity import LogCallRequestTO, LogCallResponseTO, LogLocationsResponseTO, LogLocationsRequestTO,\
    ReportObjectionableContentResponseTO, ReportObjectionableContentRequestTO
from rogerthat.utils import foreach, send_mail


@expose(('api',))
@returns(LogCallResponseTO)
@arguments(request=LogCallRequestTO)
def logCall(request):
    record = request.record
    response = LogCallResponseTO()
    response.recordId = record.id
    return response


@expose(('api',))
@returns(LogLocationsResponseTO)
@arguments(request=LogLocationsRequestTO)
def logLocations(request):
    records = request.records
    from rogerthat.bizz.location import get_location, post, CannotDetermineLocationException
    user = users.get_current_user()
    mobile = users.get_current_mobile()

    def logLocation(record):
        if not record.geoPoint and not record.rawLocation:
            logging.error("Received location record without location details!\nuser = %s\nmobile = %s"
                          % (user, mobile.id))
        else:
            try:
                geoPoint = record.geoPoint if record.geoPoint else get_location(record.rawLocation)
                post(user, geoPoint, record.timestamp, request.recipients)
            except CannotDetermineLocationException:
                pass

    foreach(logLocation, records)


@expose(('api',))
@returns(ReportObjectionableContentResponseTO)
@arguments(request=ReportObjectionableContentRequestTO)
def reportObjectionableContent(request):
    report = Report(reported_by=users.get_current_user(),
                    reason=request.reason,
                    type=request.type,
                    object=json.loads(request.object))
    report.put()

    object_str = pprint.pformat(report.object)
    app = get_app_by_id(users.get_current_app_id())
    send_mail(app.dashboard_email_address, get_server_settings().supportEmail,
              u'User reports objectionable content',
              u'User: %s\nType: %s\nReason:%s\nContent:\n%s'
              % (report.reported_by.email(), request.type, request.reason, object_str))
