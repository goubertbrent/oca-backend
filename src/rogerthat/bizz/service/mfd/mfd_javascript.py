# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

import base64
import json
import logging
import os

from google.appengine.ext.webapp import template

from mcfw.cache import cached
from mcfw.rpc import returns, arguments
from rogerthat.bizz.friend_helper import FriendHelper
from rogerthat.bizz.i18n import get_message_flow_strings, update_translation_of_type
from rogerthat.consts import MC_DASHBOARD
from rogerthat.models import Message, ServiceMenuDef, ServiceTranslation
from rogerthat.rpc import users
from rogerthat.templates.filter import mcjs
from rogerthat.to import WIDGET_MAPPING
from rogerthat.to.friends import FRIEND_TYPE_SERVICE

JS_MFR_CODE = None
JS_MFR_LIBRARIES = []

template.register_template_library('rogerthat.templates.filter')


def get_jsmfr_code():
    global JS_MFR_CODE
    if not JS_MFR_CODE:
        with open(os.path.join(os.path.dirname(__file__), 'js_mfr_code.js'), 'r') as f:
            JS_MFR_CODE = f.read()
    return JS_MFR_CODE


def get_jsmfr_libraries():
    global JS_MFR_LIBRARIES
    if not JS_MFR_LIBRARIES:
        for name, file_name, in [('sha256', 'sha256.js')]:
            with open(os.path.join(os.path.dirname(__file__), 'libraries', file_name), 'r') as f:
                JS_MFR_LIBRARIES.append((name, f.read()))
    return JS_MFR_LIBRARIES


def xpath_pick_first(obj, xpath_query):
    value = obj.xpath(xpath_query)
    if len(value) == 0:
        return None
    return value[0]


class dynobject(object):
    pass


def get_mfd_id(objid):
    return unicode(json.loads(base64.decodestring(objid[7:]))['mfd']) if objid.startswith('base64:') else None


def to_bool(s):
    if s is None:
        return None
    return s == 'true'


def to_float(s):
    if s is None:
        return None
    return float(s)


def to_long(s):
    if s is None:
        return None
    return long(s)


def to_unicode(s):
    if s is None:
        return None
    return unicode(s)


VIBRATION_ALERT_TYPES = {
    True: Message.ALERT_FLAG_VIBRATE,
    False: 0
}


ALERT_TYPES = {
    'BEEP': 0,
    'SILENT': Message.ALERT_FLAG_SILENT,
    'RING_5': Message.ALERT_FLAG_RING_5,
    'RING_15': Message.ALERT_FLAG_RING_15,
    'RING_30': Message.ALERT_FLAG_RING_30,
    'RING_60': Message.ALERT_FLAG_RING_60
}


ALERT_INTERVAL_TYPES = {
    'NONE': 0,
    'INTERVAL_5': Message.ALERT_FLAG_INTERVAL_5,
    'INTERVAL_15': Message.ALERT_FLAG_INTERVAL_15,
    'INTERVAL_30': Message.ALERT_FLAG_INTERVAL_30,
    'INTERVAL_60': Message.ALERT_FLAG_INTERVAL_60,
    'INTERVAL_300': Message.ALERT_FLAG_INTERVAL_300,
    'INTERVAL_900': Message.ALERT_FLAG_INTERVAL_900,
    'INTERVAL_3600': Message.ALERT_FLAG_INTERVAL_3600,
}


def to_alert_flags(vibrate, alert_type, alert_interval_type):
    return VIBRATION_ALERT_TYPES[vibrate] | ALERT_TYPES[alert_type] | ALERT_INTERVAL_TYPES[alert_interval_type]


def to_message_flags(allow_dismiss, auto_lock):
    flags = Message.FLAG_SENT_BY_JS_MFR
    if allow_dismiss:
        flags |= Message.FLAG_ALLOW_DISMISS
    if auto_lock:
        flags |= Message.FLAG_AUTO_LOCK
    return flags


@returns(dict)
@arguments(flow_xml=unicode)
def parse_flow_xml(flow_xml):
    logging.debug(flow_xml)

    # xml must be a <str> to be able to be parsed
    if isinstance(flow_xml, unicode):
        flow_xml = flow_xml.encode('utf-8')

    parsed_flows = dict()
    if 'messageFlowDefinitionSet' in flow_xml:
        from rogerthat.bizz.service.mfd import parse_message_flow_definition_set_xml
        mf_defs = parse_message_flow_definition_set_xml(flow_xml)
        for mf_def in mf_defs.definition:
            parsed_flows[to_unicode(mf_def.language)] = mf_def
    else:
        from rogerthat.bizz.service.mfd import parse_message_flow_definition_xml
        mf_def = parse_message_flow_definition_xml(flow_xml)
        parsed_flows[to_unicode(mf_def.language)] = mf_def

    return parsed_flows


def get_flow_code_translations(helper, flow_xml):
    # type: (FriendHelper, unicode) -> object
    if helper.service_user in (MC_DASHBOARD, None):
        return {
            'defaultLanguage': None,
            'values': {}
        }

    default_language = helper.get_service_profile().defaultLanguage
    translation_type = ServiceTranslation.MFLOW_JAVASCRIPT_CODE

    translation_keys = set()
    for keys in get_message_flow_strings(default_language, flow_xml).itervalues():
        translation_keys.update(keys)

    translation_dict = {}
    if translation_keys:
        # update with new keys and get the old if already exists
        translation_dict, _ = update_translation_of_type(helper.service_user, translation_type, translation_keys)

    return {
        'defaultLanguage': default_language,
        'values': translation_dict
    }


@returns(dict)
@arguments(helper=FriendHelper, flow_xml=unicode, context=unicode, parent_message_key=unicode, must_validate=bool)
def _render_flow_definitions(helper, flow_xml, context=None, parent_message_key=None, must_validate=False):
    # type: (FriendHelper, unicode, unicode, unicode, bool) -> dict
    output = {}
    for lang, mf_def in parse_flow_xml(flow_xml).iteritems():
        if must_validate:
            from rogerthat.bizz.service.mfd import validate_message_flow_definition
            validate_message_flow_definition(mf_def, helper.service_user, True)

        current_dir = os.path.dirname(__file__)
        tmpl = os.path.join(current_dir, 'mfr_template.tmpl')
        branding_hashes = set()
        attachemnt_urls = set()
        for m in (mf_def.message + mf_def.formMessage):
            if m.brandingKey:
                branding_hashes.add(to_unicode(m.brandingKey))
            for a in m.attachment:
                attachemnt_urls.add(to_unicode(a.url))

            for btn in getattr(m, 'answer', list()):
                if btn.action and btn.action.startswith('smi://'):
                    btn.action = 'smi://' + ServiceMenuDef.hash_tag(btn.action[6:])
                if btn.color and len(btn.color) == 3:
                    btn.color = btn.color[0] * 2 + btn.color[1] * 2 + btn.color[2] * 2

        translations = json.dumps(get_flow_code_translations(helper, flow_xml))

        js_libs = u''
        excluded_libs = ['sha256']
        for flow_code in mf_def.flowCode:
            if 'smi://' in flow_code.javascriptCode.valueOf_:
                excluded_libs.remove('sha256')
                break

        for lib_name, lib in get_jsmfr_libraries():
            if lib_name in excluded_libs:
                continue
            js_libs = '%s\n%s' % (js_libs, lib)

        output[lang] = (template.render(tmpl, dict(f=mf_def,
                                                   libs=js_libs,
                                                   context=context,
                                                   parent_message_key=parent_message_key,
                                                   WIDGET_MAPPING=WIDGET_MAPPING,
                                                   translations=translations)),
                        list(branding_hashes),
                        list(attachemnt_urls))
    return output


def _get_js_mfr_code(js_def, minify=True):
    if minify:
        import slimit
        return slimit.minify(get_jsmfr_code() + js_def, mangle=True, mangle_toplevel=False)  # @UndefinedVariable
    else:
        return get_jsmfr_code() + js_def


@returns(dict)
@arguments(helper=FriendHelper, flow_xml=unicode, context=unicode, minify=bool, parent_message_key=unicode,
           must_validate=bool)
def generate_js_flow(helper, flow_xml, context=None, minify=False, parent_message_key=None, must_validate=False):
    # type: (FriendHelper, unicode, unicode, bool, unicode, bool) -> dict[str, list[str, list[str], list[str]]]
    output = dict()
    logging.info('Generating js flow')
    tmpl = os.path.join(os.path.dirname(__file__), 'static_flow.html.tmpl')
    for lang, (js_def, brandings, attachment_urls) \
            in _render_flow_definitions(helper, flow_xml, context, parent_message_key, must_validate).iteritems():
        js_mfr_code = _get_js_mfr_code(js_def, minify)
        output[lang] = [template.render(tmpl, {'js_mfr_code': js_mfr_code}), brandings, attachment_urls]
    return output


@cached(1, lifetime=0, request=False, memcache=True, datastore='_generate_js_flow_cached')
@returns(dict)
@arguments(service_user=users.User, flow_xml=unicode, context=unicode, minify=bool, parent_message_key=unicode,
           must_validate=bool)
def _generate_js_flow_cached(service_user, flow_xml, context, minify, parent_message_key, must_validate):
    # type: (users.User, unicode, unicode, bool, unicode, bool) -> dict[str, list[str, list[str], list[str]]]
    helper = FriendHelper.from_data_store(service_user, FRIEND_TYPE_SERVICE)
    return generate_js_flow(helper, flow_xml, context, minify, parent_message_key, must_validate)


def generate_js_flow_cached(service_user, xml, context, minify, parent_message_key, must_validate):
    # TODO properly fix (these flows should be generated in advance), this is just bandaid to improve performance
    # This is for the case where a poke returns a flow
    fake_context = '~context~'
    fake_key = '~parent_message_key~'
    output = _generate_js_flow_cached(service_user, xml, fake_context, minify, fake_key, must_validate)
    for lang in output:
        modified_output = output[lang][0].replace(mcjs(fake_context), mcjs(context))
        modified_output = modified_output.replace(mcjs(fake_key), mcjs(parent_message_key))
        output[lang][0] = modified_output
    return output
