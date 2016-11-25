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

import json
import uuid
from types import NoneType, FunctionType

from google.appengine.api import urlfetch
from google.appengine.ext import db

from mcfw.consts import MISSING
from mcfw.properties import azzert, object_factory
from mcfw.rpc import returns, arguments, serialize_complex_value
from rogerthat.bizz.service.mfr import MessageFlowNotFoundException
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.service.api import system, qr
from rogerthat.to.messaging.flow import FLOW_STEP_MAPPING
from rogerthat.to.messaging.service_callback_results import CallbackResultType, MessageCallbackResultTypeTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import bizz_check, channel
from rogerthat.utils.transactions import run_in_xg_transaction, on_trans_committed
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import broadcast_updates_pending, delete_file_blob, create_file_blob
from solutions.common.consts import UNIT_PIECE
from solutions.common.dal import get_solution_settings, get_restaurant_menu
from solutions.common.models import RestaurantMenu, SolutionSettings, SolutionMainBranding
from solutions.common.models.properties import MenuCategories, MenuCategory, MenuItem
from solutions.common.to import MenuTO


@returns()
@arguments(service_user=users.User, name=unicode)
def save_menu_name(service_user, name):
    name = name.strip()
    bizz_check(name, "Name can not be empty")

    def trans():
        sln_settings = get_solution_settings(service_user)
        sln_settings.updates_pending = True

        menu = get_restaurant_menu(service_user, sln_settings.solution)
        menu.name = name

        put_and_invalidate_cache(sln_settings, menu)

        return sln_settings

    xg_on = db.create_transaction_options(xg=True)
    sln_settings = db.run_in_transaction_options(xg_on, trans)

    channel.send_message(sln_settings.service_user, 'solutions.common.menu.name_updated', name=name)
    broadcast_updates_pending(sln_settings)


@returns(NoneType)
@arguments(service_user=users.User, menu=MenuTO)
def save_menu(service_user, menu):
    def trans():
        sln_settings = get_solution_settings(service_user)

        m = get_restaurant_menu(service_user, sln_settings.solution)
        if not m:
            m = RestaurantMenu(key=RestaurantMenu.create_key(service_user, sln_settings.solution))
        m.predescription = menu.predescription
        m.postdescription = menu.postdescription
        m.categories = MenuCategories()
        category_names = list()
        for c in menu.categories:
            if c.name in category_names:
                raise BusinessException(common_translate(sln_settings.main_language, SOLUTION_COMMON, "category_duplicate_name", name=c.name))
            if c.id == MISSING:
                c.id = str(uuid.uuid4()).decode('UTF-8')
            category_names.append(c.name)
            item_names = list()
            for i in c.items:
                if i.name in item_names:
                    raise BusinessException(common_translate(sln_settings.main_language, SOLUTION_COMMON, "product_duplicate_name", name=i.name))
                if i.id == MISSING:
                    i.id = str(uuid.uuid4()).decode('UTF-8')
                item_names.append(i.name)
            m.categories.add(c)

        sln_settings.updates_pending = True
        put_and_invalidate_cache(m, sln_settings)
        return sln_settings

    xg_on = db.create_transaction_options(xg=True)
    sln_settings = db.run_in_transaction_options(xg_on, trans)
    broadcast_updates_pending(sln_settings)


@returns(RestaurantMenu)
@arguments(service_user=users.User, translate=FunctionType, solution=unicode)
def _put_default_menu(service_user, translate=None, solution=None):
    if not translate:
        languages_to = system.get_languages()
        default_lang = languages_to.default_language
        translate = lambda name: common_translate(default_lang, SOLUTION_COMMON, name)

    if not solution:
        solution = get_solution_settings(service_user).solution

    menu = RestaurantMenu(key=RestaurantMenu.create_key(service_user, solution))
    menu.predescription = translate('prediscription') + " " + translate('your-menu')
    menu.postdescription = translate('postdiscription') + " " + translate('your-menu')
    menu.categories = MenuCategories()

    drinks = MenuCategory()
    drinks.name = translate('drinks')
    drinks.items = []
    drinks.index = 0
    drinks.predescription = translate('prediscription') + " " + translate('drinks')
    drinks.postdescription = translate('postdiscription') + " " + translate('drinks')
    drinks.id = str(uuid.uuid4()).decode('UTF-8')
    for i in range(3):
        drink = MenuItem()
        drink.name = translate('drink%d' % i)
        drink.price = 180
        drink.has_price = True
        drink.description = None
        drink.step = 1
        drink.unit = UNIT_PIECE
        drink.visible_in = MenuItem.VISIBLE_IN_MENU | MenuItem.VISIBLE_IN_ORDER
        drink.image_id = -1
        drink.qr_url = None
        drink.id = str(uuid.uuid4()).decode('UTF-8')
        drinks.items.append(drink)
    menu.categories.add(drinks)

    starters = MenuCategory()
    starters.name = translate('starters')
    starters.items = []
    starters.index = 1
    starters.predescription = translate('prediscription') + " " + translate('starters')
    starters.postdescription = translate('postdiscription') + " " + translate('starters')
    starters.id = str(uuid.uuid4()).decode('UTF-8')
    for i in range(3):
        starter = MenuItem()
        starter.name = translate('starter%d' % i)
        starter.price = 695
        starter.has_price = True
        starter.description = translate('starter%d-desc' % i)
        starter.step = 1
        starter.unit = UNIT_PIECE
        starter.visible_in = MenuItem.VISIBLE_IN_MENU | MenuItem.VISIBLE_IN_ORDER
        starter.image_id = -1
        starter.qr_url = None
        starter.id = str(uuid.uuid4()).decode('UTF-8')
        starters.items.append(starter)
    menu.categories.add(starters)

    main_courses = MenuCategory()
    main_courses.name = translate('main-courses')
    main_courses.items = []
    main_courses.index = 2
    main_courses.predescription = translate('prediscription') + " " + translate('main-courses')
    main_courses.postdescription = translate('postdiscription') + " " + translate('main-courses')
    main_courses.id = str(uuid.uuid4()).decode('UTF-8')
    menu.categories.add(main_courses)

    menu.put()
    return menu


@returns(unicode)
@arguments(service_user=users.User, category_index=(int, long), item_index=(int, long))
def get_menu_item_qr_url(service_user, category_index, item_index):
    from solutions.common.bizz.messaging import POKE_TAG_MENU_ITEM_IMAGE_UPLOAD
    from solutions.common.bizz.provisioning import put_menu_item_image_upload_flow
    menu = get_restaurant_menu(service_user)
    for category in menu.categories:
        if category.index == category_index:
            item = category.items[item_index]
            if item.qr_url:
                return item.qr_url

            qr_templates = qr.list_templates().templates
            qr_template_id = qr_templates[0].id if qr_templates else None
            tag = {u'__rt__.tag': POKE_TAG_MENU_ITEM_IMAGE_UPLOAD,
                   u'category_name': category.name,
                   u'item_name': item.name,
                   u'category_id': category.id,
                   u'item_id': item.id}

            def create_qr():
                return qr.create(common_translate(get_solution_settings(service_user).main_language,
                                                  SOLUTION_COMMON,
                                                  u'upload_menu_item_image',
                                                  item_name=item.name),
                                 json.dumps(tag), qr_template_id, flow=u'Upload image')

            try:
                qr_code = create_qr()
            except MessageFlowNotFoundException:
                sln_setting, main_branding = db.get([SolutionSettings.create_key(service_user),
                                                     SolutionMainBranding.create_key(service_user)])
                put_menu_item_image_upload_flow(main_branding.branding_key, sln_setting.main_language)
                qr_code = create_qr()

            item.qr_url = qr_code.image_uri
            menu.put()
            return item.qr_url
    azzert(False)


@returns(CallbackResultType)
@arguments(service_user=users.User, message_flow_run_id=unicode, member=unicode,
           steps=[object_factory("step_type", FLOW_STEP_MAPPING)], end_id=unicode, end_message_flow_id=unicode,
           parent_message_key=unicode, tag=unicode, result_key=unicode, flush_id=unicode, flush_message_flow_id=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def set_menu_item_image(service_user, message_flow_run_id, member, steps, end_id, end_message_flow_id,
                        parent_message_key, tag, result_key, flush_id, flush_message_flow_id, service_identity,
                        user_details):

    url = steps[-1].form_result.result.value
    azzert(url)

    tag_dict = json.loads(tag)
    category_name = tag_dict['category_name']
    item_name = tag_dict['item_name']
    category_id = tag_dict['category_id']
    item_id = tag_dict['item_id']

    def create_error(message):
        result = MessageCallbackResultTypeTO()
        result.message = message
        return result

    @db.non_transactional
    def download():
        response = urlfetch.fetch(url, follow_redirects=True)
        return response

    def trans():
        sln_settings = get_solution_settings(service_user)
        menu = get_restaurant_menu(service_user, sln_settings.solution)
        category = menu.categories[category_id]
        if not category:
            return create_error(common_translate(sln_settings.main_language, SOLUTION_COMMON, u'category_not_found',
                                                 name=category_name))
        for item in category.items:
            if item.id == item_id:
                break
        else:
            return create_error(common_translate(sln_settings.main_language, SOLUTION_COMMON, u'item_not_found',
                                                 name=item_name))

        if item.image_id:
            delete_file_blob(service_user, item.image_id)

        response = download()
        if response.status_code != 200:
            return create_error(common_translate(sln_settings.main_language, SOLUTION_COMMON,
                                                 u'error-occured-unknown-try-again'))

        item.image_id = create_file_blob(service_user, response.content).key().id()
        menu.put()
        on_trans_committed(channel.send_message, service_user, 'solutions.common.menu.item_image_configured',
                           category=serialize_complex_value(category, MenuCategory, False),
                           item=serialize_complex_value(item, MenuItem, False))
        return None

    return run_in_xg_transaction(trans)
