# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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
# @@license_version:1.3@@

from google.appengine.ext import db
from google.appengine.ext.deferred import deferred

from rogerthat.consts import MIGRATION_QUEUE
from mcfw.utils import chunks
from shop.models import Charge


def job():
    deferred.defer(put_charges, _queue=MIGRATION_QUEUE)


def put_charges():
    all_charges = list(Charge.all())
    for charges in chunks(all_charges, 200):
        db.put(charges)
