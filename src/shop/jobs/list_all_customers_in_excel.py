# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
from collections import defaultdict
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import xlwt
from babel.dates import format_datetime

from rogerthat.settings import get_server_settings
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import send_mail_via_mime
from shop.models import Customer

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def job():
    settings = get_server_settings()
    customers = list(Customer.all().fetch(10))
    customers_per_app = defaultdict(list)
    for customer in customers:
        customers_per_app[customer.default_app_id].append(customer)
    book = xlwt.Workbook(encoding='utf-8')
    for app_id in customers_per_app:
        if not app_id:
            continue
        sheet = book.add_sheet(app_id)
        row = 0
        sheet.write(row, 0, 'Customer name')
        for customer in customers_per_app[app_id]:
            row += 1
            url = '%s/internal/shop/login_as?customer_id=%d' % (settings.baseUrl, customer.id)
            sheet.write(row, 0, xlwt.Formula('HYPERLINK("%s";"%s")' % (url, customer.name.replace('"', ''))))

    excel = StringIO()
    book.save(excel)
    excel_string = excel.getvalue()

    current_date = format_datetime(datetime.datetime.now(), locale=DEFAULT_LANGUAGE)
    to_emails = [u'lucas@mobicage.com', u'tom@mobicage.com', u'gert@mobicage.com']
    msg = MIMEMultipart('mixed')
    msg['Subject'] = 'List of all customers'
    msg['From'] = 'export@mobicage.com'
    msg['To'] = ','.join(to_emails)
    msg["Reply-To"] = 'noreply@mobicage.com'
    body = MIMEText('See attachment.', 'plain', 'utf-8')
    msg.attach(body)

    att = MIMEApplication(excel_string, _subtype='vnd.ms-excel')
    att.add_header('Content-Disposition', 'attachment',
                   filename='Customers %s.xls' % current_date)
    msg.attach(att)

    send_mail_via_mime(settings.senderEmail, to_emails, msg)
