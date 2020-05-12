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

import json

from mcfw.properties import azzert


def construct_push_notification(key, args, sound, smaller_args, **kwargs):
    r = {'aps': {'content-available': 1, 'badge': 1, 'alert': {'loc-key': key, 'loc-args': args}}}
    if sound:
        r['aps']['sound'] = sound
    r.update(kwargs)
    payload = json.dumps(r)
    while len(payload) > 2048:
        payload_size = len(payload)
        args = smaller_args(args, len(payload) - 2048)
        r['aps']['alert']['loc-args'] = args
        payload = json.dumps(r)
        if len(payload) >= payload_size:
            raise ValueError("Unable to squash payload.")
    return payload


def construct_unlocalized_push_notification(title, body, **kwargs):
    r = {'aps': {'content-available': 1, 'badge': 1, 'alert': {'title': title, 'body': body}}}
    r.update(kwargs)
    payload = json.dumps(r)
    azzert(len(payload) < 4096)
    return payload
