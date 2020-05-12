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

import random

from mcfw.cache import cached
from mcfw.rpc import arguments, returns
from ..threefold.api import _get_public_transaction, _get_timestamp_from_block


@returns(dict)
@arguments(transaction_id=unicode)
def get_public_transaction(transaction_id):
    base_url = _get_explorer_url()
    return _get_public_transaction(base_url, transaction_id)


def _get_explorer_url():
    urls = [u'https://explorer.testnet.threefoldtoken.com', u'https://explorer2.testnet.threefoldtoken.com']
    return random.choice(urls)


@cached(1, lifetime=86400 * 7)
@returns(long)
@arguments(block_id=long)
def get_timestamp_from_block(block_id):
    # type: (long) -> long
    base_url = _get_explorer_url()
    return _get_timestamp_from_block(base_url, block_id)
