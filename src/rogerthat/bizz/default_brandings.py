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

import io
from cgi import FieldStorage
from zipfile import ZipFile

from google.appengine.ext import ndb

from mcfw.exceptions import HttpBadRequestException
from mcfw.rpc import arguments, returns
from rogerthat.bizz.branding import store_branding_zip
from rogerthat.consts import MAX_BRANDING_SIZE
from rogerthat.exceptions.branding import DefaultBrandingRequiredException, DefaultBrandingNotFoundExcpetion
from rogerthat.models.apps import DefaultBranding


@returns([DefaultBranding])
@arguments(app_id=unicode)
def get_default_brandings(app_id):
    return [branding for branding in DefaultBranding.list_by_app_id(app_id) if not branding.is_default]


@returns(DefaultBranding)
@arguments(branding_type=unicode)
def get_global_default_branding(branding_type):
    """
    Args:
        branding_type (unicode)
    Returns:
        DefaultBranding
    """
    return DefaultBranding.default_key(branding_type).get()


@returns([DefaultBranding])
@arguments()
def get_all_default_brandings():
    return DefaultBranding.query()


@returns(DefaultBranding)
@arguments(branding_id=unicode)
def get_default_branding(branding_id):
    """
    Args:
        branding_id (unicode)
    Returns:
        DefaultBranding
    """
    try:
        branding_id = long(branding_id)
    except ValueError:
        # it is only a string in case it's a default branding, else it's a long
        pass
    branding = DefaultBranding.get_by_id(branding_id)
    if not branding:
        raise DefaultBrandingNotFoundExcpetion(branding_id)
    return branding


@returns(DefaultBranding)
@arguments(branding_type=unicode, uploaded_file=FieldStorage, default=bool, app_ids=[unicode], branding_id=unicode)
def save_default_branding(branding_type, uploaded_file, default, app_ids, branding_id=None):
    """
    Args:
        branding_type (unicode)
        uploaded_file (FieldStorage)
        default (bool)
        app_ids (list of unicode)
        branding_id (unicode)
    """
    if uploaded_file is not None:
        if not uploaded_file.type.startswith('application/zip'):
            raise HttpBadRequestException('only_zip_files_allowed')
        file_content = uploaded_file.value
        if len(file_content) > MAX_BRANDING_SIZE:
            raise HttpBadRequestException('file_too_large', {'size': '%s kB' % (MAX_BRANDING_SIZE / 1024)})
    elif not branding_id:
        raise HttpBadRequestException('please_select_a_file')
    if not default and not len(app_ids):
        raise HttpBadRequestException('one_or_more_apps_required')
    if branding_type not in DefaultBranding.TYPES:
        raise HttpBadRequestException('unknown_branding_type')
    to_put = []
    to_delete = []
    if default:
        default_key = DefaultBranding.default_key(branding_type)
        default_branding = default_key.get()
        if not default_branding:
            default_branding = DefaultBranding(key=default_key)
    else:
        if branding_id:
            default_branding = get_default_branding(branding_id)
            default_branding.app_ids = app_ids
        else:
            default_branding = DefaultBranding(app_ids=app_ids)
        for og_default_branding in DefaultBranding.get_by_app_ids(app_ids, branding_type):
            if og_default_branding.key != default_branding.key:
                og_default_branding.app_ids = [app_id for app_id in og_default_branding.app_ids if
                                               app_id not in app_ids]
                if og_default_branding.app_ids:
                    to_put.append(og_default_branding)
                else:
                    # Branding is not used by any app anymore so it can be deleted
                    to_delete.append(og_default_branding)
    if uploaded_file is not None:
        description = u'%s of %s' % (branding_type, app_ids) if not default else u'Default %s branding' % branding_type
        bytesio = io.BytesIO(uploaded_file.value)
        zip_ = ZipFile(bytesio)
        branding = store_branding_zip(None, zip_, description)
        bytesio.close()
        zip_.close()
        default_branding.branding = branding.hash
    default_branding.branding_type = branding_type
    to_put.append(default_branding)
    ndb.put_multi(to_put)
    if to_delete:
        ndb.delete_multi(to_delete)
    return default_branding


@returns()
@arguments(app_id=unicode, branding_type=unicode)
def remove_default_branding(app_id, branding_type):
    default_branding = DefaultBranding.get_by_app_id(app_id, branding_type)  # type: DefaultBranding
    if not default_branding:
        return
    default_branding.app_ids = [a_id for a_id in default_branding.app_ids if a_id != app_id]
    if default_branding.app_ids:
        default_branding.put()
    else:
        default_branding.key.delete()


@returns()
@arguments(branding_id=unicode)
def remove_default_global_branding(branding_id):
    try:
        branding = get_default_branding(branding_id)
        if branding.is_default:
            raise DefaultBrandingRequiredException()
        branding.key.delete()
    except DefaultBrandingNotFoundExcpetion:
        return
