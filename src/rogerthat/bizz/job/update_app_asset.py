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

from types import NoneType

from google.appengine.ext.deferred import deferred

from mcfw.rpc import returns, arguments
from rogerthat.bizz.job import run_job
from rogerthat.bizz.system import update_app_asset_response
from rogerthat.capi.system import updateAppAsset
from rogerthat.models import UserProfile
from rogerthat.rpc.rpc import logError
from rogerthat.to.app import AppAssetTO, UpdateAppAssetRequestTO


@returns(NoneType)
@arguments(app_id=unicode, asset=AppAssetTO)
def update_app_asset(app_id, asset):
    """
    Args:
        app_id (unicode)
        asset (AppAssetTO)
    """
    deferred.defer(_run_update_app_asset, app_id, asset)


def _run_update_app_asset(app_id, asset):
    """
    Args:
        app_id (unicode)
        asset (AppAssetTO)
    """
    request = UpdateAppAssetRequestTO(asset.kind, asset.url, asset.scale_x)
    run_job(_get_profile_keys, [app_id], _update_app_asset_for_user, [request])


def _get_profile_keys(app_id):
    return UserProfile.all(keys_only=True).filter('app_id', app_id)


def _update_app_asset_for_user(user_profile_key, request):
    """
    Args:
        user_profile_key (db.Key)
        request (UpdateAppAssetRequestTO)
    """
    user_profile = UserProfile.get(user_profile_key)
    updateAppAsset(update_app_asset_response, logError, user_profile.user, request=request)
