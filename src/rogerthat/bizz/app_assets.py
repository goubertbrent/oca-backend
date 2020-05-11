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

import uuid
from cgi import FieldStorage
from types import NoneType

from google.appengine.api import images
from google.appengine.api.blobstore import blobstore
from google.appengine.ext import ndb

from mcfw.rpc import returns, arguments
from rogerthat.bizz.gcs import upload_to_gcs
from rogerthat.bizz.job.update_app_asset import update_app_asset
from rogerthat.consts import GCS_BUCKET_PREFIX
from rogerthat.exceptions.app_assets import AppAssetNotFoundException, CannotDeleteDefaultAppAssetException
from rogerthat.models import App
from rogerthat.models.apps import AppAsset
from rogerthat.rpc.service import BusinessException
from rogerthat.to.app import AppAssetTO


@returns([AppAsset])
@arguments(app_id=unicode)
def get_app_assets(app_id):
    return [asset for asset in AppAsset.list_by_app_id(app_id) if not asset.is_default]


@returns([AppAsset])
@arguments()
def get_all_app_assets():
    return AppAsset.query()


@returns(AppAsset)
@arguments(asset_id=unicode)
def get_app_asset(asset_id):
    try:
        asset_id = long(asset_id)
    except ValueError:
        # it is only a string in case it's a default app asset, else it's a long
        pass
    return AppAsset.get_by_id(asset_id)


@returns(AppAsset)
@arguments(asset_type=unicode)
def get_default_app_asset(asset_type):
    """
    Args:
        asset_type (unicode)
    Returns:
        AppAsset
    """
    return AppAsset.default_key(asset_type).get()


def get_app_ids_without_custom_asset(asset_type):
    app_ids = set([key.name() for key in App.all(keys_only=True)])
    for asset in AppAsset.list_by_type(asset_type):
        for app_id in asset.app_ids:
            app_ids.remove(app_id)
    return app_ids


def remove_from_gcs(blob_key):
    blobstore.delete(blob_key)
    images.delete_serving_url(blob_key)


@returns(AppAsset)
@arguments(kind=unicode, uploaded_file=(FieldStorage, NoneType), default=bool, app_ids=[unicode], scale_x=float,
           asset_id=unicode)
def process_uploaded_assets(kind, uploaded_file, default, app_ids, scale_x, asset_id=None):
    """
    Args:
        kind (unicode)
        uploaded_file (FieldStorage)
        default (bool)
        app_ids (list of unicode)
        scale_x (float)
        asset_id (unicode)
    """
    if uploaded_file is not None:
        if not uploaded_file.type.startswith('image/'):
            raise BusinessException('only_images_allowed')
        file_content = uploaded_file.value
        if len(file_content) > AppAsset.MAX_SIZE:
            raise BusinessException('file_too_large')
    elif not asset_id:
        raise BusinessException('please_select_an_image')
    if not default and not len(app_ids):
        raise BusinessException('one_or_more_apps_required')
    if kind not in AppAsset.TYPES:
        raise BusinessException('unknown_asset_type')
    to_put = []
    to_delete = []
    if uploaded_file is not None:
        gcs_filename = '/%s-app-assets/%s-%s' % (GCS_BUCKET_PREFIX, kind, uuid.uuid4())
        content_type = uploaded_file.type
        blob_key = upload_to_gcs(file_content, content_type, gcs_filename)

    is_new_default = False
    modified_app_ids = set(app_ids)
    if default:
        default_key = AppAsset.default_key(kind)
        asset = default_key.get()
        if not asset:
            asset = AppAsset(id=default_key.id(), app_ids=[])
            is_new_default = True
        # get all apps that do not have a custom asset set
        modified_app_ids = get_app_ids_without_custom_asset(kind)
    else:
        if asset_id:
            asset = get_app_asset(asset_id)
            if not asset:
                raise AppAssetNotFoundException(asset_id)
            asset.app_ids = app_ids
        else:
            asset = AppAsset(app_ids=app_ids)
        for original_asset in AppAsset.get_by_app_ids(app_ids, kind):
            for app_id in original_asset.app_ids:
                modified_app_ids.add(app_id)
            if original_asset.key != asset.key:
                original_asset.app_ids = [app_id for app_id in original_asset.app_ids if app_id not in app_ids]
                if original_asset.app_ids:
                    to_put.append(original_asset)
                else:
                    to_delete.append(original_asset)
    asset.asset_type = kind
    if uploaded_file is not None:
        if asset.content_key:
            remove_from_gcs(asset.content_key)
        asset.content_key = blob_key
        asset.serving_url = images.get_serving_url(blob_key)
        asset.content_type = content_type
    asset.scale_x = scale_x
    to_put.append(asset)
    ndb.put_multi(to_put)
    if to_delete:
        for asset_to_delete in to_delete:  # type: AppAsset
            remove_from_gcs(asset_to_delete.content_key)
            asset_to_delete.key.delete()
    if not is_new_default:
        for app_id in modified_app_ids:
            if app_id in asset.app_ids:
                app_asset_to = AppAssetTO(kind, asset.serving_url, scale_x)
            else:
                app_asset_to = AppAssetTO(kind, None, scale_x)
            update_app_asset(app_id, app_asset_to)
    return asset


def _update_default_app_asset(asset_type, app_ids):
    """
        send update to send default branding to phone, if it exists
    Args:
        asset_type (unicode)
        app_ids (list of unicode)
    """
    asset = get_default_app_asset(asset_type)
    if asset:
        app_asset_to = AppAssetTO(asset.asset_type, asset.serving_url, asset.scale_x)
    else:
        # This will remove the asset on the phones
        app_asset_to = AppAssetTO(asset.asset_type, None, 0.0)
    for app_id in app_ids:
        update_app_asset(app_id, app_asset_to)


@returns()
@arguments(app_id=unicode, asset_type=unicode)
def remove_app_asset(app_id, asset_type):
    asset = AppAsset.get_by_app_id(app_id, asset_type)
    if not asset:
        return
    asset.app_ids = [a_id for a_id in asset.app_ids if a_id != app_id]
    if asset.app_ids:
        asset.put()
    else:
        remove_from_gcs(asset.content_key)
        asset.key.delete()
    _update_default_app_asset(asset_type, [app_id])


@returns()
@arguments(asset_id=unicode)
def remove_global_app_asset(asset_id):
    asset = get_app_asset(asset_id)
    if not asset:
        return
    if asset.is_default:
        raise CannotDeleteDefaultAppAssetException()
    asset_type = asset.asset_type
    app_ids = asset.app_ids
    remove_from_gcs(asset.content_key)
    asset.key.delete()
    _update_default_app_asset(asset_type, app_ids)
