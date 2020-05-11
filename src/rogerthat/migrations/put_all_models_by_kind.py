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

from google.appengine.ext import db, ndb
from google.appengine.ext.ndb.query import QueryOptions

from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.utils.transactions import run_in_transaction


def job(cls):
    if issubclass(cls, db.Model):
        run_job(_qry_db, [cls], _worker_db, [], worker_queue=MIGRATION_QUEUE, mode=MODE_BATCH, batch_size=25)
    elif issubclass(cls, ndb.Model):
        run_job(_qry_ndb, [cls], _worker_ndb, [], worker_queue=MIGRATION_QUEUE, mode=MODE_BATCH, batch_size=25)


def _qry_db(cls):
    return cls.all(keys_only=True)


def _worker_db(keys):
    def trans():
        db.put(db.get(keys))

    run_in_transaction(trans, xg=True)


def _qry_ndb(cls):
    return cls.query(default_options=QueryOptions(keys_only=True))


@ndb.transactional(xg=True)
def _worker_ndb(keys):
    ndb.put_multi(ndb.get_multi(keys))
