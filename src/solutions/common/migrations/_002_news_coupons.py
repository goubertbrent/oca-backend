# -*- coding: utf-8 -*-
# Copyright 2019 GIG Technology NV
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
# @@license_version:1.4@@

from google.appengine.ext import db, ndb

from rogerthat.models import KeyValueProperty
from rogerthat.models.properties.keyvalue import KVBlobBucket
from rogerthat.rpc import users
from rogerthat.utils.transactions import run_in_transaction
from solutions.common.models.news import NewsCoupon, RedeemedBy


class OldNewsCoupon(db.Expando):
    news_id = db.IntegerProperty()
    content = db.StringProperty(indexed=False)  # Copy of NewsItem.qr_code_caption
    redeemed_by = KeyValueProperty()

    @classmethod
    def kind(cls):
        return 'NewsCoupon'


def migrate(dry_run=True):
    coupons = OldNewsCoupon.all().fetch(None)

    to_put = []
    to_delete = []

    def trans():
        for coupon in coupons:
            if coupon.redeemed_by:
                redeemed_by = coupon.redeemed_by.to_json_dict().get('users', [])
            else:
                redeemed_by = []
            mail = coupon.key().parent().name()
            if not mail:
                raise Exception('fuck')
            to_put.append(NewsCoupon(key=NewsCoupon.create_key(coupon.key().id(), users.User(mail)),
                                     news_id=coupon.news_id,
                                     content=coupon.content,
                                     redeemed_by=[RedeemedBy(user=r['user'], redeemed_on=r['redeemed_on']) for r in
                                                  redeemed_by]))
            for blob_bucket_ids in coupon.redeemed_by._blob_keys.itervalues():
                to_delete.extend([KVBlobBucket.create_key(i, coupon.redeemed_by._ancestor) for i in blob_bucket_ids])

    run_in_transaction(trans, xg=True)
    if dry_run:
        return {'put': to_put, 'del': to_delete}

    ndb.put_multi(to_put)
    db.delete(to_delete)
