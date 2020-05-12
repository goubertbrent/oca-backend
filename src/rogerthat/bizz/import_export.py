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
import os
import re
import zipfile

from cloudstorage import RetryParams
import cloudstorage

from google.appengine.ext import db
from mcfw.rpc import arguments, returns, serialize_complex_value, parse_complex_value
from rogerthat.bizz.branding import get_branding_cloudstorage_path, replace_branding, validate_delete_branding
from rogerthat.bizz.roles import create_service_roles
from rogerthat.bizz.service import create_menu_item, ExportBrandingsException
from rogerthat.bizz.service.mfd import save_message_flow, save_message_flow_by_xml
from rogerthat.consts import DEBUG
from rogerthat.dal.mfd import get_service_message_flow_designs
from rogerthat.dal.profile import get_service_profile
from rogerthat.dal.service import get_service_identities
from rogerthat.exceptions.branding import BrandingInUseException
from rogerthat.models import Branding, ServiceRole
from rogerthat.models.utils import replace_name_in_key
from rogerthat.restapi.service_panel import get_menu
from rogerthat.rpc import users
from rogerthat.service.api.system import list_brandings, list_roles
from rogerthat.to.branding import BrandingTO, ReplacedBrandingsTO
from rogerthat.to.roles import RoleTO
from rogerthat.to.service import ExportMessageFlowDesignTO
from rogerthat.to.service_panel import WebServiceMenuTO
from rogerthat.utils.models import reconstruct_key
from rogerthat.utils.transactions import run_in_transaction


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


@arguments(service_user=users.User, service_identity=unicode)
def validate_export_service_data(service_user, service_identity):
    menu = get_menu(service_identity)
    message_flow_designs = list(get_service_message_flow_designs(service_user))
    _, brandings_with_same_name = _list_branding_for_export()
    # These brandings are brandings with the same name that aren't the most recently uploaded version.
    # This is not supported, so throw an error
    service_identities = get_service_identities(service_user)
    service_profile = get_service_profile(service_user)
    errors = []
    for branding_key in brandings_with_same_name:
        menu_items_with_old_branding = [item for item in menu.items if branding_key == item.screenBranding]
        try:
            validate_delete_branding(branding_key, message_flow_designs, service_identities,
                                     menu_items_with_old_branding, service_profile)
        except BrandingInUseException as e:
            msg = 'Branding %s - used by %s' % (e.fields['id'], e.fields['type'])
            if 'identifier' in e.fields:
                msg += ' %s' % e.fields['identifier']
            errors.append(msg)
    if errors:
        raise ExportBrandingsException(errors)


@returns()
@arguments(service_user=users.User, service_identity=unicode, result_path=unicode)
def export_service_data(service_user, service_identity, result_path):
    stream = StringIO()
    zip_file = zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED)

    with users.set_user(service_user):
        menu = get_menu(service_identity)
        message_flow_designs = get_service_message_flow_designs(service_user)
        brandings, _ = _list_branding_for_export()
        try:
            _export_brandings(zip_file, service_user, brandings)
            _export_message_flows(zip_file, map(ExportMessageFlowDesignTO.fromMessageFlowDesign, message_flow_designs))
            _export_roles(zip_file)
            _export_menu(zip_file, menu)
        finally:
            zip_file.close()
    stream.seek(0)
    with cloudstorage.open(result_path, 'w') as gcs_file:
        gcs_file.write(stream.getvalue())


def import_service_data(service_user, zip_file):
    zip_file = zipfile.ZipFile(StringIO(zip_file))
    brandings = []
    menu = None
    roles = []
    # list of tuples (branding_id, branding_content)
    branding_contents = []  # type: tuple(unicode, unicode)
    message_flows = []
    try:
        for file_name in set(zip_file.namelist()):
            if file_name == 'brandings.json':
                brandings = parse_complex_value(BrandingTO, json.loads(zip_file.read(file_name)), True)
            elif file_name == 'menu.json':
                menu = parse_complex_value(WebServiceMenuTO, json.loads(zip_file.read(file_name)), False)
            elif file_name == 'roles.json':
                roles = parse_complex_value(RoleTO, json.loads(zip_file.read(file_name)), True)  # type:list[RoleTO]
            elif '/' in file_name:
                folder = file_name.split('/')[0]
                if folder == 'message_flows':
                    message_flows.append(
                        parse_complex_value(ExportMessageFlowDesignTO, json.loads(zip_file.read(file_name)), False))
                elif folder == 'brandings':
                    branding_hash = file_name.split('/')[1].replace('.zip', '')
                    branding_contents.append((branding_hash, zip_file.read(file_name)))
    finally:
        zip_file.close()
    import_brandings_result = _import_brandings(service_user, brandings, branding_contents)
    _import_flows(service_user, message_flows, import_brandings_result)
    new_roles = _import_roles(service_user, roles)
    role_mapping = {}
    for old_role in roles:
        for new_role in new_roles:
            if old_role.name == new_role.name:
                role_mapping[old_role.id] = new_role.role_id
    if menu:
        _import_menu(service_user, menu, role_mapping)


def _list_branding_for_export():
    all_brandings = list_brandings()  # type: list[BrandingTO]
    brandings_dict = {}
    # Only export the most recent version of each branding with the same description.
    brandings_with_same_name = []
    for branding in all_brandings:
        if branding.description not in brandings_dict:
            brandings_dict[branding.description] = branding
        else:
            brandings_with_same_name.append(branding.id)
    return brandings_dict.values(), brandings_with_same_name


def _export_brandings(export_zip, service_user, brandings):
    # type: (zipfile.ZipFile) -> None
    export_zip.writestr('brandings.json', json.dumps(serialize_complex_value(brandings, BrandingTO, True)))
    to_delete = []
    for branding in brandings:
        logging.info('Exporting branding %s - %s', branding.description, branding.id)
        gcs_filename = get_branding_cloudstorage_path(branding.id, service_user)
        try:
            with cloudstorage.open(gcs_filename, 'r',
                                   retry_params=RetryParams(max_retries=1 if DEBUG else 6)) as gcs_file:
                zip_path = os.path.join('brandings', '%s.zip' % branding.id)
                old_zip_stream = StringIO()
                old_zip_stream.write(gcs_file.read())
                the_zip = zipfile.ZipFile(old_zip_stream, compression=zipfile.ZIP_DEFLATED)
                new_zip_stream = StringIO()
                with zipfile.ZipFile(new_zip_stream, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                    for f in the_zip.filelist:  # type: zipfile.ZipInfo
                        if f.filename == 'branding.html':
                            new_filename = Branding.TYPE_MAPPING[branding.type]
                            new_zip.writestr(new_filename, the_zip.read(f.filename))
                        else:
                            new_zip.writestr(f.filename, the_zip.read(f.filename))
                export_zip.writestr(zip_path, new_zip_stream.getvalue())
        except cloudstorage.NotFoundError:
            logging.error('file %s not found' % gcs_filename)
        except cloudstorage.ServerError as e:
            logging.exception('Error while getting branding from cloudstorage')
            if DEBUG and 'But got status 500' in e.message:
                to_delete.append(Branding.create_key(branding.id))
    if to_delete:
        logging.info('Deleting %s brandings that were not found', len(to_delete))
        db.delete(to_delete)


def _export_message_flows(zip_file, flows):
    # type: (zipfile.ZipFile, list[ExportMessageFlowDesignTO]) -> None
    for flow in flows:  # type: ExportMessageFlowDesignTO
        file_content = json.dumps(serialize_complex_value(flow, ExportMessageFlowDesignTO, False))
        zip_file.writestr(os.path.join('message_flows', '%s.json' % flow.name), file_content)


def _export_roles(zip_file):
    roles = list_roles()
    zip_file.writestr('roles.json', json.dumps(serialize_complex_value(roles, RoleTO, True)))


def _export_menu(zip_file, menu):
    zip_file.writestr('menu.json', json.dumps(serialize_complex_value(menu, WebServiceMenuTO, False)))


def _import_brandings(service_user, brandings, branding_contents):
    # type: (users.User, list[BrandingTO], list[tuple]) -> list[ReplacedBrandingsTO]
    logging.info('Importing %s brandings', len(brandings))
    result = []
    for branding_hash, branding_content in branding_contents:
        _brandings = filter(lambda b: b.id == branding_hash, brandings)
        if not _brandings:
            logging.warn('Not importing branding %s because it was not found in the brandings.json file', branding_hash)
            continue
        branding = _brandings[0]
        logging.debug('Importing branding %s - %s', branding_hash, branding.description)
        stringio = StringIO()
        stringio.write(branding_content)
        new_branding, original_branding_hashes = replace_branding(service_user, stringio, branding.description,
                                                                  skip_meta_file=True, only_replace_if_newer=True)
        if new_branding:
            to = ReplacedBrandingsTO(BrandingTO.from_model(new_branding), original_branding_hashes)
            result.append(to)
    return result


def _patch_keys_in_message_flow(service_user, message_flow):
    if message_flow.definition and "nmessage_flow" in message_flow.definition:
        definition = json.loads(message_flow.definition)
        for module in definition['modules']:
            if module['name'] == 'Message flow':
                old_key = db.Key(module['value']['nmessage_flow'])
                new_key = reconstruct_key(old_key)
                new_key = replace_name_in_key(new_key, new_key.parent().name(), service_user.email())
                module['value']['nmessage_flow'] = str(new_key)
                logging.debug('Patched %r to %r', old_key, new_key)
        message_flow.definition = json.dumps(definition).decode('utf-8')


def _import_flows(service_user, message_flows, replaced_brandings):
    # type: (users.User, list[ExportMessageFlowDesignTO], list[ReplacedBrandingsTO]) -> None
    logging.info('Importing %s flows', len(message_flows))

    # Flows with sub-flows need to be imported last
    message_flows.sort(key=lambda message_flow:
                       bool(message_flow.definition and "nmessage_flow" in message_flow.definition))

    for message_flow in message_flows:
        for replaced in replaced_brandings:
            if replaced.replaced_branding_hashes and message_flow.definition:
                branding_hash_re = re.compile('|'.join(replaced.replaced_branding_hashes))
                message_flow.definition = branding_hash_re.sub(replaced.new_branding.id, message_flow.definition)
        logging.debug('Importing flow %s', message_flow.name)
        _patch_keys_in_message_flow(service_user, message_flow)
        if message_flow.definition:
            is_last = message_flows[-1] == message_flow
            save_message_flow(service_user, message_flow.name, message_flow.definition, message_flow.language,
                              message_flow.validation_error is not None, message_flow.multilanguage,
                              send_updates=is_last)
        else:
            save_message_flow_by_xml(service_user, message_flow.xml, message_flow.multilanguage, False)


@returns([ServiceRole])
@arguments(service_user=users.User, roles=[RoleTO])
def _import_roles(service_user, roles):
    # type: (users.User, list[RoleTO]) -> list[ServiceRole]
    return run_in_transaction(create_service_roles, False, service_user, roles)


def _import_menu(service_user, menu, role_mapping):
    # type: (users.User, WebServiceMenuTO, dict[int, int]) -> None
    logging.info('Importing %s menu items', len([i for i in menu.items if not i.isBroadcastSettings]))
    for item in menu.items:
        if not item.isBroadcastSettings:
            logging.debug('Importing menu item %s', item.label)
            roles = [role_mapping[role] for role in item.roles]
            create_menu_item(service_user, item.iconName, item.iconColor, item.label, item.tag, item.coords,
                             item.screenBranding, item.staticFlowName, item.requiresWifi, item.runInBackground,
                             roles, item.isBroadcastSettings, None, item.action, item.link, item.fallThrough,
                             item.formId, item.embeddedApp)
