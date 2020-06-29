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

import base64
from collections import defaultdict, OrderedDict
from functools import wraps
import hashlib
import logging
import os
import threading
import time
import types

from google.appengine.api import memcache as mod_memcache
from google.appengine.ext import db, ndb, deferred

from common.mcfw.consts import MISSING
from common.mcfw.serialization import serializer, s_bool, get_serializer, s_any, deserializer, get_deserializer, ds_bool, \
    ds_any, SerializedObjectOutOfDateException, get_list_serializer, List
from common.mcfw.utils import get_readable_key

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

CACHE_ATTR = u'cache_key'
CACHE_LOGGING = os.environ.get('SERVER_SOFTWARE', 'Development').startswith('Development')


class CachedModelMixIn(object):
    on_trans_committed = None

    def invalidateCache(self):
        raise NotImplementedError()

    def updateCache(self):
        pass

    def _trigger_invalidate_cache(self):
        def invalidate_cache():
            self.invalidateCache()
            logging.info("%s: Cache invalidated", self.__class__.__name__)

        if db.is_in_transaction() and self.on_trans_committed:
            self.updateCache()
            self.on_trans_committed(invalidate_cache)
        else:
            invalidate_cache()

    def put(self):
        super(CachedModelMixIn, self).put()
        self._trigger_invalidate_cache()

    def delete(self):
        if isinstance(self, ndb.Model):
            super(CachedModelMixIn, self).key.delete()
        else:
            super(CachedModelMixIn, self).delete()
        self._trigger_invalidate_cache()


class _TLocal(threading.local):

    def __init__(self):
        self.request_cache = dict()


_tlocal = _TLocal()
del _TLocal


def get_from_request_cache(key):
    return _tlocal.request_cache.get(key, MISSING)


def add_to_request_cache(key, success, value):
    _tlocal.request_cache[key] = (success, value)


def remove_from_request_cache(key):
    _tlocal.request_cache.pop(key, None)


def flush_request_cache():
    _tlocal.request_cache.clear()


def set_cache_key(wrapped, f):
    key = lambda: f.meta[CACHE_ATTR] if hasattr(f, 'meta') and CACHE_ATTR in f.meta else '%s.%s' % (
        f.__name__, f.__module__)
    if not hasattr(wrapped, 'meta'):
        wrapped.meta = {CACHE_ATTR: key()}
        return
    if CACHE_ATTR not in wrapped.meta:
        wrapped.meta[CACHE_ATTR] = key()


def ds_key(version, cache_key):
    return "%s-%s" % (version, hashlib.sha256(cache_key).hexdigest())


class DSCache(db.Model):
    creation_timestamp = db.IntegerProperty()
    description = db.StringProperty(indexed=False)
    value = db.BlobProperty()


def invalidate_cache(f, *args, **kwargs):
    f.invalidate_cache(*args, **kwargs)


cache_key_locks = defaultdict(lambda: threading.RLock())


def cached(version, lifetime=600, request=True, memcache=True, key=None, datastore=None,
           read_cache_in_transaction=False):
    """
    Caches the result of the decorated function and returns the cached version if it exists.

    @param version: Cache version, needs to bumped everytime the semantics
    @type version: integer
    @param lifetime: Number of seconds the cached entry remains in memcache after it was created.
    @type lifetime: int
    @param request: Whether it needs to be cached in memory for the current request processing.
    @type request: bool
    @param memcache: Whether it needs to be cached in memcache.
    @type memcache: bool
    @param key: Function to create cache_key
    @param key: function
    @param datastore: Content description of cache object in datastore. Leave none to ommit the datastore cache.
    @param datastore: str
    @param read_cache_in_transaction: bool Whether or not to read from the cache when the function is executed inside a transaction.
    @raise ValueError: if neither request nor memcache are True
    """

    if not request and not memcache and not datastore:
        raise ValueError("Either request or memcache or datastore needs to be True")

    if datastore and lifetime != 0:
        raise ValueError("If datastore caching is used, values other than 0 for lifetime are not permitted.")

    def wrap(f):
        base_cache_key = f.meta[CACHE_ATTR]
        if base_cache_key == 'inner_wrapper.google.appengine.api.datastore':
            raise ValueError('Move @db.non_transactional inside the @cached method')
        f_args = f.meta["fargs"]
        f_ret = f.meta["return_type"]
        f_pure_default_args_dict = f.meta["pure_default_args_dict"]

        if isinstance(f_ret, list):
            f_ret = List(f_ret[0])
        if memcache or datastore:
            result_serializer = get_serializer(f_ret)
            result_deserializer = get_deserializer(f_ret)
        key_function = key
        if not key_function:
            def key_(kwargs):
                stream = StringIO()
                stream.write(base_cache_key)
                kwargt = f.meta["kwarg_types"]
                for a in sorted(kwargt.keys()):
                    if a in kwargs:
                        effective_value = kwargs[a]
                    else:
                        effective_value = f_pure_default_args_dict[a]
                    if isinstance(kwargt[a], list):
                        get_list_serializer(get_serializer(kwargt[a][0]))(stream, effective_value)
                    else:
                        get_serializer(kwargt[a])(stream, effective_value)
                return stream.getvalue()

            key_function = key_

        @serializer
        def serialize_result(stream, obj):
            s_bool(stream, obj[0])
            if obj[0]:
                result_serializer(stream, obj[1])
            else:
                s_any(stream, obj[1])

        f.serializer = serialize_result

        @deserializer
        def deserialize_result(stream):
            success = ds_bool(stream)
            if success:
                result = result_deserializer(stream)
            else:
                result = ds_any(stream)
            return success, result

        f.deserializer = deserialize_result

        def cache_key(*args, **kwargs):
            kwargs_ = dict(kwargs)
            kwargs_.update(dict(((f_args[0][i], args[i]) for i in xrange(len(args)))))
            return "v%s.%s" % (version, base64.b64encode(key_function(kwargs_)))

        f.cache_key = cache_key

        def invalidate_cache(*args, **kwargs):
            ck = cache_key(*args, **kwargs)
            with cache_key_locks[ck]:
                if datastore:
                    @db.non_transactional
                    def clear_dscache():
                        db.delete(db.Key.from_path(DSCache.kind(), ds_key(version, ck)))

                    clear_dscache()
                if memcache:
                    attempt = 1
                    while not mod_memcache.delete(ck):  # @UndefinedVariable
                        if attempt >= 3:
                            logging.critical("MEMCACHE FAILURE !!! COULD NOT INVALIDATE CACHE !!!")
                            raise RuntimeError("Could not invalidate memcache!")
                        logging.debug("Memcache failure. Retrying to invalidate cache.")
                        time.sleep(0.25 * attempt)
                        attempt += 1

                if request and ck in _tlocal.request_cache:
                    del _tlocal.request_cache[ck]

        def update_cache(*args, **kwargs):
            # update request cache only
            if not request:
                return

            if '_data' not in kwargs:
                raise ValueError('update_cache() takes a mandatory _data argument')

            data = kwargs.pop('_data')
            ck = cache_key(*args, **kwargs)
            with cache_key_locks[ck]:
                _tlocal.request_cache[ck] = (True, data)

        f.invalidate_cache = invalidate_cache
        f.update_cache = update_cache

        @wraps(f)
        def wrapped(*args, **kwargs):
            ck = cache_key(*args, **kwargs)
            if not read_cache_in_transaction and db.is_in_transaction():
                _log('Ignoring cache: %s, key %s', f.__name__, ck)
                return f(*args, **kwargs)
            ck = cache_key(*args, **kwargs)
            with cache_key_locks[ck]:
                if request and ck in _tlocal.request_cache:
                    success, result = _tlocal.request_cache[ck]
                    if success:
                        _log('Hit(request): %s', f.__name__)
                        return result
                if memcache:
                    memcache_result = mod_memcache.get(ck)  # @UndefinedVariable
                    if memcache_result:
                        buf = StringIO(memcache_result)
                        try:
                            success, result = deserialize_result(buf)
                            if request:
                                _tlocal.request_cache[ck] = (success, result)
                            if success:
                                _log('Hit(memcache): %s', f.__name__)
                                return result
                        except SerializedObjectOutOfDateException:
                            pass
                if datastore:
                    @db.non_transactional
                    def get_from_dscache():
                        dscache = DSCache.get_by_key_name(ds_key(version, ck))
                        if dscache:
                            buf = StringIO(str(dscache.value))
                            try:
                                success, result = deserialize_result(buf)
                                if request:
                                    _tlocal.request_cache[ck] = (success, result)
                                if memcache:
                                    mod_memcache.set(ck, dscache.value, time=lifetime)  # @UndefinedVariable
                                if success:
                                    _log('Hit(ds): %s', f.__name__)
                                    return True, result
                            except SerializedObjectOutOfDateException:
                                pass
                        return False, None

                    cached, result = get_from_dscache()
                    if cached:
                        return result

                cache_value = None
                try:
                    result = f(*args, **kwargs)
                    if isinstance(result, types.GeneratorType):
                        result = list(result)
                    cache_value = (True, result)
                    return result
                except Exception as e:
                    cache_value = (False, e)
                    raise
                finally:
                    if cache_value and cache_value[0]:
                        # Only store in request cache in case we're inside a transaction to avoid stale results
                        if not db.is_in_transaction():
                            if datastore or memcache:
                                buf = StringIO()
                                serialize_result(buf, cache_value)
                                serialized_cache_value = buf.getvalue()
                            if datastore:
                                _log('Saving(ds): %s, key %s', f.__name__, ck)

                                @db.non_transactional
                                def update_dscache():
                                    dsm = DSCache(key_name=ds_key(version, ck))
                                    dsm.description = datastore
                                    dsm.creation_timestamp = int(time.time())
                                    dsm.value = db.Blob(serialized_cache_value)
                                    dsm.put()

                                update_dscache()
                            if memcache:
                                _log('Saving(memcache): %s, key %s', f.__name__, ck)
                                mod_memcache.set(ck, serialized_cache_value, time=lifetime)  # @UndefinedVariable
                        if request:
                            _log('Saving(request): %s, key %s', f.__name__, ck)
                            _tlocal.request_cache[ck] = cache_value

        return wrapped

    return wrap


def _log(msg, *args):
    if CACHE_LOGGING:
        logging.debug('[Cache] %s', msg % args)


def get_cached_model(model_key, cached_time=86400):
    # type: (db.Key, int) -> db.Model
    return get_cached_models([model_key], cached_time)[0]


def get_cached_models(model_keys, cached_time=86400):
    """
    Get models by their key from request cache, memcache or datastore.
    If the models weren't in either cache, they're cached in the request cache and memcache.
    The cache must be manually invalidated when the model is updated or deleted by calling invalidate_model_cache
    """
    # type: (list[db.Key], int) -> list[db.Model]
    results = {}  # type: dict[str, db.Model]
    cache_keys = OrderedDict()  # type: dict[str, db.Key]
    for key in model_keys:
        cache_keys[get_readable_key(key)] = key
    # First try request cache
    for cache_key, model_key in cache_keys.iteritems():
        result = get_from_request_cache(cache_key)
        if result is not MISSING:
            _log('Hit(request): %s', cache_key)
            results[cache_key] = result[1]
    # Try memcache & save results to request cache
    if len(results) != len(cache_keys):
        memcache_keys = [key for key in cache_keys if key not in results]
        memcache_result = mod_memcache.get_multi(memcache_keys)  # type: dict
        for cache_key, value in memcache_result.iteritems():
            model = ds_any(StringIO(value))
            results[cache_key] = model
            add_to_request_cache(cache_key, True, model)
            _log('Hit(memcache): %s', cache_key)
    # Not found in either request cache or memcache, fallback to datastore & save results to memcache and request cache
    if len(results) != len(cache_keys):
        ds_keys = [key for key in cache_keys if key not in results]
        ds_models = db.get([cache_keys[key] for key in ds_keys])
        for cache_key, model in zip(ds_keys, ds_models):
            if not model:
                continue
            add_to_request_cache(cache_key, True, model)
            results[cache_key] = model
            _log('Saving(all): %s', cache_key)
        mod_memcache.set_multi({key: _serialize_model(model) for key, model in zip(ds_keys, ds_models)}, cached_time)
    return [results.get(k) for k in cache_keys]  # Keep original order


def invalidate_model_cache(models_or_keys):
    if type(models_or_keys) is not list:
        models_or_keys = [models_or_keys]
    cache_keys = [get_readable_key(model.key() if isinstance(model, db.Model) else model) for model in models_or_keys]
    for cache_key in cache_keys:
        remove_from_request_cache(cache_key)
    if not mod_memcache.delete_multi(cache_keys):
        deferred.defer(mod_memcache.delete_multi, cache_keys)


def _serialize_model(model):
    stream = StringIO()
    s_any(stream, model)
    return stream.getvalue()
