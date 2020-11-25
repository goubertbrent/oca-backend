# -*- coding: utf-8 -*-
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
# @@license_version:1.4@@
import logging
import traceback

from google.appengine.ext import ndb

from mcfw.utils import get_readable_key

traced_models = []


def should_log_line(line):
    """
    Filters out unhelpful lines in the stacktrace (such as type decorators) that can be left out without missing out.
    """
    blacklist = ['google_appengine', 'typechecked_', 'add_1_monkey_patches', 'db_hooks', 'threading.py']
    return all(word not in line for word in blacklist)


def _get_key(model):
    if any(isinstance(model, m) for m in traced_models):
        stack = traceback.format_stack()
        logging.debug(''.join([l for l in stack if should_log_line(l)]))
    if isinstance(model, ndb.Model):
        if model.key:
            return model.key
        return model._get_kind()
    else:
        return get_readable_key(model.key()) if model.has_key() else u'%s(id=<unsaved>)' % model.kind()


def put_hook(model):
    logging.debug('PUT %s', _get_key(model))


def after_get_hook(model):
    logging.debug('GET %s', _get_key(model))
