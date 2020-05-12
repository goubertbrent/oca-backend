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

from google.appengine.ext import db

from mcfw.cache import cached, get_cached_models, get_cached_model
from mcfw.rpc import returns, arguments
from rogerthat.models import App, AppSettings, AppTranslations
from rogerthat.rpc import users
from rogerthat.utils.app import get_app_id_from_app_user


@returns([App])
@arguments()
def get_all_apps():
    return App.all()


@returns([App])
@arguments()
def get_visible_apps():
    return App.all().filter("visible =", True)


@returns([App])
@arguments()
def get_extra_apps():
    return App.all().filter("demo =", False).filter("visible =", True)


@returns([App])
@arguments(app_types=[int], only_visible=bool)
def get_apps(app_types, only_visible=True):
    # type: (list[int], bool) -> list[App]
    qry = App.all().filter('type IN', app_types)
    if only_visible:
        qry.filter("visible =", True)
    return qry


@returns([App])
@arguments(app_type=int)
def get_apps_by_type(app_type):
    # type: (list[int]) -> list[App]
    qry = App.all(keys_only=True).filter('type', app_type)
    return get_apps_by_keys(qry.fetch(None))


@returns([App])
@arguments(app_keys=[db.Key])
def get_apps_by_keys(app_keys):
    # type: (list[db.Key]) -> list[App]
    return get_cached_models(app_keys)


@returns([App])
def get_apps_by_id(app_ids):
    # type: (list[unicode]) -> list[App]
    return get_cached_models([App.create_key(app_id) for app_id in app_ids])


@returns(App)
@arguments(app_id=unicode)
def get_app_by_id(app_id):
    # type: (unicode) -> App
    return get_cached_model(App.create_key(app_id))


@cached(1, request=True, memcache=False)
@returns(AppTranslations)
@arguments(app_id=unicode)
def get_app_translations(app_id):
    return AppTranslations.get_by_app_id(app_id)


@returns(unicode)
@arguments(app_id=unicode)
def get_app_name_by_id(app_id):
    return get_app_by_id(app_id).name


@returns(App)
@arguments(app_user=users.User)
def get_app_by_user(app_user):
    app_id = get_app_id_from_app_user(app_user)
    return get_app_by_id(app_id)


@cached(1, 86400, read_cache_in_transaction=True)
@returns(App)
@arguments()
def get_default_app():
    @db.non_transactional
    def f():
        return App.all().filter('is_default =', True).get()
    return f()


@cached(1, lifetime=86400, read_cache_in_transaction=True)
@returns(AppSettings)
@arguments(app_id=unicode)
def get_app_settings(app_id):
    return AppSettings.get(AppSettings.create_key(app_id))
