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

import sys

from google.appengine.api import users as gusers
from google.appengine.ext import db

from rogerthat.rpc import users
from rogerthat.rpc.rpc import rpc_items
from rogerthat.utils import now
from shop.models import AuditLog


@db.non_transactional
def audit_log(customer_id, message, variables=None, user=None, prospect_id=None):
    al = AuditLog()
    al.customer_id = customer_id
    al.prospect_id = prospect_id
    al.date = now()
    if user:
        al.user = user
    else:
        al.user = gusers.get_current_user() or users.get_current_user()
    al.message = message
    if variables:
        al.variables = variables
    else:
        al.variables = dict_str_for_audit_log(sys._getframe(2).f_locals)
    rpc_items.append(db.put_async(al), audit_log, customer_id, message, al.variables, al.user, al.prospect_id)


def dict_str_for_audit_log(variables_dict):
    return u"\n".join((u"%s=%s" % (var, value) for var, value in variables_dict.iteritems()))
