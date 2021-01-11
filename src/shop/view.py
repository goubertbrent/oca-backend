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
import os
from collections import namedtuple
from types import NoneType

import base64
import csv
import datetime
import logging
import webapp2
from cgi import FieldStorage
from google.appengine.api import users as gusers
from google.appengine.ext import db, deferred, ndb
from google.appengine.ext.webapp import template

from add_1_monkey_patches import DEBUG
from mcfw.consts import REST_TYPE_TO
from mcfw.exceptions import HttpBadRequestException
from mcfw.properties import azzert
from mcfw.restapi import rest
from mcfw.rpc import arguments, returns
from rogerthat.bizz import channel
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.gcs import upload_to_gcs
from rogerthat.bizz.profile import create_user_profile
from rogerthat.bizz.session import switch_to_service_identity, create_session
from rogerthat.consts import OFFICIALLY_SUPPORTED_COUNTRIES, ROGERTHAT_ATTACHMENTS_BUCKET
from rogerthat.dal.app import get_apps, get_apps_by_type, get_app_by_id
from rogerthat.dal.profile import get_service_profile, get_profile_info
from rogerthat.exceptions import ServiceExpiredException
from rogerthat.models import App, ServiceProfile
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.settings import get_server_settings
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from rogerthat.utils import now
from rogerthat.utils.channel import broadcast_via_iframe_result
from rogerthat.utils.cookie import set_cookie
from rogerthat.utils.service import create_service_identity_user
from rogerthat.utils.transactions import on_trans_committed, allow_transaction_propagation
from shop.bizz import search_customer, create_or_update_customer, create_contact, export_customers_csv, put_service, \
    update_contact, delete_contact, import_customer, export_cirklo_customers_csv
from shop.business.permissions import is_admin
from shop.business.qr import generate_unassigned_qr_codes_zip_for_app
from shop.constants import OFFICIALLY_SUPPORTED_LANGUAGES, COUNTRY_DEFAULT_LANGUAGES
from shop.dal import get_shop_loyalty_slides, get_shop_loyalty_slides_new_order, get_customer
from shop.exceptions import DuplicateCustomerNameException, CustomerNotFoundException
from shop.jobs.migrate_user import migrate as migrate_user
from shop.models import Customer, Contact, RegioManager, ShopLoyaltySlide, ShopLoyaltySlideNewOrder, ShopExternalLinks
from shop.to import CustomerTO, ContactTO, CustomerServiceTO, CustomerReturnStatusTO, JobReturnStatusTO, JobStatusTO, \
    ModulesReturnStatusTO, SimpleAppTO, ImportCustomersReturnStatusTO
from solutions.common.bizz import SolutionModule, OrganizationType
from solutions.common.bizz.locations import create_new_location
from solutions.common.bizz.loyalty import update_all_user_data_admins
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionSettings
from solutions.common.q_and_a.models import QuestionReply, Question
from solutions.common.to import ProvisionReturnStatusTO
from solutions.common.to.loyalty import LoyaltySlideTO, LoyaltySlideNewOrderTO
from solutions.common.utils import get_extension_for_content_type

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


@returns(ReturnStatusTO)
def wrap_with_result_status(f, *args, **kwargs):
    try:
        f(*args, **kwargs)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


def _get_solution_modules():
    return SolutionModule.shop_modules()


def _get_default_modules():
    return (SolutionModule.AGENDA,
            SolutionModule.ASK_QUESTION,
            SolutionModule.NEWS,
            SolutionModule.BULK_INVITE,
            SolutionModule.QR_CODES,
            SolutionModule.WHEN_WHERE,
            SolutionModule.STATIC_CONTENT
            )


def get_current_http_host(with_protocol=False):
    host = os.environ.get('HTTP_X_FORWARDED_HOST') or os.environ.get('HTTP_HOST')
    if with_protocol:
        return u'%s://%s' % (os.environ['wsgi.url_scheme'], host)
    return host


def _get_apps():
    apps = get_apps_by_type(App.APP_TYPE_CITY_APP)
    rt_app = get_app_by_id(App.APP_ID_ROGERTHAT)
    return sorted(apps + [rt_app], key=lambda app: app.name)


def _get_default_organization_types():
    # organization_type value, description, selected by default
    organization_types = [(ServiceProfile.ORGANIZATION_TYPE_CITY, 'Community Service', False),
                          (ServiceProfile.ORGANIZATION_TYPE_EMERGENCY, 'Care', False),
                          (ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT, 'Association', False),
                          (ServiceProfile.ORGANIZATION_TYPE_PROFIT, 'Merchant', True),
                          ]
    return sorted(organization_types, key=lambda x: x[1])


def authorize_manager():
    user = gusers.get_current_user()

    if gusers.is_current_user_admin() or is_admin(user):
        return True

    manager = RegioManager.create_key(user.email()).get()
    return bool(manager)


def get_shop_context(**kwargs):
    user = gusers.get_current_user()
    # These are the variables used in base.html
    js_templates = kwargs.pop('js_templates', {})
    js_templates.update(render_js_templates(['customer_popup'], is_folders=True))
    js_templates.update(render_js_templates(['app_select_modal']))
    ctx = {
        'modules': _get_solution_modules(),
        'default_modules': _get_default_modules(),
        'admin': is_admin(user),
        'js_templates': json.dumps(js_templates),
        'languages': sorted(OFFICIALLY_SUPPORTED_LANGUAGES.iteritems(), key=lambda (k, v): v),
        'countries': sorted(OFFICIALLY_SUPPORTED_COUNTRIES.iteritems(), key=lambda (k, v): v),
        'default_languages_json': json.dumps(COUNTRY_DEFAULT_LANGUAGES),
        'DEBUG': DEBUG,
        'organization_types': _get_default_organization_types()
    }
    ctx.update(kwargs)
    return ctx


def render_js_templates(tmpl_names, is_folders=False):
    templates = {}
    if is_folders:
        for folder in tmpl_names:
            path = os.path.join(os.path.dirname(__file__), 'templates', 'js', folder)
            for template_file in os.listdir(path):
                with open(os.path.join(path, template_file)) as f:
                    key = '%s/%s' % (folder, template_file.replace('.html', '').replace('.tmpl', ''))
                    templates[key] = f.read()
    else:
        for tmpl in tmpl_names:
            with open(os.path.join(os.path.dirname(__file__), 'templates', 'js', '%s.html' % tmpl)) as f:
                templates[tmpl] = f.read()
    return templates


class BizzManagerHandler(webapp2.RequestHandler):

    def dispatch(self):
        if not authorize_manager():
            logging.warning('User %s has no permission to this page', gusers.get_current_user())
            self.abort(401)
        return super(BizzManagerHandler, self).dispatch()

    def render_template(self, name, **context):
        context.update(get_shop_context())
        channel.append_firebase_params(context)
        path = os.path.join(os.path.dirname(__file__), 'html', '%s.html' % name)
        self.response.write(template.render(path, context))


class BizzAdminHandler(BizzManagerHandler):

    def get(self, *args, **kwargs):
        if self.request.get('iframe', 'false') != 'true':
            # loads admin.html in an iframe
            path = os.path.join(os.path.dirname(__file__), 'html', 'index.html')
            context = {
                'DEBUG': DEBUG,
            }
            channel.append_firebase_params(context)
        else:
            path = os.path.join(os.path.dirname(__file__), 'html', 'admin.html')
            context = get_shop_context()
            model = ShopExternalLinks.create_key().get()
            context['external_links'] = model.links if model else []
        self.response.out.write(template.render(path, context))


class ShopLogoutHandler(webapp2.RequestHandler):

    def get(self):
        self.redirect(gusers.create_logout_url("/internal/shop"))


class QuestionsHandler(BizzManagerHandler):

    def get(self):
        cursor = self.request.get('cursor') or None
        questions, new_cursor, _ = Question.list_latest() \
            .fetch_page(20, start_cursor=cursor and ndb.Cursor.from_websafe_string(cursor))
        path = os.path.join(os.path.dirname(__file__), 'html', 'questions.html')
        context = get_shop_context(questions=questions,
                                   cursor=new_cursor and new_cursor.to_websafe_string() or '')
        self.response.out.write(template.render(path, context))


class QuestionsDetailHandler(BizzManagerHandler):

    def get(self, question_id):
        question = Question.get_by_id(long(question_id))
        path = os.path.join(os.path.dirname(__file__), 'html', 'questions_detail.html')
        all_replies = QuestionReply.list_by_question(question.key)
        context = get_shop_context(question=question, all_replies=all_replies,
                                   question_statuses=Question.STATUS_STRINGS.iteritems())
        self.response.out.write(template.render(path, context))


class LoginAsCustomerHandler(BizzManagerHandler):

    def get(self):
        google_user = gusers.get_current_user()
        customer_id = int(self.request.get("customer_id"))
        layout_only = bool(self.request.get("layout_only"))

        if is_admin(google_user):
            access = RegioManager.ACCESS_FULL
            customer = Customer.get_by_id(customer_id)
            service_identity_user = create_service_identity_user(users.User(customer.service_email))
        else:
            regio_manager = RegioManager.create_key(google_user.email()).get()
            customer = db.get(Customer.create_key(customer_id))
            service_identity_user = create_service_identity_user(users.User(customer.service_email))
            if not regio_manager:
                access = RegioManager.ACCESS_NO
            else:
                access = regio_manager.has_access()

        if access == RegioManager.ACCESS_NO:
            self.response.out.write("Access denied!")
            logging.critical("%s tried to login to dashboard of %s (customer_id: %s)",
                             google_user.email(), customer.name, customer_id)
        else:
            session = users.get_current_session()
            if not session or session.type != session.TYPE_ROGERTHAT:
                rogerthat_user = users.User(google_user.email())
                profile_info = get_profile_info(rogerthat_user)
                if not profile_info:
                    create_user_profile(rogerthat_user, google_user.email().replace("@", " at ")) # todo communities set community_id
                try:
                    secret, session = create_session(rogerthat_user, ignore_expiration=True)
                except ServiceExpiredException:
                    return self.redirect('/service_expired')
                server_settings = get_server_settings()
                set_cookie(self.response, server_settings.cookieSessionName, secret)
            switch_to_service_identity(session, service_identity_user, access == RegioManager.ACCESS_READ_ONLY,
                                       shop=True, layout_only=layout_only)
            self.redirect("/")


class ExportEmailAddressesHandler(BizzManagerHandler):

    def get(self):
        azzert(is_admin(gusers.get_current_user()))

        Export = namedtuple('Export', 'email first_name last_name')

        result = dict()
        for contact in Contact.all():
            result[contact.email.strip().lower()] = Export(contact.email, contact.first_name, contact.last_name)

        self.response.headers['Content-Type'] = 'application/vnd.ms-excel'
        self.response.headers['Content-Disposition'] = str('attachment; filename=contacts_export_%s.csv' % now())
        writer = csv.writer(self.response.out, dialect='excel')
        for export in result.values():
            writer.writerow((export.email.encode("utf-8"),
                             export.first_name.encode("utf-8"),
                             export.last_name.encode("utf-8")))


class CustomersImportHandler(BizzManagerHandler):

    def get(self):
        return self.render_template('customers_import')


@rest("/internal/shop/rest/customers/export", "get")
@returns(ReturnStatusTO)
@arguments()
def export_customers():
    google_user = gusers.get_current_user()
    azzert(is_admin(google_user))
    deferred.defer(export_customers_csv, google_user)
    return RETURNSTATUS_TO_SUCCESS


@rest("/internal/shop/rest/customers/cirklo/export", "get")
@returns(ReturnStatusTO)
@arguments(app_id=unicode)
def export_cirklo_customers(app_id):
    google_user = gusers.get_current_user()
    azzert(is_admin(google_user))
    deferred.defer(export_cirklo_customers_csv, google_user, app_id)
    return RETURNSTATUS_TO_SUCCESS


@rest("/internal/shop/rest/customer/put", "post")
@returns(CustomerReturnStatusTO)
@arguments(customer_id=(int, long, NoneType), name=unicode, address1=unicode, address2=unicode, zip_code=unicode,
           city=unicode, country=unicode, language=unicode, vat=unicode, organization_type=(int, long),
           force=bool, community_id=(int, long))
def put_customer(customer_id, name, address1, address2, zip_code, city, country, language, vat, organization_type,
                 force=False, community_id=0):
    try:
        customer = create_or_update_customer(customer_id, vat, name, address1, address2,
                                             zip_code, city, country, language, organization_type, force,
                                             community_id=community_id)
    except DuplicateCustomerNameException as ex:
        return CustomerReturnStatusTO.create(False, warning=ex.message)
    except BusinessException as be:
        return CustomerReturnStatusTO.create(False, be.message)

    return CustomerReturnStatusTO.create(customer=CustomerTO.fromCustomerModel(customer))


@rest("/internal/shop/rest/customer/find", "get")
@returns([CustomerTO])
@arguments(search_string=unicode)
def find_customer(search_string):
    return [CustomerTO.fromCustomerModel(c) for c in search_customer(search_string, [])]


@rest("/internal/shop/rest/customer", "get")
@returns(CustomerReturnStatusTO)
@arguments(customer_id=(int, long))
def get_customer_details(customer_id):
    try:
        customer = db.run_in_transaction(Customer.get_by_id, customer_id)
    except CustomerNotFoundException as exception:
        return CustomerReturnStatusTO.create(False, errormsg=exception.message)
    return CustomerReturnStatusTO.create(True, customer=CustomerTO.fromCustomerModel(customer))


@rest('/internal/shop/rest/customers/<customer_id:[^/]+>/contacts', 'post', type=REST_TYPE_TO)
@returns(ContactTO)
@arguments(customer_id=(int, long), data=ContactTO)
def new_contact(customer_id, data):
    # type: (long, ContactTO) -> ContactTO
    try:
        contact = create_contact(customer_id, data.first_name, data.last_name, data.email, data.phone_number)
        return ContactTO.fromContactModel(contact)
    except BusinessException as e:
        raise HttpBadRequestException(e.message)


@rest('/internal/shop/rest/customers/<customer_id:[^/]+>/contacts/<contact_id:[^/]+>', 'put', type=REST_TYPE_TO)
@returns(ContactTO)
@arguments(customer_id=(int, long), contact_id=(int, long), data=ContactTO)
def save_contact(customer_id, contact_id, data):
    # type: (long, long, ContactTO) -> ContactTO
    try:
        contact = update_contact(customer_id, contact_id, data.first_name, data.last_name, data.email,
                                 data.phone_number)
        return ContactTO.fromContactModel(contact)
    except BusinessException as e:
        raise HttpBadRequestException(e.message)


@rest('/internal/shop/rest/customers/<customer_id:[^/]+>/contacts/<contact_id:[^/]+>', 'delete')
@returns()
@arguments(customer_id=(int, long), contact_id=(int, long))
def delete_contact_rest(customer_id, contact_id):
    try:
        delete_contact(customer_id, contact_id)
    except BusinessException as e:
        raise HttpBadRequestException(e.message)


@rest('/internal/shop/rest/customers/<customer_id:[^/]+>/contacts', 'get')
@returns([ContactTO])
@arguments(customer_id=(int, long))
def list_contacts(customer_id):
    return [ContactTO.fromContactModel(c) for c in Contact.list(Customer.create_key(customer_id))]


@rest("/internal/shop/rest/customer/get_default_modules", "get")
@returns(ModulesReturnStatusTO)
@arguments(customer_id=(int, long))
def get_default_modules(customer_id):
    return ModulesReturnStatusTO.create(success=False, modules=_get_default_modules(), errormsg=None)


def check_only_one_city_service(customer_id, service):
    # type: (int, CustomerServiceTO) -> None
    if SolutionModule.CITY_APP in service.modules:
        community = get_community(service.community_id)
        customer = Customer.get_by_id(customer_id)  # type: Customer
        customers = Customer.list_enabled_by_organization_type_in_community(service.community_id, OrganizationType.CITY) \
            .fetch(None)  # type: List[Customer]
        settings = {s.service_user.email(): s for s in
                    db.get([SolutionSettings.create_key(c.service_user) for c in customers if c.service_email])}
        for other_customer in customers:  # type: Customer
            sln_settings = settings.get(other_customer.service_email)
            if sln_settings and other_customer.service_email != customer.service_email \
                and SolutionModule.CITY_APP in sln_settings.modules:
                msg = 'City app module cannot be enabled for more than one service per community. ' \
                      'Service %s (%s) currently has the city app module enabled for community %s(%d)' % (
                          other_customer.service_email, other_customer.name, community.name, community.id)
                raise BusinessException(msg)


@rest("/internal/shop/rest/service/put", "post")
@returns(ProvisionReturnStatusTO)
@arguments(customer_id=(int, long), service=CustomerServiceTO)
def save_service(customer_id, service):
    try:
        check_only_one_city_service(customer_id, service)
        xg_on = db.create_transaction_options(xg=True)
        service = allow_transaction_propagation(db.run_in_transaction_options, xg_on, put_service, customer_id, service,
                                                broadcast_to_users=[gusers.get_current_user()])
        return ProvisionReturnStatusTO.create(True, None, service)
    except BusinessException as ex:
        logging.warn(ex, exc_info=1)
        return ProvisionReturnStatusTO.create(False, ex)
    except:
        logging.error("Failed to create service", exc_info=1)
        return ProvisionReturnStatusTO.create(False, "An unknown error has occurred. Please call Mobicage support.")


@rest("/internal/shop/rest/customer/service/get", "get")
@returns(CustomerServiceTO)
@arguments(customer_id=long)
def get_service(customer_id):
    return _get_service(customer_id, gusers.get_current_user())


def _get_service(customer_id, current_user):
    customer = Customer.get_by_id(customer_id)  # type: Customer
    service_user = users.User(customer.service_email)

    settings = get_solution_settings(service_user)
    svc = CustomerServiceTO()
    svc.email = customer.user_email
    svc.language = settings.main_language
    svc.modules = settings.modules
    svc.organization_type = get_service_profile(service_user).organizationType
    svc.managed_organization_types = customer.managed_organization_types or []
    svc.community_id = customer.community_id
    return svc


@rest("/internal/shop/rest/service/change_email", "post")
@returns(JobReturnStatusTO)
@arguments(customer_id=(long, int), email=unicode)
def change_service_email(customer_id, email):
    customer = Customer.get_by_id(customer_id)
    logging.info('Changing customer.user_email from "%s" to "%s"', customer.user_email, email)

    to_user = users.User(email)
    try:
        if customer.user_email == customer.service_email:
            return JobReturnStatusTO.create(False, 'It is not possible to change the email of this service')
        else:
            from_user = users.User(customer.user_email)
            migrate_user(users.get_current_user(), from_user, to_user, customer.service_email, customer_id=customer_id)
            return JobReturnStatusTO.create()
    except BusinessException, e:
        logging.warn(e, exc_info=1)
        return JobReturnStatusTO.create(False, e.message)
    except:
        logging.exception("Failed to start the email migration job")
        return JobReturnStatusTO.create(False, "An unknown error has occurred. Please call Mobicage support.")


@rest("/internal/shop/rest/location/add", "post")
@returns(ReturnStatusTO)
@arguments(customer_id=(long, int), name=unicode)
def add_location(customer_id, name):
    customer = Customer.get_by_id(customer_id)
    create_new_location(customer.service_user, name, broadcast_to_users=[gusers.get_current_user()])
    return ReturnStatusTO.create()


@rest("/internal/shop/rest/job/get_status", "get")
@returns(JobStatusTO)
@arguments(job=unicode)
def get_job_status(job):
    job_model = db.get(job)
    return JobStatusTO.from_model(job_model)


@rest("/internal/shop/rest/loyalty/slides/delete", "post")
@returns(ReturnStatusTO)
@arguments(slide_id=(int, long))
def delete_loyalty_slide(slide_id):
    azzert(is_admin(gusers.get_current_user()))
    try:
        def trans():
            sli = ShopLoyaltySlide.get_by_id(slide_id)
            if sli:
                sli.deleted = True
                sli.put()
                on_trans_committed(update_all_user_data_admins, sli.apps if sli.has_apps else [])

        db.run_in_transaction(trans)

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)


@rest("/internal/shop/rest/loyalty/slides/new_order/delete", "post")
@returns(ReturnStatusTO)
@arguments(slide_id=unicode)
def delete_loyalty_slide_new_order(slide_id):
    azzert(is_admin(gusers.get_current_user()))
    try:
        sli_key = ShopLoyaltySlideNewOrder.create_key(slide_id)
        sli = ShopLoyaltySlideNewOrder.get(sli_key)
        if sli:
            update_all_user_data_admins([sli.app_id])
            db.delete(sli_key)

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)


class LoyaltySlidesHandler(BizzManagerHandler):

    def get(self):
        current_user = gusers.get_current_user()
        if not is_admin(current_user):
            self.abort(403)
        path = os.path.join(os.path.dirname(__file__), 'html', 'loyalty_slides.html')
        context = get_shop_context(slides=[LoyaltySlideTO.fromSolutionLoyaltySlideObject(c, include_apps=True)
                                           for c in get_shop_loyalty_slides()],
                                   current_user_apps=_get_apps())
        self.response.out.write(template.render(path, context))


class LoyaltySlidesNewOrderHandler(BizzManagerHandler):

    def get(self):
        current_user = gusers.get_current_user()
        if not is_admin(current_user):
            self.abort(403)
        path = os.path.join(os.path.dirname(__file__), 'html', 'loyalty_slides_new_order.html')
        context = get_shop_context(slides=[LoyaltySlideNewOrderTO.fromSlideObject(c)
                                           for c in get_shop_loyalty_slides_new_order()],
                                   current_user_apps=_get_apps())
        self.response.out.write(template.render(path, context))


class UploadLoyaltySlideHandler(BizzManagerHandler):

    def post(self):
        current_user = gusers.get_current_user()
        if not is_admin(current_user):
            self.abort(403)
        slide_id = self.request.get("slide_id", "")
        slide_name = self.request.get("slide_name", "")
        try:
            slide_time = long(self.request.get("slide_time", 10))
        except:
            self.response.out.write(broadcast_via_iframe_result(u"rogerthat.internal.shop.loyalty.slide.post_result",
                                                                error=u"Please fill in valid time!"))
            return
        slide_function_dependencies = long(self.request.get("slide_function_dependencies", 0))
        slide_apps = self.request.get("slide_apps", "[]")

        if slide_id == "":
            slide_id = None
        else:
            slide_id = long(slide_id)

        apps = json.loads(slide_apps)

        uploaded_file = self.request.POST.get('slide_file')  # type: FieldStorage
        if not slide_id and not isinstance(uploaded_file, FieldStorage):
            self.response.out.write(broadcast_via_iframe_result(u"rogerthat.internal.shop.loyalty.slide.post_result",
                                                                error=u"Please select a picture!"))
            return

        gcs_filename = None
        content_type = None
        if isinstance(uploaded_file, FieldStorage):
            content_type = uploaded_file.type
            if not content_type.startswith("image/"):
                self.response.out.write(broadcast_via_iframe_result(u"rogerthat.internal.shop.loyalty.slide.post_result",
                                                                    error=u"The uploaded file is not an image!"))
                return

            date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
            gcs_filename = '%s/oca/shop/loyalty/slides/%s_%s.%s' % (ROGERTHAT_ATTACHMENTS_BUCKET,
                                                                    date,
                                                                    uploaded_file.filename,
                                                                    get_extension_for_content_type(content_type))
            upload_to_gcs(uploaded_file.value, content_type, gcs_filename)

        def trans():
            if slide_id:
                sli = ShopLoyaltySlide.get_by_id(slide_id)
            else:
                sli = ShopLoyaltySlide()
                sli.timestamp = now()

            sli.deleted = False
            sli.name = slide_name
            sli.time = slide_time
            if gcs_filename:
                sli.gcs_filename = gcs_filename
            if content_type:
                sli.content_type = content_type
            if apps:
                sli.has_apps = True
            else:
                sli.has_apps = False
            sli.apps = apps
            sli.function_dependencies = slide_function_dependencies
            sli.put()
            on_trans_committed(update_all_user_data_admins, sli.apps if sli.has_apps else [])

        db.run_in_transaction(trans)

        self.response.out.write(broadcast_via_iframe_result(u"rogerthat.internal.shop.loyalty.slide.post_result"))


class UploadLoyaltySlideNewOrderHandler(BizzManagerHandler):

    def post(self):
        current_user = gusers.get_current_user()
        if not is_admin(current_user):
            self.abort(403)
        slide_id = self.request.get("slide_id", "")
        try:
            slide_time = long(self.request.get("slide_time", 10))
        except:
            self.response.out.write(broadcast_via_iframe_result(u"rogerthat.internal.shop.loyalty.slide.new_order.post_result",
                                                                error=u"Please fill in valid time!"))
            return
        slide_app_id = self.request.get("slide_app", "")
        if slide_app_id == "":
            slide_app_id = None

        if slide_id == "":
            slide_id = None

        uploaded_file = self.request.POST.get('slide_file')  # type: FieldStorage
        if not slide_id and not isinstance(uploaded_file, FieldStorage):
            self.response.out.write(broadcast_via_iframe_result(u"rogerthat.internal.shop.loyalty.slide.new_order.post_result",
                                                                error=u"Please select a picture!"))
            return

        gcs_filename = None
        content_type = None
        if isinstance(uploaded_file, FieldStorage):
            content_type = uploaded_file.type
            if not content_type.startswith("image/"):
                self.response.out.write(broadcast_via_iframe_result(u"rogerthat.internal.shop.loyalty.slide.post_result",
                                                                    error=u"The uploaded file is not an image!"))
                return

            date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
            gcs_filename = '%s/oca/shop/loyalty/new_order_slides/%s_%s.%s' % (ROGERTHAT_ATTACHMENTS_BUCKET,
                                                                              date,
                                                                              uploaded_file.filename,
                                                                              get_extension_for_content_type(content_type))
            upload_to_gcs(uploaded_file.value, content_type, gcs_filename)

        def trans():
            if slide_id:
                sli = ShopLoyaltySlideNewOrder.get(ShopLoyaltySlideNewOrder.create_key(slide_id))
            else:
                if slide_app_id is None:
                    self.response.out.write(broadcast_via_iframe_result(u"rogerthat.internal.shop.loyalty.slide.new_order.post_result",
                                                                        error=u"Missing app"))
                    return
                sli = ShopLoyaltySlideNewOrder(key=ShopLoyaltySlideNewOrder.create_key(slide_app_id))
                sli.timestamp = now()

            sli.time = slide_time
            if gcs_filename:
                sli.gcs_filename = gcs_filename
            if content_type:
                sli.content_type = content_type
            sli.put()
            on_trans_committed(update_all_user_data_admins, [sli.app_id])

        db.run_in_transaction(trans)

        self.response.out.write(broadcast_via_iframe_result(
            u"rogerthat.internal.shop.loyalty.slide.new_order.post_result"))


@rest("/internal/shop/log_error", "post")
@returns(NoneType)
@arguments(description=unicode, errorMessage=unicode, timestamp=int, user_agent=unicode)
def log_error(description, errorMessage, timestamp, user_agent):
    from rogerthat.bizz.system import logErrorBizz
    from rogerthat.to.system import LogErrorRequestTO
    request = LogErrorRequestTO()
    request.description = description
    request.errorMessage = errorMessage
    request.mobicageVersion = u"web"
    request.platform = 0
    request.platformVersion = user_agent
    request.timestamp = timestamp
    return logErrorBizz(request, gusers.get_current_user(), session=users.get_current_session())


@rest("/internal/shop/rest/apps/all", "get")
@returns([SimpleAppTO])
@arguments()
def load_all_apps():
    return [SimpleAppTO.from_model(a) for a in get_apps([App.APP_TYPE_CITY_APP], only_visible=False)]


@rest("/internal/shop/rest/customers/generate_qr_codes", "get")
@returns(ReturnStatusTO)
@arguments(app_id=unicode, amount=(int, long), mode=unicode)
def rest_generate_qr_codes(app_id, amount, mode):
    return wrap_with_result_status(generate_unassigned_qr_codes_zip_for_app, app_id, amount, mode)


@rest('/internal/shop/customers/import/sheet', 'post')
@returns(ImportCustomersReturnStatusTO)
@arguments(import_id=(int, long), community_id=(int, long), file_data=str)
def rest_import_customers(import_id, community_id, file_data):
    user = gusers.get_current_user()

    community = get_community(community_id)
    city_service_user = community.main_service_user
    sln_settings = get_solution_settings(city_service_user)
    city_customer = get_customer(city_service_user)
    currency = sln_settings.currency

    try:
        stream = StringIO(base64.b64decode(file_data))
        stream.readline()  # skip header
        reader = csv.reader(stream)
    except csv.Error:
        return ImportCustomersReturnStatusTO.create(
            False, 'Invalid csv format'
        )

    customer_count = 0
    for row in reader:
        try:
            _, org_type_name, name, vat, email, phone, address, zip_code, \
                city, website, facebook_page, contact_name, contact_address, contact_zipcode, \
                contact_city, contact_email, contact_phone = map(unicode, [v.decode('utf-8') for v in row])
        except ValueError:
            return ImportCustomersReturnStatusTO.create(
                False, 'Invalid csv file header/column format'
            )

        customer_count += 1
        deferred.defer(
            import_customer, user, import_id, community_id, city_customer, currency, name, vat, org_type_name,
            email, phone, address, zip_code, city, website, facebook_page, contact_name, contact_address,
            contact_zipcode, contact_city, contact_email, contact_phone
        )

    return ImportCustomersReturnStatusTO.create(True, customer_count=customer_count)


class ConsoleHandler(BizzManagerHandler):
    def get(self, route=''):
        if DEBUG:
            url = 'http://localhost:4199' + route
        else:
            url = '/console' + route
        path = os.path.join(os.path.dirname(__file__), 'html', 'console.html')
        context = get_shop_context(url=url)
        self.response.out.write(template.render(path, context))


class ConsoleIndexHandler(webapp2.RequestHandler):
    def get(self, route=''):
        path = os.path.join(os.path.dirname(__file__), 'html', 'console-index.html')
        self.response.out.write(template.render(path, {}))
