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

from google.appengine.api import users
from google.appengine.ext import db, ndb

from common.mcfw.cache import CachedModelMixIn
from common.mcfw.properties import azzert
from common.mcfw.rpc import returns, arguments
from common.mcfw.utils import chunks
from common.utils import foreach


@returns(ndb.Key)
@arguments(user=users.User, solution=unicode, namespace=unicode)
def parent_ndb_key(user, solution=u'mc-tracker', namespace=None):
    azzert('/' not in user.email(), 'Cannot create parent_key (/) for %s' % user.email())
    return parent_ndb_key_unsafe(user, solution, namespace)


@returns(ndb.Key)
@arguments(user=users.User, solution=unicode, namespace=unicode)
def parent_ndb_key_unsafe(user, solution=u'mc-tracker', namespace=None):
    return ndb.Key(solution, user.email(), namespace=namespace)


@returns(db.Key)
@arguments(user=users.User, solution=unicode)
def parent_key(user, solution=u'mc-tracker'):
    azzert(user)
    azzert('/' not in user.email(), 'Cannot create parent_key (/) for %s' % user.email())
    return parent_key_unsafe(user, solution)


@returns(db.Key)
@arguments(user=users.User, solution=unicode)
def parent_key_unsafe(user, solution=u'mc-tracker'):
    return db.Key.from_path(solution, user.email())


@returns(db.Key)
@arguments()
def system_parent_key():
    return db.Key.from_path(u'mc-tracker', 'system')


def generator(iterator):
    return (o for o in iterator)


def put_and_invalidate_cache(*models):
    if models:
        db.put(models)
        foreach(lambda m: m.invalidateCache(), (m for m in models if isinstance(m, CachedModelMixIn)))


def put_in_chunks(to_put, is_ndb=False):
    if is_ndb:
        ndb.put_multi(to_put)
    else:
        for chunk in chunks(to_put, 200):
            db.put(chunk)
