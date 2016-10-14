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
import hashlib
import logging

from const import SECRET_PP, SECRET_AP
from google.appengine.ext import db
from google.appengine.ext.db.metadata import get_kinds
from models import BackupSettings
import webapp2


class ConfigHandler(webapp2.RequestHandler):

    def get(self):
        s = BackupSettings.get_or_insert("settings")
        self.response.write("""<html><body><form method="POST">
Available models:<br>
%s
Ignore models:<br>
<textarea name="ignore-models" rows="5" cols="80">%s</textarea><br>
<br>
Set password:<br>
<input type="password" name="pass1"/><br>
Repeat:<br>
<input type="password" name="pass2"/><br>
<br>
<input type="submit" value="submit"/>
""" % (", ".join(get_kinds()), "\n".join(s.ignore_models)))

    def post(self):
        models = [m.strip() for m in self.request.get('ignore-models').split('\n')]
        pass1 = self.request.get("pass1")
        pass2 = self.request.get("pass2")
        if pass1 and pass1 != pass2:
            logging.error("Could not validate passwords.")
            self.error(500)
            return
        def trans():
            s = BackupSettings.get_by_key_name("settings")
            s.ignore_models = models
            if pass1:
                d = hashlib.sha512(SECRET_PP)
                d.update(pass1)
                d.update(SECRET_AP)
                s.server_secret_hash = d.hexdigest()
            s.put()
        db.run_in_transaction(trans)
        self.redirect('/')

app = webapp2.WSGIApplication([
    ('/', ConfigHandler)
], debug=True)
