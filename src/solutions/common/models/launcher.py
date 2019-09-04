# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

from google.appengine.ext import db, blobstore


class OSALauncherApp(db.Model):
    user = db.UserProperty()
    timestamp = db.IntegerProperty()
    app_id = db.StringProperty()
    version_code = db.IntegerProperty(indexed=False)
    package = blobstore.BlobReferenceProperty()

    @classmethod
    def create_key(cls, app_id):
        return db.Key.from_path(cls.kind(), app_id)


    @classmethod
    def get_by_app_id(cls, app_id):
        key = cls.create_key(app_id)
        return cls.get(key)
