# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
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
# @@license_version:1.6@@

import logging

import cloudstorage
from google.appengine.ext import webapp
from rogerthat.bizz.gcs import get_blobstore_cloudstorage_path


# Old objects that were stored in the blobstore have been moved to cloud storage.
# These blobs are stored at the path /rogerthat-attachments/blobstore/{blob_key}
class CloudStorageBlobstoreHandler(webapp.RequestHandler):
    def get(self, key, *args, **kwargs):
        filename = get_blobstore_cloudstorage_path(key)
        try:
            gcs_stats = cloudstorage.stat(filename)
            self.response.headers['Content-Type'] = gcs_stats.content_type
            self.response.headers['Cache-Control'] = 'public, max-age=31536000'  # Cache forever (1 year)
            self.response.headers['Content-Disposition'] = 'inline; filename=%s' % key
            with cloudstorage.open(filename, 'r') as gcs_file:
                self.response.write(gcs_file.read())

        except cloudstorage.errors.NotFoundError:
            logging.warn('%s NOT found in gcs', filename)
            self.error(404)
