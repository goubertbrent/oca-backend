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

from google.appengine.ext import db, ndb
from google.appengine.ext.ndb.query import QueryOptions

from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.consts import MIGRATION_QUEUE


def job(cls, namespace=None, batch_size=50):
    if issubclass(cls, db.Model):
        run_job(_qry_db, [cls, namespace], _worker_db, [], worker_queue=MIGRATION_QUEUE, mode=MODE_BATCH,
                batch_size=batch_size)
    elif issubclass(cls, ndb.Model):
        run_job(_qry_ndb, [cls, namespace], _worker_ndb, [], worker_queue=MIGRATION_QUEUE, mode=MODE_BATCH,
                batch_size=batch_size)


def _qry_db(cls, namespace=None):
    return cls.all(keys_only=True,
                   namespace=namespace)


def _worker_db(keys):
    db.delete(db.get(keys))


def _qry_ndb(cls, namespace=None):
    return cls.query(default_options=QueryOptions(keys_only=True),
                     namespace=namespace)


def _worker_ndb(keys):
    ndb.delete_multi(keys)
