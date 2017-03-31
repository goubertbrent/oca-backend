# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import time

from babel.dates import format_datetime, get_timezone

from google.appengine.ext import webapp, deferred
from rogerthat.rpc import users
from rogerthat.service.api import system
from rogerthat.settings import get_server_settings
from rogerthat.utils import send_mail_via_mime
from shop.models import Customer
from solutions.common.bizz import SolutionModule
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionSettings
from solutions.common.models.city_vouchers import SolutionCityVoucherTransaction, \
    SolutionCityVoucher, SolutionCityVoucherExport, SolutionCityVoucherExportMerchant
import xlwt
from solution_server_settings import get_solution_server_settings


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
    

class SolutionCityVouchersExportHandler(webapp.RequestHandler):
        
    def get(self):
        create_voucher_export_pdfs()


def create_voucher_export_pdfs():

    def get_last_month():
        today = date.today()
        d = today - relativedelta(months=1)
        return date(d.year, d.month, 1)

    first_day_of_last_month = int(time.mktime(get_last_month().timetuple()))
    first_day_of_current_month = int(time.mktime(date.today().replace(day=1).timetuple()))
    
    for sln_settings in SolutionSettings.all().filter('modules =', SolutionModule.CITY_VOUCHERS):
        deferred.defer(create_voucher_statistics_for_city_service, sln_settings.service_user, first_day_of_last_month, first_day_of_current_month)


def create_voucher_statistics_for_city_service(service_user, first_day_of_last_month, first_day_of_current_month):
    customer = Customer.get_by_service_email(service_user.email())
    if not customer:
        logging.error("failed to create voucher statistics customer not found")
        return
    sln_settings = get_solution_settings(service_user)
    users.set_user(service_user)
    try:
        si = system.get_identity()
    finally:
        users.clear_user()
    app_id = si.app_ids[0]
    ancestor_key = SolutionCityVoucher.create_parent_key(app_id)
    
    qry = SolutionCityVoucherTransaction.all().ancestor(ancestor_key)
    qry.filter("action =", SolutionCityVoucherTransaction.ACTION_REDEEMED)
    qry.filter("created >=", first_day_of_last_month)
    qry.filter("created <", first_day_of_current_month)
    
    transactions = []
    merchant_transactions = dict()
    merchants = dict()
    unique_vouchers = dict()
    for t in qry:
        t.dt = format_datetime(t.created, 'EEE d MMM yyyy HH:mm',
                                         tzinfo=get_timezone(sln_settings.timezone), locale=customer.language)
        t.voucher = t.parent()
        transactions.append(t)
        if t.service_user not in merchant_transactions:
            merchant_transactions[t.service_user] = {"value": 0, "transactions": []}
        merchant_transactions[t.service_user]["value"] += t.value
        merchant_transactions[t.service_user]["transactions"].append(t.key())
        unique_vouchers[t.voucher.key()] = t.voucher
        
    for merchant_service_user in merchant_transactions.keys():
        merchants[merchant_service_user] = get_solution_settings(merchant_service_user)
        
    qry = SolutionCityVoucher.all().ancestor(ancestor_key)
    qry.filter("activated =", True)
    qry.filter("redeemed = ", False)
    vouchers = []
    for v in qry:
        v.dt = format_datetime(v.created, 'EEE d MMM yyyy HH:mm',
                                         tzinfo=get_timezone(sln_settings.timezone), locale=customer.language)
        vouchers.append(v)
    
    book = xlwt.Workbook(encoding="utf-8")
    
    # TAB 1
    sheet_transactions = book.add_sheet("Transacties")
    row = 0
    sheet_transactions.write(row, 0, "Tijdstip")
    sheet_transactions.write(row, 1, "Waardebon")
    sheet_transactions.write(row, 2, "Interne rekening")
    sheet_transactions.write(row, 3, "Kostenplaats")
    sheet_transactions.write(row, 4, "Handelaar")
    sheet_transactions.write(row, 5, "Opgenomen waarde")
    for transaction in transactions:
        row += 1
        sheet_transactions.write(row, 0, transaction.dt)
        sheet_transactions.write(row, 1, transaction.voucher.uid)
        sheet_transactions.write(row, 2, transaction.voucher.internal_account)
        sheet_transactions.write(row, 3, transaction.voucher.cost_center)
        sheet_transactions.write(row, 4, merchants[transaction.service_user].name)
        sheet_transactions.write(row, 5, round(transaction.value / 100.0, 2))
    row += 2
    sheet_transactions.write(row, 0, "Totaal")
    sheet_transactions.write(row, 5, xlwt.Formula('SUM(F2:F%s)' % (row -1)))
    
    # TAB 2
    sheet_merchants = book.add_sheet("Handelaars")
    row = 0
    sheet_merchants.write(row, 0, "Handelaar")
    sheet_merchants.write(row, 1, "Adres")
    sheet_merchants.write(row, 2, "IBAN")
    sheet_merchants.write(row, 3, "BIC")
    sheet_merchants.write(row, 4, "Totaal uit te betalen waarde")
    for merchant_service_user in merchants.keys():
        merchant = merchants[merchant_service_user]
        row += 1
        sheet_merchants.write(row, 0, merchant.name)
        sheet_merchants.write(row, 1, merchant.address)
        sheet_merchants.write(row, 2, merchant.iban or u"")
        sheet_merchants.write(row, 3, merchant.bic or u"")
        sheet_merchants.write(row, 4, round(merchant_transactions[merchant_service_user]["value"] / 100.0, 2))
        
    row += 2
    sheet_merchants.write(row, 0, "Totaal")
    sheet_merchants.write(row, 4, xlwt.Formula('SUM(E2:E%s)' % (row -1)))
    
    # TAB 3
    sheet_vouchers = book.add_sheet("Bonnen in omloop")
    row = 0
    sheet_vouchers.write(row, 0, "Waardebon")
    sheet_vouchers.write(row, 1, "Interne rekening")
    sheet_vouchers.write(row, 2, "Kostenplaats")
    sheet_vouchers.write(row, 3, "Uitgegeven op")
    sheet_vouchers.write(row, 4, "Openstaande waarde")
    for voucher in vouchers:
        unique_vouchers[voucher.key()] = voucher
        row += 1
        sheet_vouchers.write(row, 0, voucher.uid)
        sheet_vouchers.write(row, 1, voucher.internal_account)
        sheet_vouchers.write(row, 2, voucher.cost_center)
        sheet_vouchers.write(row, 3, voucher.dt)
        value = voucher.value - voucher.redeemed_value
        sheet_vouchers.write(row, 4, round(value / 100.0, 2))
    
    row += 2
    sheet_vouchers.write(row, 0, "Totaal")
    sheet_vouchers.write(row, 2, xlwt.Formula('SUM(E2:E%s)' % (row -1)))
    
    # TAB 4
    sheet_voucher_details = book.add_sheet("Bonnen detail")
    row = 0
    for voucher in sorted(unique_vouchers.itervalues(), key=lambda v: v.created):
        voucher_transactions = [h for h in voucher.load_transactions()]
        sheet_voucher_details.write(row, 0, "Waardebon")
        sheet_voucher_details.write(row, 1, voucher.uid)
        sheet_voucher_details.write(row, 2, "Openstaande waarde")
        sheet_voucher_details.write(row, 3, xlwt.Formula('SUM(D%s:D%s)' % (row + 2,  row + 1 + len(voucher_transactions))))
        
        row += 1
        sheet_voucher_details.write(row, 0, "Interne rekening")
        sheet_voucher_details.write(row, 1, voucher.internal_account)
        sheet_voucher_details.write(row, 2, "Kostenplaats")
        sheet_voucher_details.write(row, 3, voucher.cost_center)
        
        for history in reversed(voucher_transactions):
            merchant_service_user = history.service_user or service_user
            if merchant_service_user not in merchants:
                merchants[merchant_service_user] = get_solution_settings(merchant_service_user)
            
            row += 1
            dt = format_datetime(history.created, 'EEE d MMM yyyy HH:mm',
                                        tzinfo=get_timezone(sln_settings.timezone), locale=customer.language)
            
            sheet_voucher_details.write(row, 0, dt)
            sheet_voucher_details.write(row, 1, merchants[merchant_service_user].name)
            sheet_voucher_details.write(row, 2, history.action_str)
            if history.action == SolutionCityVoucherTransaction.ACTION_ACTIVATED or \
                history.action == SolutionCityVoucherTransaction.ACTION_REDEEMED:
                sheet_voucher_details.write(row, 3, round(history.value / 100.0, 2))
        
        row += 2
    
    excel_file = StringIO()
    book.save(excel_file)
    excel_string = excel_file.getvalue()
    
    second_day_of_last_month = first_day_of_last_month + 86400
    d = datetime.fromtimestamp(second_day_of_last_month)
      
    sln_city_voucher_export_key = SolutionCityVoucherExport.create_key(app_id, d.year, d.month)
    sln_city_voucher_export = SolutionCityVoucherExport(key=sln_city_voucher_export_key)
    sln_city_voucher_export.xls = excel_string
    sln_city_voucher_export.year_month = d.year * 100 + d.month
    sln_city_voucher_export.put()
    
    for merchant_service_user in merchant_transactions.keys():
        deferred.defer(create_voucher_statistics_for_service, merchants[merchant_service_user], app_id, customer.language, \
                       merchant_transactions[merchant_service_user]["transactions"], d.year, d.month)
 
    to_emails = sln_settings.inbox_mail_forwarders
    if to_emails:
        solution_server_settings = get_solution_server_settings()
        msg = MIMEMultipart('mixed')
        msg['Subject'] = 'Waardebonnen export'
        msg['From'] = solution_server_settings.shop_export_email
        msg['To'] = ','.join(to_emails)
        msg["Reply-To"] = solution_server_settings.shop_no_reply_email
        body = MIMEText('Zie bijlage om de waardebonnen export te bekijken.', 'plain', 'utf-8')
        msg.attach(body)
     
        att = MIMEApplication(excel_string, _subtype='vnd.ms-excel')
        att.add_header('Content-Disposition', 'attachment', filename='Waardebonnen %s-%s.xls' % (d.year, d.month))
        msg.attach(att)
     
        server_settings = get_server_settings()
        send_mail_via_mime(server_settings.senderEmail, to_emails, msg)


def create_voucher_statistics_for_service(sln_settings, app_id, language, transaction_keys, year, month):
    transactions = SolutionCityVoucherTransaction.get(transaction_keys)
    book = xlwt.Workbook(encoding="utf-8")
    
    sheet_transactions = book.add_sheet("Transacties")
    row = 0
    sheet_transactions.write(row, 0, "Tijdstip")
    sheet_transactions.write(row, 1, "Waardebon")
    sheet_transactions.write(row, 2, "Opgenomen waarde")
    for transaction in transactions:
        transaction.dt = format_datetime(transaction.created, 'EEE d MMM yyyy HH:mm',
                                         tzinfo=get_timezone(sln_settings.timezone), locale=language)
        transaction.voucher = transaction.parent()
        row += 1
        sheet_transactions.write(row, 0, transaction.dt)
        sheet_transactions.write(row, 1, transaction.voucher.uid)
        sheet_transactions.write(row, 2, round(transaction.value / 100.0, 2))
    row += 2
    sheet_transactions.write(row, 0, "Totaal")
    sheet_transactions.write(row, 2, xlwt.Formula('SUM(C2:C%s)' % (row -1)))
    
    excel_file = StringIO()
    book.save(excel_file)
    excel_string = excel_file.getvalue()
    
    export_key = SolutionCityVoucherExportMerchant.create_key(sln_settings.service_user, None, year, month)
    export = SolutionCityVoucherExportMerchant(key=export_key)
    export.xls = excel_string
    export.year_month = year * 100 + month
    export.put()
