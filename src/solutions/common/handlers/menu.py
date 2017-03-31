# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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
# @@license_version:1.2@@

from google.appengine.ext.webapp import blobstore_handlers
from solutions.common.models import FileBlob


class ViewMenuItemImageHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, image_id):
        image_id = long(image_id)
        image = FileBlob.get_by_id(image_id)
        if not image:
            self.error(404)
        else:
            self.response.headers['Cache-Control'] = 'public, max-age=31536000'
            self.response.headers['Content-Type'] = 'image/jpeg'
            self.response.write(image.content)
