# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

import datetime

import xlwt
from babel.dates import format_datetime

from rogerthat.models import BroadcastStatistic, ServiceIdentity
from rogerthat.rpc import users
from mcfw.rpc import arguments, returns
from solutions import translate, SOLUTION_COMMON
from solutions.common.dal import get_solution_settings
from solutions.common.utils import is_default_service_identity
from rogerthat.utils.service import create_service_identity_user

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


@returns(unicode)
@arguments(service_user=users.User, service_identity=unicode)
def get_broadcast_statistics_excel(service_user, service_identity):
    """
    Generates an excel file containing the broadcast statistics.

    Format: Date | Sent to | Received | Read | Acknowledged | Message

    Args:
        service_user(users.User): Service user

    Returns: Excel file

    """
    sln_settings = get_solution_settings(service_user)
    lang = sln_settings.main_language

    def transl(key):
        return translate(lang, SOLUTION_COMMON, key)

    if is_default_service_identity(service_identity):
        service_identity_user = create_service_identity_user(service_user, ServiceIdentity.DEFAULT)
    else:
        service_identity_user = create_service_identity_user(service_user, service_identity)
    bc_stats = BroadcastStatistic.get_all_by_service_identity_user(service_identity_user).order('timestamp')
    column_timestamp = 0
    column_sent = 1
    column_received = 2
    column_read = 3
    # column_acknowledged = 4
    column_message = 4
    bold_style = xlwt.XFStyle()
    bold_style.font.bold = True
    book = xlwt.Workbook(encoding="utf-8")

    messages_sheet = book.add_sheet(transl('broadcast_statistics')[0:31])
    messages_sheet.write(0, column_timestamp, transl('Date'), bold_style)
    messages_sheet.write(0, column_sent, transl('sent_to'), bold_style)
    messages_sheet.write(0, column_received, transl('received'), bold_style)
    messages_sheet.write(0, column_read, transl('Read'), bold_style)
    # messages_sheet.write(0, column_acknowledged, transl('acknowledged'), bold_style)
    messages_sheet.write(0, column_message, transl('message'), bold_style)
    messages_sheet.col(column_timestamp).width = 6000
    messages_sheet.col(column_sent).width = 5000
    messages_sheet.col(column_received).width = 5000
    messages_sheet.col(column_read).width = 5000
    # messages_sheet.col(column_acknowledged).width = 5000
    messages_sheet.col(column_message).width = 20000

    for i, statistic in enumerate(bc_stats):
        i += 1
        if statistic.timestamp:
            datetime_string = format_datetime(datetime.datetime.utcfromtimestamp(statistic.timestamp), locale=lang,
                                          tzinfo=sln_settings.tz_info)
        else:
            datetime_string = ''
        messages_sheet.write(i, column_timestamp, datetime_string)
        messages_sheet.write(i, column_message, statistic.message or '')
        messages_sheet.write(i, column_sent, statistic.sent or 0)
        messages_sheet.write(i, column_received, statistic.received or 0)
        messages_sheet.write(i, column_read, statistic.read or 0)
        # messages_sheet.write(i, column_acknowledged, statistic.acknowledged or 0)

    excel_file = StringIO()
    book.save(excel_file)
    return excel_file.getvalue()
