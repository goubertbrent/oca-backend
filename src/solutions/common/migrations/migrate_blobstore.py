# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

import datetime
import logging

import cloudstorage
from google.appengine.ext import db, blobstore
from google.appengine.ext.blobstore.blobstore import BlobInfo
from rogerthat.bizz.gcs import get_blobstore_cloudstorage_path
from rogerthat.bizz.job import run_job
from rogerthat.consts import ROGERTHAT_ATTACHMENTS_BUCKET, DEBUG
from shop.models import ShopLoyaltySlide, ShopLoyaltySlideNewOrder
from solutions.common.models.launcher import OSALauncherApp
from solutions.common.models.loyalty import SolutionLoyaltySlide


def migrate_blobstore():
    run_job(_get_all_blob_info, [], _move_to_gcs, [])

def migrate_shop_loyalty_apps():
    run_job(_get_all_shop_loyalty_apps, [], _move_shop_loyalty_app_to_cloudstorage, [])

def migrate_shop_loyalty_slides():
    run_job(_get_all_shop_loyalty_slides, [], _move_shop_loyalty_slides_to_cloudstorage, [])

def migrate_shop_loyalty_new_order_slides():
    run_job(_get_all_shop_loyalty_new_order_slides, [], _move_shop_loyalty_new_order_slides_to_cloudstorage, [])

def migrate_loyalty_slides():
    run_job(_get_all_loyalty_slides, [], _move_loyalty_slides_to_cloudstorage, [])


def _get_all_blob_info():
    return blobstore.BlobInfo.all()

def _get_all_shop_loyalty_apps():
    return OSALauncherApp.all(keys_only=True)

def _get_all_shop_loyalty_slides():
    return ShopLoyaltySlide.all(keys_only=True)

def _get_all_shop_loyalty_new_order_slides():
    return ShopLoyaltySlideNewOrder.all(keys_only=True)

def _get_all_loyalty_slides():
    return SolutionLoyaltySlide.all(keys_only=True)


def _move_to_gcs(blob_info):
    """
    Args:
        blob_info (BlobInfo)
    """
    blob_key = blob_info.key()
    if DEBUG and 'encoded_gs_file:' in str(blob_key):
        logging.debug('Skipping file %s because it is already in the cloud storage', blob_key)
        return
    filename = get_blobstore_cloudstorage_path(blob_key)
    try:
        with cloudstorage.open(filename, 'w', blob_info.content_type) as f:
            blob_reader = blob_info.open()
            f.write(blob_reader.read())
    except Exception:
        logging.exception('Failed to move item %s to blobstore', blob_key, _suppress=False)


def _move_shop_loyalty_app_to_cloudstorage(la_key):
    la = db.get(la_key)
    if not la.package:
        return

    blob_info = BlobInfo.get(la.package.key())

    filename = '%s/oca/launcher/apps/%s.apk' % (ROGERTHAT_ATTACHMENTS_BUCKET, la.app_id)
    with cloudstorage.open(filename, 'w', blob_info.content_type) as f:
        blob_reader = blob_info.open()
        f.write(blob_reader.read())


def _move_shop_loyalty_slides_to_cloudstorage(ls_key):
    def trans():
        ls = db.get(ls_key)
        if ls.gcs_filename:
            return

        blob_key = ls.item.key()
        blob_info = BlobInfo.get(blob_key)

        date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        filename = '%s/oca/shop/loyalty/slides/%s_%s' % (ROGERTHAT_ATTACHMENTS_BUCKET, date, blob_key)
        with cloudstorage.open(filename, 'w', blob_info.content_type) as f:
            blob_reader = blob_info.open()
            f.write(blob_reader.read())

        ls.gcs_filename = filename
        ls.put()

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


def _move_shop_loyalty_new_order_slides_to_cloudstorage(ls_key):
    def trans():
        ls = db.get(ls_key)
        if ls.gcs_filename:
            return

        blob_key = ls.item.key()
        blob_info = BlobInfo.get(blob_key)

        date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        filename = '%s/oca/shop/loyalty/new_order_slides/%s_%s' % (ROGERTHAT_ATTACHMENTS_BUCKET, date, blob_key)
        with cloudstorage.open(filename, 'w', blob_info.content_type) as f:
            blob_reader = blob_info.open()
            f.write(blob_reader.read())

        ls.gcs_filename = filename
        ls.put()

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


def _move_loyalty_slides_to_cloudstorage(ls_key):
    def trans():
        ls = db.get(ls_key)
        if ls.gcs_filename:
            return

        blob_key = ls.item.key()
        blob_info = BlobInfo.get(blob_key)

        date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        filename = '%s/oca/loyalty_slides/%s_%s' % (ROGERTHAT_ATTACHMENTS_BUCKET, date, blob_key)
        with cloudstorage.open(filename, 'w', blob_info.content_type) as f:
            blob_reader = blob_info.open()
            f.write(blob_reader.read())

        ls.gcs_filename = filename
        ls.put()

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)
