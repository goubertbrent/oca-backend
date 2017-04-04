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
# @@license_version:1.2@@

from _collections import defaultdict
import datetime
from dateutil.relativedelta import relativedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib

from babel.dates import format_datetime
import xlwt

from rogerthat.consts import DAY
from rogerthat.models import ServiceProfile
from rogerthat.settings import get_server_settings
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import get_epoch_from_datetime, months_between, send_mail_via_mime, now
from google.appengine.ext import db
from mcfw.utils import chunks
from shop.models import Order
from solution_server_settings import get_solution_server_settings


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def job():
    today = datetime.date.today()
    epoch = get_epoch_from_datetime(today - relativedelta(months=9))

    qry = Order.all()
    qry.filter("is_subscription_order =", True)
    qry.filter("date <", epoch)
    qry.filter("status =", Order.STATUS_SIGNED)

    # assemble customers
    customer_keys = set()
    orders_by_order_number = dict()
    for order in qry:
        date = datetime.date.fromtimestamp(order.date)
        months_past_since_today = months_between(today, date)
        if months_past_since_today < 8:
            continue
        if (order.next_charge_date - now()) > (100 * DAY):
            continue
        customer_keys.add(order.customer_key)
        orders_by_order_number[order.order_number] = 12 - months_past_since_today

    # filter merchant customers
    apps = defaultdict(list)
    for customer_keys_chunk in chunks(list(customer_keys), 100):
        customers_chunk = db.get(customer_keys_chunk)
        for customer in customers_chunk:
            if customer.service_disabled_at != 0:
                continue
            if customer.organization_type != ServiceProfile.ORGANIZATION_TYPE_PROFIT:
                continue
            if customer.stripe_id and customer.stripe_credit_card_id:
                continue
            apps[customer.app_id].append(customer)

    settings = get_server_settings()

    # generate excel with information
    book = xlwt.Workbook(encoding="utf-8")
    for app_id, customers in apps.iteritems():
        sheet = book.add_sheet(app_id)
        row = 0
        sheet.write(row, 0, "Customer name")
        sheet.write(row, 1, "Months to renewal")
        for customer in customers:
            row += 1
            sheet.write(row, 0, xlwt.Formula('HYPERLINK("%s";"%s")' % ("%s/internal/shop/?%s" % (settings.baseUrl, urllib.urlencode(((('customer_id', customer.id),)))), customer.name)))
            sheet.write(row, 1, orders_by_order_number[customer.subscription_order_number])
    if apps:
        excel = StringIO()
        book.save(excel)
        excel_string = excel.getvalue()
        
        solution_server_settings = get_solution_server_settings()

        current_date = format_datetime(datetime.datetime.now(), locale=DEFAULT_LANGUAGE)
        
        to_emails = solution_server_settings.shop_customer_extention_emails
        msg = MIMEMultipart('mixed')
        msg['Subject'] = 'Customers in need of extention'
        msg['From'] = solution_server_settings.shop_export_email
        msg['To'] = ','.join(to_emails)
        msg["Reply-To"] = solution_server_settings.shop_no_reply_email
        body = MIMEText('See attachment to help the customers in need', 'plain', 'utf-8')
        msg.attach(body)

        att = MIMEApplication(excel_string, _subtype='vnd.ms-excel')
        att.add_header('Content-Disposition', 'attachment', filename='Prospects %s.xls' % (current_date))
        msg.attach(att)

        send_mail_via_mime(settings.senderEmail, to_emails, msg)
