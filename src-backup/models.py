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
from google.appengine.ext import db
from mcfw.cache import cached
from mcfw.rpc import returns, arguments
from mcfw.serialization import deserializer, serializer, ds_model, s_model, \
    register

class BackupSettings(db.Model):
    ignore_models = db.StringListProperty()
    server_secret_hash = db.StringProperty()

    def put(self):
        super(BackupSettings, self).put()
        get_settings.invalidate_cache()

@deserializer
def ds_bs(stream):
    return ds_model(stream, BackupSettings)

@serializer
def s_bs(stream, app):
    s_model(stream, app, BackupSettings)

register(BackupSettings, s_bs, ds_bs)

@cached(1)
@returns(BackupSettings)
@arguments()
def get_settings():
    return BackupSettings.get_by_key_name("settings")