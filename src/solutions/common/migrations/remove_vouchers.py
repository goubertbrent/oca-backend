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

from rogerthat.utils.models import delete_all_models_by_query
from solutions.common.models import SolutionSettings


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


def cleanup_city_vouchers(dry_run=True):
    module_name = 'city_vouchers'
    to_put = []
    for settings in SolutionSettings.all().filter('modules', module_name):
        settings.modules.remove(module_name)
        to_put.append(settings)
    if not dry_run:
        db.put(to_put)
    return len(to_put)


def remove_unused_models():
    models = [SolutionCityVoucherSettings, SolutionCityVoucherTransaction,
              SolutionCityVoucherRedeemTransaction, SolutionCityVoucher, SolutionCityVoucherQRCodeExport,
              SolutionCityVoucherExport, SolutionCityVoucherExportMerchant]
    for model in models:
        delete_all_models_by_query(model.query())
