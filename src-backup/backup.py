# -*- coding: utf-8 -*-
# COPYRIGHT (C) 2011-2014 MOBICAGE NV
# ALL RIGHTS RESERVED.
#
# ALTHOUGH YOU MAY BE ABLE TO READ THE CONTENT OF THIS FILE, THIS FILE
# CONTAINS CONFIDENTIAL INFORMATION OF MOBICAGE NV. YOU ARE NOT ALLOWED
# TO MODIFY, REPRODUCE, DISCLOSE, PUBLISH OR DISTRIBUTE ITS CONTENT,
# EMBED IT IN OTHER SOFTWARE, OR CREATE DERIVATIVE WORKS, UNLESS PRIOR
# WRITTEN PERMISSION IS OBTAINED FROM MOBICAGE NV.
#
# THE COPYRIGHT NOTICE ABOVE DOES NOT EVIDENCE ANY ACTUAL OR INTENDED
# PUBLICATION OF SUCH SOURCE CODE.
#
# @@license_version:1.7@@
import gc
import hashlib
import json
import logging
import time

from const import SECRET_PP, SECRET_AP
from google.appengine.ext import db
from google.appengine.ext.db import model_to_protobuf
from google.appengine.ext.db.metadata import get_kinds
from mcfw.serialization import s_str
from models import get_settings
import webapp2


MAX_RESULT_SIZE = 30 * 1024 * 1024
MAX_RUNNING_TIME = 50

def validate_password(settings, password):
    d = hashlib.sha512()
    d.update(SECRET_PP)
    d.update(password)
    d.update(SECRET_AP)
    return d.hexdigest() == settings.server_secret_hash

class ModelsHandler(webapp2.RequestHandler):

    def post(self):
        settings = get_settings()
        if not settings:
            logging.error("Could not load settings")
            self.abort(500)
            return
        if not validate_password(settings, self.request.get("password")):
            logging.error("Could not validate password!")
            self.abort(500)
            return
        kinds = list()
        for kind in get_kinds():
            if not (kind in settings.ignore_models or kind.startswith("_")):
                kinds.append(kind)
        self.response.headers['Content-Type'] = 'application/json-rpc'
        json.dump(kinds, self.response.out)

class EntitiesHandler(webapp2.RequestHandler):

    def post(self):
        gc.collect()
        settings = get_settings()
        if not settings:
            logging.error("Could not load settings")
            self.abort(500)
            return
        if not validate_password(settings, self.request.get("password")):
            logging.error("Could not validate password!")
            self.abort(500)
            return

        cursor = self.request.get("cursor")
        kind = self.request.get("kind")
        if not kind:
            logging.error("Kind parameter is required")
            self.abort(500)
            return

        logging.info("Kind: %s", kind)
        logging.info("Cursor: %s", cursor)

        cls = type(str(kind), (db.Model,), dict())

        qry = db.GqlQuery("SELECT * FROM %s" % kind)
        qry.with_cursor(cursor)

        now = lambda: int(time.time())
        start = now()

        bytes_written = 0
        entity_count = 0
        stop = False

        checksum = hashlib.sha256(self.request.get("password"))
        for ent in qry:
            buf = str(model_to_protobuf(ent).SerializeToString())
            s_str(self.response.out, buf)
            checksum.update(buf)
            entity_count += 1
            bytes_written += len(buf) + 4
            if bytes_written > MAX_RESULT_SIZE or now() - start > MAX_RUNNING_TIME:
                break
        else:
            stop = True

        logging.info("Entity count: %s\nBytes served: %s\nMore: %s", entity_count, bytes_written, not stop)

        if not stop:
            self.response.headers['X-Cursor'] = qry.cursor()
        self.response.headers['X-Checksum'] = checksum.hexdigest()
        self.response.headers['Content-Type'] = 'application/octet-stream'

app = webapp2.WSGIApplication([
    ('/models', ModelsHandler),
    ('/backup', EntitiesHandler)
], debug=True)
