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

import base64
import binascii
import datetime
import json
import logging
import os
import re

import webapp2
from dateutil.relativedelta import relativedelta

from google.appengine.api import search
from google.appengine.api import users as gusers
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from mcfw.cache import cached
from mcfw.consts import MISSING
from mcfw.restapi import rest
from mcfw.rpc import serialize_complex_value, arguments, returns
from mcfw.serialization import s_ushort
from rogerthat.bizz.beacon import add_new_beacon
from rogerthat.bizz.friends import user_code_by_hash, makeFriends, ORIGIN_USER_INVITE
from rogerthat.bizz.service import SERVICE_LOCATION_INDEX
from rogerthat.dal import parent_key
from rogerthat.dal.app import get_app_by_id
from rogerthat.dal.service import get_service_interaction_def, get_service_identity
from rogerthat.models import Beacon, App, ProfilePointer, ServiceProfile
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.settings import get_server_settings
from rogerthat.templates import get_languages_from_request
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from rogerthat.utils import get_epoch_from_datetime, bizz_check
from rogerthat.utils.app import get_app_id_from_app_user
from rogerthat.utils.crypto import md5_hex
from shop.bizz import is_admin
from shop.business.i18n import shop_translate
from shop.models import Invoice, OrderItem, Product, Prospect, RegioManagerTeam, LegalEntity, Customer
from shop.to import CustomerLocationTO
from shop.view import get_shop_context
from solution_server_settings import get_solution_server_settings


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class ExportProductsHandler(webapp2.RequestHandler):
    def get(self):
        if self.request.headers.get('X-Rogerthat-Secret') != get_server_settings().secret:
            self.abort(401)

        products = export_products()

        self.response.headers['Content-Type'] = 'text/json'
        self.response.write(json.dumps(products))


class ExportInvoicesHandler(webapp2.RequestHandler):
    def get(self):
        if self.request.headers.get('X-Rogerthat-Secret') != get_server_settings().secret:
            self.abort(401)

        year = int(self.request.GET['year'])
        month = int(self.request.GET['month'])

        invoices = export_invoices(year, month)

        self.response.headers['Content-Type'] = 'text/json'
        self.response.write(json.dumps(invoices))


class ProspectCallbackHandler(webapp2.RequestHandler):

    def get (self):
        solution_server_settings = get_solution_server_settings()
        if not solution_server_settings.tropo_callback_token:
            logging.error("tropo_callback_token is not set yet")
            self.abort(401)

        if self.request.get('token') != solution_server_settings.tropo_callback_token:
            self.abort(401)

        prospect_id = self.request.get('prospect_id')
        if not prospect_id:
            logging.warn("missing prospect_id in prospect callback invite result")
            self.abort(401)

        status = self.request.get('status')
        if not status:
            logging.warn("missing status in prospect callback invite result")
            self.abort(401)

        if status not in Prospect.INVITE_RESULT_STRINGS:
            logging.warn("got unexpected status in prospect callback invite result %s", status)
            self.abort(401)

        prospect_interaction = db.get(prospect_id)
        if not prospect_interaction:
            logging.warn("could not find prospect with key %s", prospect_id)
            self.abort(401)

        prospect = prospect_interaction.prospect
        logging.info("Process callback invite result for prospect with id '%s' and status '%s'", prospect.id, status)
        if status == Prospect.INVITE_RESULT_STRING_YES:
            prospect_interaction.code = prospect.invite_code = Prospect.INVITE_CODE_ANSWERED
            prospect_interaction.result = prospect.invite_result = Prospect.INVITE_RESULT_YES
        elif status == Prospect.INVITE_RESULT_STRING_NO:
            prospect_interaction.code = prospect.invite_code = Prospect.INVITE_CODE_ANSWERED
            prospect_interaction.result = prospect.invite_result = Prospect.INVITE_RESULT_NO
        elif status == Prospect.INVITE_RESULT_STRING_MAYBE:
            prospect_interaction.code = prospect.invite_code = Prospect.INVITE_CODE_ANSWERED
            prospect_interaction.result = prospect.invite_result = Prospect.INVITE_RESULT_MAYBE
        elif status == Prospect.INVITE_RESULT_STRING_NO_ANSWER:
            prospect_interaction.code = prospect.invite_code = Prospect.INVITE_CODE_NO_ANSWER
        elif status == Prospect.INVITE_RESULT_STRING_CALL_FAILURE:
            prospect_interaction.code = prospect.invite_code = Prospect.INVITE_CODE_CALL_FAILURE

        db.put([prospect, prospect_interaction])
        self.response.out.write("Successfully processed invite result")


class StaticFileHandler(webapp2.RequestHandler):
    def get(self, filename):
        cur_path = os.path.dirname(__file__)
        path = os.path.join(cur_path, u'html', filename)
        with open(path, 'r') as f:
            self.response.write(f.read())


def model_to_dict(model):
    d = db.to_dict(model)
    if 'pdf' in d:
        del d['pdf']
    for k, v in d.iteritems():
        if isinstance(v, users.User):
            d[k] = v.email()
    d['_key'] = str(model.key())
    return d


def export_invoices(year, month):
    start_date = datetime.date(year, month, 1)
    end_date = start_date + relativedelta(months=1)

    qry = Invoice.all() \
        .filter('date >=', get_epoch_from_datetime(start_date)) \
        .filter('date <', get_epoch_from_datetime(end_date))

    invoices = list()
    order_keys = set()
    all_products = dict(((p.code, p) for p in Product.all()))
    for invoice_model in qry:
        i = model_to_dict(invoice_model)
        order_key = invoice_model.parent_key().parent()
        i['invoice_number'] = invoice_model.invoice_number
        i['order_items'] = map(model_to_dict, OrderItem.all().ancestor(order_key))
        if invoice_model.charge.is_recurrent:
            # only apply recurrent charges
            for order_item in reversed(i['order_items']):
                order_item['count'] = invoice_model.charge.subscription_extension_length or 1
                product = all_products[order_item['product_code']]
                if not (product.is_subscription_discount or product.is_subscription):
                    i['order_items'].remove(order_item)

            # add the subscription extensions like XCTY
            if invoice_model.charge.subscription_extension_order_item_keys:
                extension_order_items = db.get(invoice_model.charge.subscription_extension_order_item_keys)
                for item in extension_order_items:
                    item.count = 1
                i['order_items'] += map(model_to_dict, extension_order_items)

        i['order_key'] = order_key
        i['currency'] = invoice_model.currency_code
        order_keys.add(order_key)
        invoices.append(i)

    orders = {o.key(): o for o in db.get(order_keys)}

    contact_keys = set()
    customer_keys = set()
    for i in invoices:
        order_model = orders[i['order_key']]
        del i['order_key']
        i['customer_key'] = order_model.customer_key
        i['contact_key'] = order_model.contact_key
        i['manager'] = None if not order_model.manager else order_model.manager.email()
        customer_keys.add(order_model.customer_key)
        contact_keys.add(order_model.contact_key)

    del orders

    customer_and_contact_models = {m.key(): m for m in db.get(customer_keys.union(contact_keys))}

    # filter invoices for customers of resellers
    reseller_ids = [k.id() for k in LegalEntity.list_non_mobicage(keys_only=True)]
    reseller_team_ids = [t.id for t in RegioManagerTeam.all().filter('legal_entity_id IN', reseller_ids)]

    for i in reversed(invoices):
        customer_model = customer_and_contact_models[i['customer_key']]
        if customer_model.team_id in reseller_team_ids:
            invoices.remove(i)
            continue
        del i['customer_key']
        i['customer'] = model_to_dict(customer_model)
        contact_model = customer_and_contact_models[i['contact_key']]
        del i['contact_key']
        i['contact'] = model_to_dict(contact_model)

    del customer_and_contact_models

    return sorted(invoices,
                  key=lambda i: int(i['invoice_number'].split('.')[-1]))


def export_products():
    products = list()
    for product_model in Product.all():
        p = model_to_dict(product_model)
        p['product_code'] = product_model.code
        p['description'] = product_model.description(u'nl')
        p['default_comment'] = product_model.default_comment(u'nl')
        products.append(p)
    return products


class BeaconsAppValidateUrlHandler(webapp2.RequestHandler):
    def post(self):
        # this url is used in the beacon configurator app to override the uuid, major and minor
        from rogerthat.pages.shortner import get_short_url_by_code
        url = self.request.POST.get("url", None)
        signature_client = self.request.POST.get("signature", None)
        if not (url and signature_client):
            logging.error("not all params given")
            self.abort(500)
            return

        signature_client = signature_client.upper()
        logging.info("validate beacon app url: %s and signature: %s", url, signature_client)
        solution_server_settings = get_solution_server_settings()
        signature_server = md5_hex(solution_server_settings.shop_beacons_app_secret % (url, url)).upper()
        logging.info("signature server: %s", signature_server)
        if not (url and signature_client == signature_server):
            logging.error("signature did not match")
            self.abort(500)
            return

        m = re.match("^(HTTP|http)(S|s)?://(.*)/(M|S)/(.*)$", url)
        if not m:
            logging.error("invalid url")
            self.abort(500)
            return

        _, _, _, _, code = m.groups()
        su = get_short_url_by_code(code)
        logging.info("validate short url: %s", su.full)
        if not su.full.startswith("/q/s/"):
            logging.error("short url does not start with /q/s")
            self.abort(500)
            return

        match = re.match("^/q/s/(.+)/(\\d+)$", su.full)
        if not match:
            logging.error("user_code not found in url")
            self.abort(500)
            return

        user_code = match.group(1)
        logging.info("validating user code: %s", user_code)
        sid = match.group(2)
        logging.info("validating sid: %s", sid)
        pp = ProfilePointer.get_by_key_name(user_code)
        if not pp:
            logging.error("ProfilePointer not found")
            self.abort(500)
            return

        sid = get_service_interaction_def(pp.user, int(sid))
        if not sid:
            logging.error("sid not found")
            self.abort(500)
            return

        si = get_service_identity(sid.service_identity_user)

        if not si:
            logging.error("service_identity not found")
            self.abort(500)
            return

        def trans():
            beacon = Beacon.all().ancestor(parent_key(si.service_user)).get()
            if beacon:
                return beacon.uuid, beacon.name
            app = App.get(App.create_key(si.app_id))
            app.beacon_last_minor = app.beacon_last_minor + 1
            name = "%s|%s" % (app.beacon_major, app.beacon_last_minor)
            logging.info("add_new_beacon: %s", name)
            if not add_new_beacon(app.beacon_uuid, name, u'Autoconnect', si.service_identity_user):
                raise Exception("Beacon already exists")

            app.put()
            return app.beacon_uuid, name

        xg_on = db.create_transaction_options(xg=True)
        beacon_uuid, beacon_name = db.run_in_transaction_options(xg_on, trans)

        major, minor = beacon_name.split("|")
        logging.info("Auto connecting beacon %s to service %s", beacon_name, si.service_identity_user)

        outfile = StringIO()
        s_ushort(outfile, int(major))
        s_ushort(outfile, int(minor))
        id_ = base64.b64encode(outfile.getvalue())

        self.response.headers['Content-Type'] = 'text/json'
        self.response.write(json.dumps({"uuid": beacon_uuid,
                                        "major": int(major),
                                        "minor": int(minor),
                                        "email": si.qualifiedIdentifier,
                                        "name": si.name,
                                        "id": id_}))


class GenerateQRCodesHandler(webapp2.RequestHandler):
    def get(self):
        current_user = gusers.get_current_user()
        if not is_admin(current_user):
            self.abort(403)
        path = os.path.join(os.path.dirname(__file__), 'html', 'generate_qr_codes.html')
        context = get_shop_context()
        self.response.out.write(template.render(path, context))


class AppBroadcastHandler(webapp2.RequestHandler):
    def get(self):
        current_user = gusers.get_current_user()
        if not is_admin(current_user):
            self.abort(403)
        path = os.path.join(os.path.dirname(__file__), 'html', 'app_broadcast.html')
        context = get_shop_context()
        self.response.out.write(template.render(path, context))


class CustomerMapHandler(webapp2.RequestHandler):
    def get(self, app_id):
        path = os.path.join(os.path.dirname(__file__), 'html', 'customer_map.html')
        settings = get_server_settings()
        lang = get_languages_from_request(self.request)[0]
        translations = {
            'merchants': shop_translate(lang, 'merchants'),
            'merchants_with_terminal': shop_translate(lang, 'merchants_with_terminal'),
            'community_services': shop_translate(lang, 'community_services'),
            'care': shop_translate(lang, 'care'),
            'associations': shop_translate(lang, 'associations'),
        }
        params = {
            'maps_key': settings.googleMapsKey,
            'app_id': app_id,
            'translations': json.dumps(translations)
        }
        self.response.out.write(template.render(path, params))


@cached(2, 21600)
@returns(unicode)
@arguments(app_id=unicode)
def get_customer_locations_for_app(app_id):
    query_string = (u'app_ids:"%s"' % app_id)
    query = search.Query(query_string=query_string,
                         options=search.QueryOptions(returned_fields=['service', 'name', 'location', 'description'],
                                                     limit=1000))
    search_result = search.Index(name=SERVICE_LOCATION_INDEX).search(query)

    customers = {customer.service_email: customer for customer in Customer.list_by_app_id(app_id)}

    def map_result(service_search_result):
        customer_location = CustomerLocationTO()
        for field in service_search_result.fields:
            if field.name == 'service':
                customer = customers.get(field.value.split('/')[0])
                if customer:
                    customer_location.has_terminal = customer.has_loyalty
                    customer_location.address = customer.address1
                    customer_location.type = customer.organization_type
                    if customer.address2:
                        customer_location.address += '\n%s' % customer.address2
                    if customer.zip_code or customer.city:
                        customer_location.address += '\n'
                        if customer.zip_code:
                            customer_location.address += customer.zip_code
                        if customer.zip_code and customer.city:
                            customer_location.address += ' '
                        if customer.city:
                            customer_location.address += customer.city
                else:
                    customer_location.type = ServiceProfile.ORGANIZATION_TYPE_PROFIT
                continue
            if field.name == 'name':
                customer_location.name = field.value
                continue
            if field.name == 'location':
                customer_location.lat = field.value.latitude
                customer_location.lon = field.value.longitude
                continue
            if field.name == 'description':
                customer_location.description = field.value
                continue
        return customer_location

    return json.dumps(serialize_complex_value([map_result(r) for r in search_result.results], CustomerLocationTO, True))


class CustomerMapServicesHandler(webapp2.RequestHandler):
    def get(self, app_id):
        customer_locations = get_customer_locations_for_app(app_id)
        self.response.write(customer_locations)


@rest('/unauthenticated/loyalty/scanned', 'get', read_only_access=True, authenticated=False)
@returns(ReturnStatusTO)
@arguments(user_email_hash=unicode, merchant_email=unicode, app_id=unicode)
def rest_loyalty_scanned(user_email_hash, merchant_email, app_id):
    try:
        bizz_check(user_email_hash is not MISSING, 'user_email_hash is required')
        bizz_check(merchant_email is not MISSING, 'merchant_email is required')
        bizz_check(app_id is not MISSING, 'app_id is required')

        user_code = user_code_by_hash(binascii.unhexlify(user_email_hash))
        profile_pointer = ProfilePointer.get(user_code)
        if not profile_pointer:
            logging.debug('No ProfilePointer found with user_code %s', user_code)
            raise BusinessException('User not found')
        app_user=profile_pointer.user

        bizz_check(get_app_by_id(app_id), 'App not found')
        bizz_check(app_id == get_app_id_from_app_user(profile_pointer.user), 'Invalid user email hash')

        merchant_found = False
        for customer in Customer.list_by_user_email(merchant_email):
            merchant_found = True
            service_user = users.User(customer.service_email)
            logging.info('Received loyalty scan of %s by %s (%s)', app_user, service_user, customer.user_email)
            makeFriends(service_user, app_user, None, None, ORIGIN_USER_INVITE,
                        notify_invitee=False,
                        notify_invitor=False,
                        allow_unsupported_apps=True)

        bizz_check(merchant_found, 'Merchant not found')
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)
    else:
        return RETURNSTATUS_TO_SUCCESS
