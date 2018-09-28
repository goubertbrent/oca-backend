# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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

import logging

from google.appengine.api import search
from google.appengine.ext import db

from mcfw.rpc import returns, arguments
from mcfw.utils import normalize_search_string
from rogerthat.bizz.job import run_job
from rogerthat.consts import HIGH_LOAD_WORKER_QUEUE
from rogerthat.rpc import users
from shop.dal import get_customer
from shop.models import Customer
from solutions.common.dal import get_solution_settings, \
    get_solution_settings_or_identity_settings

MERCHANTS_INDEX = 'MERCHANTS_INDEX'


def drop_index(the_index):
    while True:
        search_result = the_index.get_range(ids_only=True)
        ids = [r.doc_id for r in search_result.results]
        if not ids:
            break
        the_index.delete(ids)


def job(queue=HIGH_LOAD_WORKER_QUEUE):
    the_index = search.Index(name=MERCHANTS_INDEX)
    drop_index(the_index)
    run_job(query, [], worker, [], worker_queue=queue)


def worker(c_key):
    customer = db.get(c_key)
    if customer.service_disabled_at != 0:
        return
    if not customer.service_email:
        return
    re_index(customer.service_user)


def query():
    return Customer.all(keys_only=True)


@returns(search.Document)
@arguments(service_user=users.User)
def re_index(service_user):
    customer = get_customer(service_user)
    if not customer:
        return None
    if not customer.service_email:
        return None
    if customer.service_disabled_at != 0:
        return None
    service_user_email = service_user.email()

    the_index = search.Index(name=MERCHANTS_INDEX)
    the_index.delete([service_user_email])
    
    fields = [search.AtomField(name='merchant', value=service_user_email),
              search.TextField(name='customer_id', value=str(customer.id)),
              search.TextField(name='customer_user_email', value=customer.user_email),
              search.TextField(name='customer_name', value=customer.name),
              search.TextField(name='customer_address1', value=customer.address1),
              search.TextField(name='customer_address2', value=customer.address2),
              search.TextField(name='customer_zip_code', value=customer.zip_code),
              search.TextField(name='customer_app_ids', value=" ".join(customer.app_ids)),
              search.TextField(name='customer_website', value=customer.website),
              search.TextField(name='customer_facebook_page', value=customer.facebook_page),
              ]

    sln_settings = get_solution_settings(service_user)
    fields.append(search.TextField(name='sln_facebook_page', value=sln_settings.facebook_page))

    identities = [None]
    if sln_settings.identities:
        identities.extend(sln_settings.identities)
    for service_identity in identities:
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings,
                                                                    service_identity)
        if not sln_i_settings:
            continue

        fields.extend([search.TextField(name='slni_%s_name' % service_identity, value=sln_i_settings.name),
                       search.TextField(name='slni_%s_phone_number' % service_identity, value=sln_i_settings.phone_number),
                       search.TextField(name='slni_%s_qualified_identifier' % service_identity, value=sln_i_settings.qualified_identifier),
                       search.TextField(name='slni_%s_address' % service_identity, value=sln_i_settings.address)
                       ])

    m_doc = search.Document(doc_id=service_user_email, fields=fields)
    the_index.put(m_doc)

    return m_doc


def find_merchant(search_string):
    the_index = search.Index(name=MERCHANTS_INDEX)
    try:
        query_string = u"%s" % (normalize_search_string(search_string))
        query = search.Query(query_string=query_string,
                             options=search.QueryOptions(returned_fields=['merchant', 'customer_id', 'customer_name']))
        search_result = the_index.search(query)
        if search_result.results:
            return search_result.results
    except:
        logging.error('Search query error for search_string "%s"', search_string, exc_info=True)
    return None
