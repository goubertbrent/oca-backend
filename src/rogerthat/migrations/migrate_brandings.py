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

import logging

import cloudstorage
from google.appengine.ext import db, blobstore
from rogerthat.bizz.branding import get_branding_cloudstorage_path
from rogerthat.bizz.job import run_job
from rogerthat.models import Branding


def migrate():
    run_job(_get_all_brandings, [], _move_to_cloudstorage, [])

def cleanup():
    run_job(_get_all_brandings, [], _clear_branding, [])


def _get_all_brandings():
    return Branding.all(keys_only=True)


def _move_to_cloudstorage(b_key):
    def trans():
        b = db.get(b_key)
        if b.blob_key:
            return

        if not b.blob:
            logging.error("branding with key: '%s' does not have a blob" % b.hash, _suppress=False)
            return

        filename = get_branding_cloudstorage_path(b.hash, b.user)
        with cloudstorage.open(filename, 'w') as f:
            f.write(b.blob)

        blobstore_filename = '/gs' + filename
        blobstore_key = blobstore.create_gs_key(blobstore_filename)
        b.blob_key = blobstore_key.decode('utf-8')
        b.put()

    db.run_in_transaction(trans)


def _clear_branding(b_key):
    def trans():
        b = db.get(b_key)
        if not b.blob:
            return

        if not b.blob_key:
            logging.error("branding with key: '%s' does not have a blob_key" % b.hash, _suppress=False)
            return

        b.blob = None
        b.put()

    db.run_in_transaction(trans)
