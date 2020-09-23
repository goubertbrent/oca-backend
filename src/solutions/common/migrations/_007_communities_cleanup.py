# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
# @@license_version:1.5@@
from google.appengine.ext import ndb, db

from rogerthat.models import App
from rogerthat.models.news import NewsStream
from rogerthat.utils.models import delete_all_models_by_query
from solutions.common.models import SolutionSettings
from solutions.common.models.cityapp import CityAppProfile


# Only run scripts in here *after* running everything in 006_communities


class AssociationStatistic(ndb.Model):
    pass


class SolutionCityVoucherSettings(ndb.Model):
    pass


class SolutionCityVoucherTransaction(ndb.Model):
    pass


class SolutionCityVoucherRedeemTransaction(ndb.Model):
    pass


class SolutionCityVoucher(ndb.Model):
    pass


class SolutionCityVoucherQRCodeExport(ndb.Model):
    pass


class SolutionCityVoucherExport(ndb.Model):
    pass


class SolutionCityVoucherExportMerchant(ndb.Model):
    pass


class ProspectInteractions(ndb.Model):
    pass


def _1_news_streams(dry_run=True):
    keys = [NewsStream.create_key(key.name()) for key in App.all(keys_only=True)]
    if dry_run:
        return keys
    ndb.delete_multi(keys)


def _2_cityapp_profiles(dry_run=True):
    keys = CityAppProfile.query().fetch(keys_only=True)
    if not dry_run:
        ndb.delete_multi(keys)
    return len(keys)


def _4_cleanup_city_vouchers(dry_run=True):
    module_name = 'city_vouchers'
    to_put = []
    for settings in SolutionSettings.all().filter('modules', module_name):
        settings.modules.remove(module_name)
        to_put.append(settings)
    if not dry_run:
        db.put(to_put)
    return len(to_put)


def _3_remove_unused_models():
    models = [AssociationStatistic, SolutionCityVoucherSettings, SolutionCityVoucherTransaction,
              SolutionCityVoucherRedeemTransaction, SolutionCityVoucher, SolutionCityVoucherQRCodeExport,
              SolutionCityVoucherExport, SolutionCityVoucherExportMerchant, ProspectInteractions]
    for model in models:
        delete_all_models_by_query(model.query())
