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
import time

def _safe(f, *args, **kwargs):
    try:
        return f(*args, **kwargs)
    except:
        try:
            logging.exception("Caught exception while cleaning context")
        except:
            try:
                logging.critical("Could not log exception while cleaning context", _suppress=False)
            except:
                pass  # we give up


def _log_time_elapsed(start, path):
    if path and path not in ('/_ah/queue/deferred', '/_ah/warmup', '/cron/rpc/cleanup') and not path.startswith('/mapreduce'):
        elapsed = time.time() - start
        if elapsed > 5:
            logging.warning("Request took %s seconds!" % elapsed)


def run_in_context(f, *args, **kwargs):
    from common.setup_functions import reset_suppressing
    path = kwargs.pop('_path', None)
    start = time.time()

    reset_suppressing()
    try:
        return f(*args, **kwargs)
    finally:
        _safe(_log_time_elapsed, start, path)
        _safe(reset_suppressing)