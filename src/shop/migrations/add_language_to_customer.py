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

from google.appengine.ext import db

from shop.constants import COUNTRY_DEFAULT_LANGUAGES
from shop.models import Customer


def job():
    customers = Customer.all()
    to_put = list()
    for c in customers:
        if not c.language:
            if not c.country:
                raise Exception('Customer %s has no country assigned' % c.name)
            c.language = COUNTRY_DEFAULT_LANGUAGES[c.country]
            to_put.append(c)
    db.put(to_put)
