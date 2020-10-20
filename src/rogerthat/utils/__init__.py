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
import datetime
import hashlib
import json
import logging
import os
import re
import string
import threading
import time
import traceback
import urllib
import uuid
from copy import deepcopy
from random import choice

from dateutil.parser import parse as datutil_parse
from google.appengine.api import users, mail, urlfetch
from google.appengine.api.datastore import Key
from google.appengine.ext import db
from google.appengine.ext.deferred import deferred
from google.appengine.ext.deferred.deferred import PermanentTaskFailure

import python_http_client
from log_offload.log_offload import LogOffload
from typing import Optional

from mcfw.consts import MISSING
from mcfw.properties import azzert, get_members
from rogerthat.consts import OFFICIALLY_SUPPORTED_LANGUAGES, DEBUG, FAST_QUEUE
from rogerthat.utils.languages import OFFICIALLY_SUPPORTED_ISO_LANGUAGES, get_iso_lang

try:
    import cPickle as pickle
except ImportError:
    import pickle
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

SLOG_HEADER = "[XX-SLOGv1]"
OFFLOAD_HEADER = "[XX-OFFLOADv1]"

PRIVATIZE_LIST_KEYS = ('email_addresses', 'matched_addresses', 'categories', 'components', 'coords')
PRIVATIZE_KEYS = ('message', 'caption', 'latitude', 'longitude', 'password', 'qrcode', 'icon', 'avatar', 'chunk',
                  'static_flow', 'staticFlow', 'shareDescription', 'data', 'profileData', 'cursor', 'content',
                  'description', 'secret', 'image', 'picture', 'details')
ANONIMIZE_KEYS = ('member', 'email', 'sender', 'qualifiedIdentifier', 'qualified_identifier', 'user')


class _TLocal(threading.local):

    def __init__(self):
        self.parent = None


_tlocal = _TLocal()
del _TLocal
log_offload = LogOffload(offload_header=OFFLOAD_HEADER)


def foreach(func, iterable, *args, **kwargs):
    for item in iterable:
        func(item, *args, **kwargs)


def runeach(iterable):
    foreach(lambda f: f(), iterable)


def first(func, iterable):
    for item in iterable:
        if func(item):
            return item
    return None


def circular(lst):
    while True:
        for item in lst:
            yield item


class jsonEncoder(json.JSONEncoder):

    def default(self, obj):
        isa = lambda *xs: any(isinstance(obj, x) for x in xs)  # shortcut
        return obj.isoformat() if isa(datetime.datetime) else \
            dict((p, getattr(obj, p)) for p in obj.properties()) if isa(db.Model) else \
            obj.email() if isa(users.User) else \
            json.JSONEncoder.default(self, obj)


def today():
    now_ = now()
    return now_ - (now_ % (3600 * 24))


_now_impl = lambda: int(time.time())


def now():
    return _now_impl()


def months_between(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def trace(target):
    return target

    from mcfw.cache import set_cache_key

    def wrapper(*args, **kwargs):
        from google.appengine.api import quota
        start_cpu = quota.get_request_cpu_usage()
        start_api = quota.get_request_api_cpu_usage()
        my_parent = _tlocal.parent
        start = time.time()
        _tlocal.parent = start
        try:
            return target(*args, **kwargs)
        finally:
            _tlocal.parent = my_parent
            end = time.time()
            end_cpu = quota.get_request_cpu_usage()
            end_api = quota.get_request_api_cpu_usage()
            logging.info("""*** USAGE TRACING ***:
{"function": "%s.%s", "cpu": %s, "api": %s, "elapsed": %s, "start": %f, "parent": %s}""" % (
                target.__module__, target.__name__,
                int(round(quota.megacycles_to_cpu_seconds(end_cpu - start_cpu) * 1000)),
                int(round(quota.megacycles_to_cpu_seconds(end_api - start_api) * 1000)),
                int(round((end - start) * 1000)),
                start, "%f" % my_parent if my_parent else "null"))

    set_cache_key(wrapper, target)
    if hasattr(target, "meta"):
        wrapper.meta.update(target.meta)
    wrapper.__name__ = target.__name__
    wrapper.__module__ = target.__module__

    return wrapper


def hash_user_identifier(id_):
    if id_ is None:
        return None
    if isinstance(id_, users.User):
        id_ = id_.email()
    if isinstance(id_, unicode):
        id_ = id_.encode('utf-8')
    d = hashlib.md5()
    index = 0
    for ch in id_:
        if ch == ":":
            break
        d.update(ch)
        index += 1
    else:
        return d.hexdigest()
    return d.hexdigest() + id_[index:]


def privatize(data, anonimize=False):
    if isinstance(data, dict):
        result = {}
        for key, value in data.iteritems():
            if value is MISSING:
                continue
            if key == "accept_missing":
                continue
            if isinstance(value, (list, dict)):
                if key in PRIVATIZE_LIST_KEYS and value and isinstance(value, list):
                    value = ["***%d items***" % len(value)]
                else:
                    value = privatize(value, anonimize)
            elif value and key in PRIVATIZE_KEYS:
                value = "*****" if isinstance(value, (str, unicode)) else "#####"
            elif anonimize and key in ANONIMIZE_KEYS:
                value = hash_user_identifier(value)
            result[key] = value
        return result
    elif isinstance(data, list):
        return [privatize(value, anonimize) for value in data]
    return data


def duplicate_entity(entity, **kwargs):
    clazz = entity.__class__
    attributes = dict((k, v.__get__(entity, clazz)) for k, v in clazz.properties().iteritems())
    attributes.update(kwargs)
    return clazz(**attributes)


def ed(val):
    return base64.b64encode(val, "._").replace("=", "-")


def dd(val):
    return base64.b64decode(val.replace("-", "="), "._")


def urlencode(d):
    if not isinstance(d, dict):
        d = dict(d)
    r = dict()
    for k, v in d.iteritems():
        if isinstance(v, unicode):
            r[k] = v.encode('UTF8')
        else:
            r[k] = v
    return urllib.urlencode(r)


def guid():
    return str(uuid.uuid4())


def generate_random_key():
    digester = hashlib.sha256()
    for x in xrange(100):
        digester.update(str(x))
        digester.update(str(uuid.uuid4()))
        digester.update(str(time.time()))

    key = digester.hexdigest()
    return key


def _send_mail(from_, email, subject, body, reply_to, html, attachments, bcc_emails=None):
    emails = []
    if isinstance(email, basestring):
        if email.endswith('@rogerth.at'):
            return
        emails = [email]
    else:
        for e in email:
            if not e.endswith('@rogerth.at'):
                emails.append(e)

    if emails:
        _send_mail_via_sendgrid_api(from_, emails, subject, body, reply_to, html, attachments, bcc_emails=bcc_emails)


def _send_mail_via_sendgrid_api(from_, email, subject, body, reply_to, html, attachments, bcc_emails=None):
    if DEBUG:
        logging.info('Not sending email in debug\nFrom: %s to:%s subject: %s\nbody: %s', from_, email, subject, body)
        return
    import sendgrid
    from sendgrid.helpers import mail as sgMail
    from rogerthat.settings import get_server_settings
    settings = get_server_settings()
    if not settings.sendGridApiKey:
        logging.error("sendGridApiKey is not set", _suppress=False)
        return

    sg = sendgrid.SendGridAPIClient(apikey=(settings.sendGridApiKey))
    message = sgMail.Mail()
    message.from_email = sgMail.Email(from_)
    message.subject = subject

    personalization = sgMail.Personalization()
    if isinstance(email, basestring):
        personalization.add_to(sgMail.Email(email))
    else:
        for e in email:
            personalization.add_to(sgMail.Email(e))

    if not bcc_emails:
        bcc_emails = []
    for e in bcc_emails:
        personalization.add_bcc(sgMail.Email(e))

    message.add_personalization(personalization)

    if reply_to:
        message.reply_to = sgMail.Email(reply_to)

    message.add_content(sgMail.Content('text/plain', body))
    if html:
        message.add_content(sgMail.Content("text/html", html))
    if attachments:
        for attachment_name, attachment_value in attachments:
            extension = attachment_name.split('.')[1]
            mime_type = mail.EXTENSION_MIME_MAP.get(extension, None)
            if mime_type is None:
                mime_type = 'application/octet-stream'

            attachment = sgMail.Attachment()
            attachment.content = attachment_value
            attachment.type = mime_type
            attachment.filename = attachment_name
            attachment.disposition = "attachment"
            message.add_attachment(attachment)

    if DEBUG:
        logging.warn("Not sending real email via api\n%s", message.get())
        return

    try:
        response = sg.client.mail.send.post(request_body=message.get())
    except python_http_client.HTTPError as e:
        logging.debug('Status code: %s', e.status_code)
        logging.debug('Reason: %s', e.reason)
        logging.debug('Body: %s', e.body)
        logging.debug('Headers: %s', e.headers)
        raise e

    try:
        # try/catch just to be sure the mail is not sent over and over
        logging.debug('Status code: %s', response.status_code)
        logging.debug('Body: %s', response.body)
        logging.debug('Headers: %s', response.headers)
    except:
        pass


def send_mail(from_, email, subject, body, reply_to=None, html=None, attachments=None, transactional=None, bcc_emails=None):
    if transactional is None:
        transactional = db.is_in_transaction()

    deferred.defer(_send_mail, from_, email, subject, body, reply_to, html, attachments, bcc_emails=bcc_emails,
                   _transactional=transactional, _queue=FAST_QUEUE)


def send_mail_via_mime(from_, to, mime, transactional=None, send_in_deferred=True):
    try:
        azzert(to)
    except:
        logging.exception('There were no recipients. Not sending out the email.', _suppress=False)
        return
    if transactional is None:
        transactional = db.is_in_transaction()
    if send_in_deferred:
        deferred.defer(_send_mail_via_mime, from_, to, mime, _transactional=transactional, _queue=FAST_QUEUE)
    else:
        _send_mail_via_mime(from_, to, mime)


def _send_mail_via_mime(from_, to, mime):
    import smtplib
    from rogerthat.settings import get_server_settings
    settings = get_server_settings()

    mime_string = mime.as_string()
    logging.info("mime_string type: %s", type(mime_string))
    if DEBUG:
        logging.warn("Not sending real email via mime\n%s", mime_string[:1000])
        for part in mime.walk():
            logging.info("part.get_content_type(): %s", part.get_content_type())
            if part.get_content_type() in ('text/plain', 'text/html'):
                logging.info(base64.b64decode(part.get_payload()))
        return

    if isinstance(to, basestring) and to.endswith('@rogerth.at'):
        logging.debug("Not sending real email to rogerth.at domains")
        return

    if settings.dkimPrivateKey:
        if from_ == settings.dashboardEmail or "<%s>" % settings.dashboardEmail in from_:
            logging.info("Adding dkim signature")
            try:
                import dkim
                signature = dkim.sign(mime_string,
                                      'dashboard.email',
                                      settings.dashboardEmail.split('@')[1],
                                      settings.dkimPrivateKey,
                                      include_headers=['To', 'From', 'Subject'])
                logging.info("signature type: %s", type(signature))
                mime_string = signature.encode('utf-8') + mime_string
            except:
                logging.exception("Could not create dkim signature!")
        else:
            logging.info("Skipping dkim signature because '%s' != '%s'", from_, settings.dashboardEmail)

    mailserver = smtplib.SMTP_SSL(settings.smtpserverHost, int(settings.smtpserverPort))
    mailserver.ehlo()
    mailserver.login(settings.smtpserverLogin, settings.smtpserverPassword)
    mailserver.sendmail(from_, to, mime_string)
    mailserver.quit()


def xml_escape(value):
    return value.replace("&", "&amp;").replace("\"", "&quot;").replace("'", "&apos;").replace("<", "&lt;").replace(">",
                                                                                                                   "&gt;")


def bizz_check(condition, error_message='', error_class=None):
    if not condition:
        from rogerthat.rpc.service import BusinessException
        if error_class is None:
            error_class = BusinessException
        else:
            azzert(issubclass(error_class, BusinessException))
        raise error_class(error_message)


def strip_weird_chars(val):
    allowed = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'"
    return "".join((l for l in val if l in allowed))


def determine_if_platform_supports_rogerthat_by_user_agent(user_agent):
    user_agent = user_agent.lower()
    return "android" in user_agent \
           or "iphone" in user_agent \
           or "ipad" in user_agent \
           or "ipod" in user_agent


def get_platform_by_user_agent(user_agent):
    user_agent = user_agent.lower()
    if "android" in user_agent:
        return "android"
    if "iphone" in user_agent or "ipad" in user_agent or "ipod" in user_agent:
        return "ios"
    return False


def get_smartphone_install_url_by_user_agent(user_agent, app_id):
    from rogerthat.dal.app import get_app_by_id
    if "Android" in user_agent:
        return get_app_by_id(app_id).android_market_android_uri
    elif any((i in user_agent for i in ('iPhone', 'iPad', 'iPod'))):
        return get_app_by_id(app_id).ios_appstore_ios_uri
    return None


def safe_file_name(filename):
    safe = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.0123456789"
    return str("".join((l in safe and l or "_" for l in filename)))


def parse_color(color):
    color = color.lstrip('#')
    if len(color) == 3:
        color = color[0] * 2 + color[1] * 2 + color[2] * 2
    m = re.match("^([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})$", color)
    if not m:
        raise ValueError("%s is not a valid color." % color)
    return tuple(map(lambda x: int(x, 16), m.groups()))


def slog(msg_=None, email_=None, function_=None, **kwargs):
    seconds = time.time()
    t = time.strftime('%a, %d %b %Y %H:%M:%S.%%03d', time.gmtime(seconds)) % ((seconds % 1) * 1000)
    d = {
        'T': t,
        't': seconds,
        '_c': os.environ.get('HTTP_X_APPENGINE_COUNTRY', '<unknown>'),
        '_i': os.environ.get('INSTANCE_ID', '<unknown>'),
        '_dc': os.environ.get('DATACENTER', '<unknown>'),
        '_t': threading.current_thread().ident
    }
    if msg_:
        d['m'] = msg_
    if email_:
        d['e'] = email_
    if function_:
        d['f'] = function_
    if kwargs:
        d['a'] = privatize(deepcopy(kwargs))
    logging.info("%s %s" % (SLOG_HEADER, json.dumps(d)))


OFFLOAD_TYPE_APP = "app"
OFFLOAD_TYPE_WEB = "web"
OFFLOAD_TYPE_WEB_CHANNEL = "web_channel"
OFFLOAD_TYPE_API = "api"
OFFLOAD_TYPE_CALLBACK_API = "callback_api"
OFFLOAD_TYPES = (OFFLOAD_TYPE_APP, OFFLOAD_TYPE_WEB, OFFLOAD_TYPE_WEB_CHANNEL,
                 OFFLOAD_TYPE_API, OFFLOAD_TYPE_CALLBACK_API)


def offload(user, type_, request_data, response_data, function=None, success=None):
    return log_offload.create_log(user and hash_user_identifier(user.email()), type_, privatize(request_data, True),
                                  privatize(response_data, True), function, success)


def generate_password(size):
    letters = list(string.letters)
    letters.remove('l')
    letters.remove('I')
    letters.remove('O')
    digits = list(string.digits)
    digits.remove('0')
    digits.remove('1')
    return unicode(''.join([choice(letters + digits) for _ in range(size)]))


def try_or_defer(function, *args, **kwargs):
    from add_1_monkey_patches import stop_suppressing, start_suppressing
    log_first_error = kwargs.pop('log_first_error', False)
    start_suppressing()
    try:
        try:
            kw = {k: v for k, v in kwargs.iteritems() if not k.startswith('_')}
            function(*args, **kw)
        except Exception, e:
            if isinstance(e, PermanentTaskFailure):  # BusinessException inherits from PermanentTaskFailure
                logging.info('PermanentTaskFailure', exc_info=True)
                raise e
            else:
                logging.exception(e, _suppress=(not log_first_error))

            deferred.defer(function, *args, **kwargs)
            logging.exception("Failed to execute %s, deferring ...." % function)
    finally:
        stop_suppressing()


def get_country_code_by_ipaddress(ipaddress):
    from rogerthat.settings import get_server_settings
    from rogerthat.utils.crypto import encrypt_for_jabber_cloud, decrypt_from_jabber_cloud

    if not ipaddress:
        logging.info("Can't resolve country if there is no IP address.")
        return None

    settings = get_server_settings()
    jabberEndpoint = choice(settings.jabberEndPoints)
    challenge, data = encrypt_for_jabber_cloud(settings.jabberSecret.encode('utf8'), ipaddress.encode('utf8'))
    response = urlfetch.fetch(url="http://%s/ip2country" % jabberEndpoint, payload=data, method="POST",
                              allow_truncated=False, follow_redirects=False, validate_certificate=False)
    if response.status_code == 200:
        country_code = decrypt_from_jabber_cloud(settings.jabberSecret.encode('utf8'), challenge, response.content)
        return country_code
    else:
        logging.warn("Failed to get country from ip2country. status_code: %s" % response.status_code)
        return None


def llist(value):
    if hasattr(value, "__iter__"):
        for val in value:
            yield val
    else:
        yield value


def get_python_stack_trace(short=True):
    stack = traceback.format_stack()
    if short and len(stack) > 4:
        return stack[-5]
    return ''.join(stack)


def is_flag_set(flag, value):
    return value & flag == flag


def set_flag(flag, value):
    return flag | value


def unset_flag(flag, value):
    return value & ~flag


def is_clean_app_user_email(user):
    pieces = user.email().split('@')
    if len(pieces) != 2:
        return False
    if pieces[0] == '' or pieces[1] == '':
        return False
    if '/' in user.email():
        return False
    return True


def case_insensitive_compare(a, b):
    return cmp(a.lower(), b.lower()) or cmp(a, b)


def reversed_dict(d):
    return {v: k for k, v in d.iteritems()}


def get_full_language_string(short_language):
    """ Map short language ('en', 'fr') to long language str ('English', 'French (Français)') """
    language = OFFICIALLY_SUPPORTED_ISO_LANGUAGES.get(short_language)
    if language is None:
        language = OFFICIALLY_SUPPORTED_LANGUAGES.get(short_language)
    azzert(language)
    return language


def get_officially_supported_languages(iso_format=True):
    short_getter = lambda (shortlang, longlang): shortlang
    long_getter = lambda (shortlang, longlang): longlang

    D = OFFICIALLY_SUPPORTED_ISO_LANGUAGES if iso_format else OFFICIALLY_SUPPORTED_LANGUAGES
    return map(short_getter, sorted(D.iteritems(), key=long_getter))


def filename_friendly_time(timestamp):
    return time.strftime("%Y-%m-%d--%H-%M-%S", time.gmtime(timestamp))


def is_numeric_string(s):
    try:
        int(s)
        return True
    except:
        return False


def file_get_contents(filename):
    with open(filename) as f:
        return f.read()

# @returns(long)
# @arguments((datetime.datetime, datetime.date))


def get_epoch_from_datetime(datetime_):
    if isinstance(datetime_, datetime.datetime):
        epoch = datetime.datetime.utcfromtimestamp(0)
    elif isinstance(datetime_, datetime.date):
        epoch = datetime.date.fromtimestamp(0)
    else:
        azzert(False, "Provided value should be a datetime.datetime or datetime.date instance")
    delta = datetime_ - epoch
    return long(delta.total_seconds())


# @returns(int)
# @arguments(datetime.date)


def calculate_age_from_date(born):
    today = datetime.date.today()
    try:
        birthday = born.replace(year=today.year)
    except ValueError:  # raised when birth date is February 29 and the current year is not a leap year
        birthday = born.replace(year=today.year, day=born.day - 1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


def email_to_id(email):
    from rogerthat.settings import get_server_settings
    from rogerthat.utils.crypto import encrypt_value, sha256
    from mcfw.serialization import s_str

    settings = get_server_settings()
    settings.secret = settings.secret or str(uuid.uuid4())
    tmp_secret = uuid.uuid4().get_bytes()
    stream = StringIO()
    s_str(stream, tmp_secret)
    email = email if isinstance(email, str) else email.encode("utf-8")
    s_str(stream, encrypt_value(sha256("%s%s" % (tmp_secret, settings.secret.encode("utf-8"))), email))
    return base64.encodestring(stream.getvalue())


def id_to_email(id_):
    from rogerthat.settings import get_server_settings
    from rogerthat.utils.crypto import sha256, decrypt_value
    from mcfw.serialization import ds_str

    settings = get_server_settings()
    stream = StringIO(base64.decodestring(id_))
    tmp_secret = ds_str(stream)
    return decrypt_value(sha256("%s%s" % (tmp_secret, settings.secret.encode("utf-8"))), ds_str(stream)).decode('utf-8')


def replace_url_with_forwarded_server(upload_url):
    from rogerthat.settings import get_server_settings
    http_x_forwarded = os.environ.get('HTTP_X_FORWARDED_SERVER')
    if not http_x_forwarded:
        http_x_forwarded = os.environ.get('HTTP_X_FORWARDED_HOST')
    if http_x_forwarded and http_x_forwarded != os.environ.get('SERVER_NAME'):
        to_replace_part = 'https://%s/' % os.environ.get('SERVER_NAME')
        if upload_url.startswith(to_replace_part):
            ss = get_server_settings()
            upload_url = "%s/%s" % (ss.baseUrl, upload_url[len(to_replace_part):])
    return upload_url


def format_price(price, currency=None):
    price_string = u'{:0,.2f}'.format(price / 100.0)
    if currency:
        price_string = '%s %s' % (currency, price_string)
    return price_string


def correct_base64_padding_if_needed(val):
    incorrect_padding_check = len(val) % 8
    if incorrect_padding_check != 0:
        for _ in xrange(8 - incorrect_padding_check):
            val = "%s=" % val
    return val


def get_current_queue():
    return _get_request_header('X-Appengine-Queuename')


def get_current_task_name():
    return _get_request_header('X-Appengine-TaskName')


def _get_request_header(header_name):
    try:
        import webapp2
        request = webapp2.get_request()
        if request:
            return request.headers.get(header_name, None)
    except:
        logging.warn('Failed to get header %s' % header_name, exc_info=1)


def get_backend_service():
    service_name = u'service-backend'
    if DEBUG:
        return None
    current_version = get_current_version()
    if not current_version:
        return None
    if ':' in current_version:
        return None
    return u'%s-dot-%s' % (current_version, service_name)


def get_current_version():
    if DEBUG:
        return os.environ.get('SERVER_PORT')
    return os.environ.get('GAE_VERSION')


def get_current_service():
    if DEBUG:
        return os.environ.get('SERVER_PORT')
    return os.environ.get('GAE_SERVICE')


def clamp(val, minimum=0, maximum=255):
    if val < minimum:
        return minimum
    if val > maximum:
        return maximum
    return val


def colorscale(hexstr, scalefactor):
    """
    Scales a hex string by ``scalefactor``. Returns scaled hex string.
    To darken the color, use a float value between 0 and 1.
    To brighten the color, use a float value greater than 1.
    # >>> colorscale("#DF3C3C", .5)
    #6F1E1E
    # >>> colorscale("#52D24F", 1.6)
    #83FF7E
    # >>> colorscale("#4F75D2", 1)
    #4F75D2
    """

    hexstr = hexstr.strip('#')

    if scalefactor < 0 or len(hexstr) != 6:
        return hexstr

    r, g, b = int(hexstr[:2], 16), int(hexstr[2:4], 16), int(hexstr[4:], 16)

    r = clamp(r * scalefactor)
    g = clamp(g * scalefactor)
    b = clamp(b * scalefactor)

    return u"#%02x%02x%02x" % (r, g, b)


def merge_transfer_object(src_to, dst_to):
    complex_members, simple_members = get_members(type(src_to))
    for attr_name, _ in simple_members:
        if hasattr(dst_to, attr_name):
            setattr(dst_to, attr_name, getattr(src_to, attr_name))
    for attr_name, prop in complex_members:
        if hasattr(dst_to, attr_name):
            src_value = getattr(src_to, attr_name)
            if prop.list:
                dst_value = [merge_transfer_object(x, prop.type()) for x in src_value]
            else:
                dst_value = merge_transfer_object(src_value, prop.type())
            setattr(dst_to, attr_name, dst_value)
    return dst_to


def to_pascal_case(snake_case_str):
    components = snake_case_str.split('_')
    return ''.join(x.title() for x in components)


CHUNK_SIZE = 1024 * 1024


def read_file_in_chunks(file_obj, chunk_size=CHUNK_SIZE):
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
        yield chunk


def drop_index(the_index):
    while True:
        search_result = the_index.get_range(ids_only=True)
        ids = [r.doc_id for r in search_result.results]
        if not ids:
            break
        the_index.delete(ids)


def get_server_url():
    """
        Return current server url, does not work in a task
    """
    host = os.environ.get('HTTP_X_FORWARDED_HOST') or os.environ['HTTP_HOST']
    return u'%s://%s' % (os.environ['wsgi.url_scheme'], host)


def random_string(stringLength):
    """Generate a random string with the combination of lowercase and uppercase letters """
    letters = string.ascii_letters
    return ''.join(choice(letters) for _ in range(stringLength))


def date_to_iso_format(date):
    # type: (datetime.datetime) -> unicode
    return date and u'%sZ' % date.isoformat()


def parse_date(date_str):
    # type: (str) -> Optional[datetime]
    return date_str and datutil_parse(date_str).replace(tzinfo=None)
