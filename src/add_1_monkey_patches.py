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

import datetime
import json
import logging
import os
import pickle
import threading
import time
import urllib
import uuid
from functools import wraps

import google.appengine.api.users
import webapp2
from google.appengine.api import taskqueue
from google.appengine.api.datastore_errors import TransactionFailedError
from google.appengine.api.images.images_stub import ImagesServiceStub
from google.appengine.datastore.datastore_rpc import TransactionOptions, ConfigOption
from google.appengine.ext import db, deferred

import influxdb
from influxdb.resultset import ResultSet

SERVER_SOFTWARE = os.environ.get("SERVER_SOFTWARE", "Development")
APPSCALE = SERVER_SOFTWARE.startswith('AppScaleServer')
DEBUG = SERVER_SOFTWARE.startswith('Development')


# THIS PIECE OF CODE MUST BE ON TOP BECAUSE IT MONKEY PATCHES THE BUILTIN USER CLASS
# START MONKEY PATCH

def email_lower(email):
    if email is None:
        return None
    email = email.email() if isinstance(email, google.appengine.api.users.User) else email
    email = unicode(email) if not isinstance(email, unicode) else email
    return email.lower()


original_constructor = google.appengine.api.users.User.__init__


def __init__(self, *args, **kwargs):
    if args:
        email = args[0]
        if email:
            lower_email = email_lower(email)
            if lower_email != email:
                args = list(args)
                args[0] = lower_email
    else:
        email = kwargs.get('email', None)
        if email != None:
            lower_email = email_lower(email)
            if lower_email != email:
                kwargs['email'] = lower_email
    original_constructor(self, *args, **kwargs)


google.appengine.api.users.User.__init__ = __init__


# END MONKEY PATCH

# MONKEY PATCH logging
# Add possibility to bring down error levels for deferreds

class _TLocal(threading.local):

    def __init__(self):
        self.suppress = 0


_tlocal = _TLocal()
del _TLocal


def start_suppressing():
    _tlocal.suppress += 1


def stop_suppressing():
    if _tlocal.suppress > 0:
        _tlocal.suppress -= 1


def reset_suppressing():
    _tlocal.suppress = 0


class suppressing(object):

    def __enter__(self):
        start_suppressing()
        return self

    def __exit__(self, *args, **kwargs):
        stop_suppressing()


_orig_error = logging.error
_orig_critical = logging.critical


def _new_error(msg, *args, **kwargs):
    suppress = kwargs.pop('_suppress', True)
    if _tlocal.suppress > 0 and suppress:
        logging.warning(msg, *args, **kwargs)
    else:
        _orig_error(msg, *args, **kwargs)


def _new_critical(msg, *args, **kwargs):
    suppress = kwargs.pop('_suppress', True)
    if _tlocal.suppress > 0 and suppress:
        logging.warning(msg, *args, **kwargs)
    else:
        _orig_critical(msg, *args, **kwargs)


def _new_exception(msg, *args, **kwargs):
    suppress = kwargs.pop('_suppress', True)
    if _tlocal.suppress > 0 and suppress:
        logging.warning(msg, *args, exc_info=1, **kwargs)
    else:
        _orig_error(msg, *args, exc_info=1, **kwargs)


logging.error = _new_error
logging.critical = _new_critical
logging.exception = _new_exception


class StubsFilter(logging.Filter):

    def filter(self, record):
        # Get rid of the annoying 'Sandbox prevented access to file' warnings
        return 'stubs.py' != record.filename


logging.root.addFilter(StubsFilter())


# MONKEY PATCH db

# Add possibility to run post-transaction actions

class __TLocal(threading.local):

    def __init__(self):
        self.propagation = False


_temp_transaction_options = __TLocal()
del __TLocal

_orig_run_in_transaction_options = db.run_in_transaction_options
_options = [attr for attr in dir(TransactionOptions) if isinstance(getattr(TransactionOptions, attr), ConfigOption)]
_clone_options = lambda o: {attr: getattr(o, attr) for attr in _options}
_default_options = _clone_options(db.create_transaction_options())


def _wrap_run_in_transaction_func(is_retries, is_options):
    @wraps(_orig_run_in_transaction_options)
    def wrapped(*args, **kwargs):
        if is_options:
            options = _clone_options(args[0])
            args = args[1:]
        else:
            options = dict(_default_options)
        if is_retries:
            retries = args[0]
            args = args[1:]
        else:
            retries = options['retries']
        options['retries'] = 0
        if options.get('propagation') is None and _temp_transaction_options.propagation:
            options['propagation'] = db.ALLOWED
        options = db.create_transaction_options(**options)

        if db.is_in_transaction():
            return _orig_run_in_transaction_options(options, *args, **kwargs)

        if not retries:
            retries = 3
        if APPSCALE:
            retries += 3

        def run(transaction_guid):
            max_tries = retries + 1
            count = 0
            while count < max_tries:
                count += 1
                start = time.time()
                try:
                    return _orig_run_in_transaction_options(options, *args, **kwargs)
                except (TransactionFailedError, db.Timeout) as e:
                    if isinstance(e, db.Timeout) and type(e) != db.Timeout:
                        raise e  # only retrying in case of db.Timeout exceptions, not subclasses
                    if count == max_tries:
                        raise e
                    transactions.post_transaction_actions.reset(transaction_guid)
                    logging.info("%s: %s. Retrying... (%s)", e.__class__.__name__, e.message, count)
                    sleep_time = 1.1 - (time.time() - start)
                    if sleep_time > 0:
                        logging.info("Sleeping %s seconds ....", sleep_time)
                        time.sleep(sleep_time)

        from rogerthat.utils import transactions
        if db.is_in_transaction():
            transaction_guid = transactions.post_transaction_actions.get_current_transaction_guid()
        else:
            transaction_guid = str(uuid.uuid4())
            transactions.post_transaction_actions.set_current_transaction_guid(transaction_guid)
        try:
            r = run(transaction_guid)
        except:
            transactions.post_transaction_actions.finalize(success=False, transaction_guid=transaction_guid)
            raise
        try:
            transactions.post_transaction_actions.finalize(success=True, transaction_guid=transaction_guid)
        except:
            logging.error("Caught exception in rpc.transaction_done", exc_info=1, _suppress=False)
        return r

    return wrapped


db.run_in_transaction = _wrap_run_in_transaction_func(is_retries=False, is_options=False)
db.run_in_transaction_custom_retries = _wrap_run_in_transaction_func(is_retries=True, is_options=False)
db.run_in_transaction_options = _wrap_run_in_transaction_func(is_retries=False, is_options=True)


# END MONKEY PATCH

def _allow_transaction_propagation(func, *args, **kwargs):
    original_propagation_value = _temp_transaction_options.propagation
    _temp_transaction_options.propagation = True
    try:
        return func(*args, **kwargs)
    finally:
        _temp_transaction_options.propagation = original_propagation_value


db.allow_transaction_propagation = _allow_transaction_propagation
del _allow_transaction_propagation

# MONKEY PATCH json.dump & json.dumps to eliminate useless white space

_orig_json_dumps = json.dumps


def _new_json_dumps(*args, **kwargs):
    if len(args) < 8:
        kwargs.setdefault("separators", (',', ':'))
    try:
        return _orig_json_dumps(*args, **kwargs)
    except Exception as e:
        logging.debug(args)
        raise

json.dumps = _new_json_dumps

_orig_json_dump = json.dump


def _new_json_dump(*args, **kwargs):
    if len(args) < 8:
        kwargs.setdefault("separators", (',', ':'))
    return _orig_json_dump(*args, **kwargs)


json.dump = _new_json_dump

# END MONKEY PATCH
# MONKEY PATCH os.path.expanduser & os.path.expanduser to avoid using
# unspported os.path.getuserid

_orig_os_path_expanduser = os.path.expanduser


def _new_os_path_expanduser(path):
    return path


os.path.expanduser = _new_os_path_expanduser
# END MONKEY PATCH

# MONKEY PATCH deferred.defer

_old_deferred_defer = deferred.defer


def _new_deferred_defer(obj, *args, **kwargs):
    # Sets current user and fixes an issue where the transactional argument wasn't supplied when the task is too large
    from rogerthat.rpc import users
    from mcfw.consts import MISSING
    if users.get_current_deferred_user() == MISSING:
        kwargs['__user'] = users.get_current_user()
    else:
        kwargs['__user'] = users.get_current_deferred_user()

    taskargs = dict((x, kwargs.pop(("_%s" % x), None))
                    for x in ("countdown", "eta", "name", "target",
                              "retry_options"))
    taskargs["url"] = kwargs.pop("_url", deferred.deferred._DEFAULT_URL)
    transactional = kwargs.pop("_transactional", False)
    taskargs["headers"] = dict(deferred.deferred._TASKQUEUE_HEADERS)
    taskargs["headers"].update(kwargs.pop("_headers", {}))
    queue = kwargs.pop("_queue", deferred.deferred._DEFAULT_QUEUE)
    pickled = deferred.serialize(obj, *args, **kwargs)
    try:
        task = taskqueue.Task(payload=pickled, **taskargs)
        return task.add(queue, transactional=transactional)
    except taskqueue.TaskTooLargeError:
        key = deferred.deferred._DeferredTaskEntity(data=pickled).put()
        pickled = deferred.deferred.serialize(deferred.deferred.run_from_datastore, str(key))
        task = taskqueue.Task(payload=pickled, **taskargs)
        # this is the patched line (transactional=transactional)
        return task.add(queue, transactional=transactional)


def _new_deferred_run(data):
    try:
        func, args, kwds = pickle.loads(data)
    except Exception, e:
        raise deferred.PermanentTaskFailure(e)
    else:
        from rogerthat.rpc import users
        current_user = kwds.pop('__user', None)
        if current_user:
            users.set_deferred_user(current_user)

        try:
            dt = datetime.datetime.utcnow()
            # do not log between 00:00 and 00:15
            # too many defers are run at this time
            if dt.hour != 0 or dt.minute > 15:
                from rogerthat.utils import get_current_queue
                logging.debug('Queue: %s\ndeferred.run(%s.%s%s%s)',
                              get_current_queue(),
                              func.__module__, func.__name__,
                              "".join((",\n             %s" % repr(a) for a in args)),
                              "".join((",\n             %s=%s" % (k, repr(v)) for k, v in kwds.iteritems())))
        except:
            logging.exception('Failed to log the info of this defer (%s)', func)

        try:
            return func(*args, **kwds)
        except deferred.PermanentTaskFailure:
            stop_suppressing()
            raise
        except:
            request = webapp2.get_request()
            if request:
                execution_count_triggering_error_log = 9
                execution_count = request.headers.get('X-Appengine-Taskexecutioncount', None)
                if execution_count and int(execution_count) == execution_count_triggering_error_log:
                    logging.error('This deferred.run already failed %s times!', execution_count, _suppress=False)
            raise
        finally:
            if current_user:
                users.clear_user()


deferred.defer = deferred.deferred.defer = _new_deferred_defer
deferred.run = deferred.deferred.run = _new_deferred_run

# END MONKEY PATCH

# MONKEY PATCH expando unindexed properties

_orginal_expando_getattr = db.Expando.__getattribute__


def _new_expando_getattr(self, key):
    if key == '_unindexed_properties':
        return self.__class__._unindexed_properties.union(self.dynamic_properties())
    return _orginal_expando_getattr(self, key)


db.Expando.__getattribute__ = _new_expando_getattr

# END MONKEY PATCH

try:
    # disable the annoying AppenginePlatformWarning's
    from requests.packages import urllib3

    urllib3.disable_warnings()
except ImportError:
    pass
try:
    import requests  # @UnusedImport
    try:
        import requests_toolbelt.adapters.appengine
        requests_toolbelt.adapters.appengine.monkeypatch()
    except ImportError:
        logging.error('You must include `requests-toolbelt` in requirements.txt when using the `requests` library')
except ImportError:
    pass

dummy2 = lambda: None


def _Dynamic_Composite(self, request, response):
    """Implementation of ImagesService::Composite.

    Based off documentation of the PIL library at
    http://www.pythonware.com/library/pil/handbook/index.htm

    Args:
      request: ImagesCompositeRequest - Contains image request info.
      response: ImagesCompositeResponse - Contains transformed image.

    Raises:
      ApplicationError: Bad data was provided, likely data about the dimensions.
    """
    from PIL import Image
    from google.appengine.api import images
    from google.appengine.api.images import images_service_pb
    from google.appengine.api.images.images_stub import _BackendPremultiplication, _ArgbToRgbaTuple, RGBA
    from google.appengine.runtime import apiproxy_errors

    if (not request.canvas().width() or not request.canvas().height() or
            not request.image_size() or not request.options_size()):
        raise apiproxy_errors.ApplicationError(
            images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)
    if (request.canvas().width() > 4000 or
            request.canvas().height() > 4000 or
            request.options_size() > images.MAX_COMPOSITES_PER_REQUEST):
        raise apiproxy_errors.ApplicationError(
            images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)

    width = request.canvas().width()
    height = request.canvas().height()
    color = _ArgbToRgbaTuple(request.canvas().color())

    color = _BackendPremultiplication(color)
    canvas = Image.new(RGBA, (width, height), color)
    sources = []
    for image in request.image_list():
        sources.append(self._OpenImageData(image))

    for options in request.options_list():
        if (options.anchor() < images.TOP_LEFT or
                options.anchor() > images.BOTTOM_RIGHT):
            raise apiproxy_errors.ApplicationError(
                images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)
        if options.source_index() >= len(sources) or options.source_index() < 0:
            raise apiproxy_errors.ApplicationError(
                images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)
        if options.opacity() < 0 or options.opacity() > 1:
            raise apiproxy_errors.ApplicationError(
                images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)
        source = sources[options.source_index()]
        x_anchor = (options.anchor() % 3) * 0.5
        y_anchor = (options.anchor() / 3) * 0.5
        x_offset = int(options.x_offset() + x_anchor * (width - source.size[0]))
        y_offset = int(options.y_offset() + y_anchor * (height - source.size[1]))
        if source.mode == RGBA:
            canvas.paste(source, (x_offset, y_offset), source)
        else:
            # Fix here: alpha must be an integer (and not a float)
            alpha = int(options.opacity() * 255)
            mask = Image.new('L', source.size, alpha)
            canvas.paste(source, (x_offset, y_offset), mask)
    response_value = self._EncodeImage(canvas, request.canvas().output())
    response.mutable_image().set_content(response_value)


def new_query(self,
              query,
              params=None,
              epoch=None,
              expected_response_code=200,
              database=None,
              raise_errors=True,
              chunked=False,
              chunk_size=0):
    """Send a query to InfluxDB.

    :param query: the actual query string
    :type query: str

    :param params: additional parameters for the request,
        defaults to {}
    :type params: dict

    :param epoch: response timestamps to be in epoch format either 'h',
        'm', 's', 'ms', 'u', or 'ns',defaults to `None` which is
        RFC3339 UTC format with nanosecond precision
    :type epoch: str

    :param expected_response_code: the expected status code of response,
        defaults to 200
    :type expected_response_code: int

    :param database: database to query, defaults to None
    :type database: str

    :param raise_errors: Whether or not to raise exceptions when InfluxDB
        returns errors, defaults to True
    :type raise_errors: bool

    :param chunked: Enable to use chunked responses from InfluxDB.
        With ``chunked`` enabled, one ResultSet is returned per chunk
        containing all results within that chunk
    :type chunked: bool

    :param chunk_size: Size of each chunk to tell InfluxDB to use.
    :type chunk_size: int

    :returns: the queried data
    :rtype: :class:`~.ResultSet`
    """
    if params is None:
        params = {}

    params['q'] = query
    params['db'] = database or self._database

    if epoch is not None:
        params['epoch'] = epoch

    if chunked:
        params['chunked'] = 'true'
        if chunk_size > 0:
            params['chunk_size'] = chunk_size

    # START PATCH - use POST request instead of GET
    # Needed because url length is max. 2KB on appengine
    response = self.request(
        url="query",
        method='POST',
        params=None,
        data=urllib.urlencode(params),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        expected_response_code=expected_response_code
    )
    # END PATCH

    if chunked:
        return self._read_chunked_response(response)

    data = response.json()

    results = [
        ResultSet(result, raise_errors=raise_errors)
        for result
        in data.get('results', [])
    ]

    # TODO(aviau): Always return a list. (This would be a breaking change)
    if len(results) == 1:
        return results[0]

    return results


influxdb.InfluxDBClient.query = new_query


if DEBUG:
    # Fixes "System error: new style getargs format but argument is not a tuple" on devserver for composite images
    ImagesServiceStub._Dynamic_Composite = _Dynamic_Composite

    # Log which datastore models are being read / written on the devserver.
    from db_hooks import add_before_put_hook, add_after_get_hook
    from db_hooks.hooks import put_hook, after_get_hook

    add_before_put_hook(put_hook)
    add_after_get_hook(after_get_hook)
