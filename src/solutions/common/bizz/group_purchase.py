# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import base64
import json
import logging
import os
import re
from types import NoneType
from zipfile import ZipFile, ZIP_DEFLATED

from google.appengine.api import images
from google.appengine.ext import db
from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.dal import put_and_invalidate_cache, parent_key_unsafe
from rogerthat.models import Message
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.service.api import messaging, system
from rogerthat.to.messaging import MemberTO
from rogerthat.to.service import UserDetailsTO, SendApiCallCallbackResultTO
from rogerthat.utils import now, file_get_contents
from rogerthat.utils.channel import send_message
from solutions import translate
import solutions
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import broadcast_updates_pending, put_branding
from solutions.common.dal import get_solution_settings, get_solution_main_branding
from solutions.common.handlers import JINJA_ENVIRONMENT
from solutions.common.models.group_purchase import SolutionGroupPurchase, SolutionGroupPurchaseSubscription
from solutions.common.models.properties import SolutionUser
from solutions.common.to import SolutionGroupPurchaseTO
from solutions.common.utils import create_service_identity_user_wo_default


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


API_METHOD_GROUP_PURCHASE_PURCHASE = "solutions.group_purchase.purchase"

@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, group_purchase=SolutionGroupPurchaseTO)
def save_group_purchase(service_user, service_identity, group_purchase):

    picture = group_purchase.picture
    if picture:
        picture = str(picture)
        meta, img_b64 = picture.split(',')
        img_str = base64.b64decode(img_b64)

        previous_len_img = len(img_b64)
        while len(img_b64) > 512 * 1024:
            img = images.Image(img_str)
            img.im_feeling_lucky()
            img_str = img.execute_transforms(output_encoding=images.JPEG)  # Reduces quality to 85%
            img_b64 = base64.b64encode(img_str)
            meta = "data:image/jpg;base64"

            if previous_len_img <= len(img_b64):
                break
            previous_len_img = len(img_b64)

        picture = "%s,%s" % (meta, img_b64)
    else:
        picture = None

    def trans():
        sln_settings = get_solution_settings(service_user)
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        if group_purchase.id:
            sgp = SolutionGroupPurchase.get_by_id(group_purchase.id, parent_key_unsafe(service_identity_user, sln_settings.solution))
            if group_purchase.new_picture:
                sgp.picture_version += 1
        else:
            sgp = SolutionGroupPurchase(parent=parent_key_unsafe(service_identity_user, sln_settings.solution))
            sgp.picture_version = 0

        sgp.title = group_purchase.title
        sgp.description = group_purchase.description
        sgp.units = group_purchase.units
        sgp.unit_description = group_purchase.unit_description
        sgp.unit_price = group_purchase.unit_price
        sgp.min_units_pp = group_purchase.min_units_pp
        sgp.max_units_pp = group_purchase.max_units_pp
        sgp.time_from = group_purchase.time_from
        sgp.time_until = group_purchase.time_until
        sgp.picture = picture

        sln_settings.updates_pending = True
        put_and_invalidate_cache(sgp, sln_settings)
        return sln_settings
    xg_on = db.create_transaction_options(xg=True)
    sln_settings = db.run_in_transaction_options(xg_on, trans)
    broadcast_updates_pending(sln_settings)
    send_message(service_user, u"solutions.common.group_purchase.update", service_identity=service_identity)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, group_purchase_id=(int, long))
def delete_group_purchase(service_user, service_identity, group_purchase_id):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    def txn():
        sln_settings = get_solution_settings(service_user)
        m = SolutionGroupPurchase.get_by_id(group_purchase_id, parent_key_unsafe(service_identity_user, sln_settings.solution))
        azzert(service_user == m.service_user)
        m.deleted = True
        m.put()
    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, txn)

    send_message(service_user, u"solutions.common.group_purchase.update", service_identity=service_identity)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, group_purchase_id=(int, long), message=unicode)
def broadcast_group_purchase(service_user, service_identity, group_purchase_id, message):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    sln_settings = get_solution_settings(service_user)
    sgp = SolutionGroupPurchase.get_by_id(group_purchase_id, parent_key_unsafe(service_identity_user, sln_settings.solution))

    sln_main_branding = get_solution_main_branding(service_user)
    branding = sln_main_branding.branding_key if sln_main_branding else None

    members = dict()
    for e in sgp.subscriptions:
        if e.sender:
            member = MemberTO()
            member.alert_flags = Message.ALERT_FLAG_VIBRATE
            member.member = e.sender.email
            member.app_id = e.sender.app_id
            members["%s:%s" % (member.member, member.app_id)] = member

    if members:
        messaging.send(parent_key=None,
                       parent_message_key=None,
                       message=message,
                       answers=[],
                       flags=Message.FLAG_ALLOW_DISMISS,
                       members=members.values(),
                       branding=branding,
                       tag=None,
                       service_identity=service_identity)


@returns(SolutionGroupPurchase)
@arguments(service_user=users.User, service_identity=unicode, group_purchase_id=(int, long), name=unicode, user_detail=UserDetailsTO, units=int)
def new_group_purchase_subscription(service_user, service_identity, group_purchase_id, name, user_detail, units):
    from solutions.common.bizz.provisioning import populate_identity
    sln_settings = get_solution_settings(service_user)
    if not units > 0:
        raise BusinessException(translate(sln_settings.main_language, SOLUTION_COMMON, 'new-group-subscription-failure-required-at-least-1-unit'))
    main_branding = get_solution_main_branding(service_user)
    app_user = user_detail.toAppUser() if user_detail else None

    def trans():
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        sgp = SolutionGroupPurchase.get_by_id(group_purchase_id, parent_key_unsafe(service_identity_user, sln_settings.solution))
        units_user = 0
        if user_detail:
            for subscription in sgp.subscriptions_for_user(app_user):
                units_user += subscription.units
        if sgp.max_units_pp and units_user >= sgp.max_units_pp:
            raise BusinessException(translate(sln_settings.main_language, SOLUTION_COMMON,
                                              'new-group-subscription-failure-reached-maximum'))
        if sgp.max_units_pp and (units_user + units) > sgp.max_units_pp:
            raise BusinessException(translate(sln_settings.main_language, SOLUTION_COMMON,
                                              'new-group-subscription-failure-exceeded-maximum',
                                              max_units=sgp.max_units_pp - units_user))
        if (sgp.units_available - units) >= 0:
            sgpe = SolutionGroupPurchaseSubscription(parent=sgp)
            sgpe.sender = SolutionUser.fromTO(user_detail) if user_detail else None
            sgpe.name = name
            sgpe.units = units
            sgpe.timestamp = now()
            sgpe.app_user = app_user
            sgpe.put()

            units_user += units
        else:
            raise BusinessException(translate(sln_settings.main_language, SOLUTION_COMMON, 'new-group-subscription-failure-insufficient-units'))
        return sln_settings, sgp, units_user

    xg_on = db.create_transaction_options(xg=True)
    sln_settings, sgp, units_user = db.run_in_transaction_options(xg_on, trans)

    send_message(service_user, u"solutions.common.group_purchase.update", service_identity=service_identity)

    populate_identity(sln_settings, main_branding.branding_key, main_branding.branding_key)  # update service data
    system.publish_changes()

    if user_detail:
        user_data = json.loads(system.get_user_data(user_detail.email, ["groupPurchaseSubscriptions"], service_identity,
                                                    user_detail.app_id))
        if user_data["groupPurchaseSubscriptions"] is None:
            user_data["groupPurchaseSubscriptions"] = dict()

        user_data["groupPurchaseSubscriptions"][unicode(sgp.id)] = units_user
        system.put_user_data(user_detail.email, json.dumps(user_data), service_identity, user_detail.app_id)

    return sgp


def provision_group_purchase_branding(sln_group_purchase_settings, main_branding, language):
    if not sln_group_purchase_settings.branding_hash:
        logging.info("Storing GROUP PURCHASE branding")
        stream = ZipFile(StringIO(main_branding.blob))
        try:
            new_zip_stream = StringIO()
            zip_ = ZipFile(new_zip_stream, 'w', compression=ZIP_DEFLATED)
            try:
                path = os.path.join(os.path.dirname(solutions.__file__), 'common', 'templates', 'brandings/app_jquery.tmpl.js')
                zip_.writestr("jquery.tmpl.min.js", file_get_contents(path))
                path = os.path.join(os.path.dirname(solutions.__file__), 'common', 'templates', 'brandings/moment-with-locales.min.js')
                zip_.writestr("moment-with-locales.min.js", file_get_contents(path))
                zip_.writestr("app-translations.js", JINJA_ENVIRONMENT.get_template("brandings/app_group_purchases_translations.js").render({'language': language}).encode("utf-8"))
                path = os.path.join(os.path.dirname(solutions.__file__), 'common', 'templates', 'brandings/app_group_purchases.js')
                zip_.writestr("app.js", file_get_contents(path).encode("utf-8"))

                for file_name in set(stream.namelist()):
                    str_ = stream.read(file_name)
                    if file_name == 'branding.html':
                        html = str_
                        # Remove previously added dimensions:
                        html = re.sub("<meta\\s+property=\\\"rt:dimensions\\\"\\s+content=\\\"\\[\\d+,\\d+,\\d+,\\d+\\]\\\"\\s*/>", "", html)
                        html = re.sub('<head>', """<head>
<link href="jquery/jquery.mobile.inline-png-1.4.2.min.css" rel="stylesheet" media="screen">
<style type="text/css">
#group_purchases-empty{text-align: center;}
div.groupPurchase{padding: 10px 10px 25px 10px;}
img.groupPurchasePicture { width: 100%; margin-top: 10px; }
div.backgoundLight{background: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3gEYDyEEzIMX+AAAACZpVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVAgb24gYSBNYWOV5F9bAAAADUlEQVQI12NgYGCQBAAAHgAaOwrXiAAAAABJRU5ErkJggg==");}
div.backgoundDark{background: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3gEYDyIY868YdAAAACZpVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVAgb24gYSBNYWOV5F9bAAAADUlEQVQI12P4//+/JAAJFQMXEGL3cQAAAABJRU5ErkJggg==");}
h2.title { margin: 0;}
.subscribed { font-weight: bold; }
</style>
<script src="jquery/jquery-1.11.0.min.js"></script>
<script src="jquery/jquery.mobile-1.4.2.min.js"></script>
<script src="jquery.tmpl.min.js"></script>
<script src="moment-with-locales.min.js"></script>
<script src="rogerthat/rogerthat-1.0.js" type="text/javascript"></script>
<script src="rogerthat/rogerthat.api-1.0.js" type="text/javascript"></script>

<script src="app-translations.js" type="text/javascript"></script>
<script src="app.js" type="text/javascript"></script>""", html)
                        html = re.sub('<nuntiuz_message/>', """<div data-role="popup" id="gp-popup" class="ui-content">
    <a href="#" data-rel="back" data-role="button" data-theme="a" data-icon="delete" data-iconpos="notext" class="closePopupOverlay ui-btn-right">Close</a>
    <div id="gp-popup-content"></div>
</div>
<div id="menu"></div>""", html)
                        zip_.writestr('app.html', html)

                    else:
                        zip_.writestr(file_name, str_)
            finally:
                zip_.close()

            branding_content = new_zip_stream.getvalue()
            new_zip_stream.close()

            sln_group_purchase_settings.branding_hash = put_branding(u"Group Purchase App", base64.b64encode(branding_content)).id
            sln_group_purchase_settings.put()
        except:
            logging.error("Failure while parsing group purchase app branding", exc_info=1)
            raise
        finally:
            stream.close()


@returns(SendApiCallCallbackResultTO)
@arguments(service_user=users.User, email=unicode, method=unicode, params=unicode, tag=unicode, service_identity=unicode,
           user_details=[UserDetailsTO])
def solution_group_purchcase_purchase(service_user, email, method, params, tag, service_identity, user_details):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    jsondata = json.loads(params)

    group_purchase_id = int(jsondata['groupPurchaseId'])
    units = int(jsondata['units'])

    r = SendApiCallCallbackResultTO()
    sln_settings = get_solution_settings(service_user)
    try:
        sgp = new_group_purchase_subscription(service_user, service_identity, group_purchase_id, user_details[0].name, user_details[0], units)
        r.result = u"Successfully purchased %s units" % units
        r.error = None
        message = translate(sln_settings.main_language, SOLUTION_COMMON, 'group-subscription-successful-title',
                            units=units, title=sgp.title)
    except BusinessException, e:
        r.result = e.message
        r.error = None
        sgp = SolutionGroupPurchase.get_by_id(group_purchase_id, parent_key_unsafe(service_identity_user, sln_settings.solution))
        message = translate(sln_settings.main_language, SOLUTION_COMMON, 'group-subscription-failure-title-reason',
                            units=units, title=sgp.title, reason=e.message)
    except:
        logging.error("Failure when adding new group_purchase subscription", exc_info=1)
        r.result = None
        r.error = u"An unknown error occurred"
        sgp = SolutionGroupPurchase.get_by_id(group_purchase_id, parent_key_unsafe(service_identity_user, sln_settings.solution))
        message = translate(sln_settings.main_language, SOLUTION_COMMON, 'group-subscription-failure-unknown-title',
                            title=sgp.title)

    member = MemberTO()
    member.alert_flags = Message.ALERT_FLAG_VIBRATE
    member.member = user_details[0].email
    member.app_id = user_details[0].app_id

    main_branding = get_solution_main_branding(service_user)
    messaging.send(parent_key=None,
                   parent_message_key=None,
                   message=message,
                   answers=[],
                   flags=Message.FLAG_ALLOW_DISMISS,
                   members=[member],
                   branding=main_branding.branding_key,
                   tag=None,
                   service_identity=service_identity)
    return r
