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

import logging

from google.appengine.ext import db
from rogerthat.bizz.job import run_job
from rogerthat.utils.models import reconstruct_key


def _migrate_key(k):
    if isinstance(k, db.Key):
        return k

    db_key = db.Key(k)
    logging.info('Old key: %s', repr(db_key))
    new_key = reconstruct_key(db_key)
    return new_key


def _qry(cls, keys_only=False):
    return cls.all(keys_only=keys_only)


def _worker(model_or_key, props, dry_run):
    if isinstance(model_or_key, db.Key):
        model = db.get(model_or_key)
    else:
        model = model_or_key

    for prop in props:
        try:
            k = getattr(model, prop)
        except AttributeError:
            if prop == 'voucher_key':
                return
            raise

        if not k:
            continue
        
        if isinstance(k, list):
            new_keys = map(_migrate_key, k)
            setattr(model, prop, map(str, new_keys))
            logging.info('Setting %s.%s to %s', model.kind(), prop, map(repr, new_keys))
        else:
            new_key = _migrate_key(k)
            setattr(model, prop, str(new_key))
            logging.info('Setting %s.%s to %s', model.kind(), prop, repr(new_key))

    if not dry_run:
        db.run_in_transaction(model.put)


def job(cls, properties, dry_run=True, keys_only=True):
    run_job(_qry, [cls, keys_only], _worker, [properties, dry_run], worker_queue='dataswitch-queue')
