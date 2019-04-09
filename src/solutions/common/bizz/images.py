# -*- coding: utf-8 -*-
# Copyright 2019 Mobicage NV
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
# @@license_version:1.4@@
from cgi import FieldStorage

from google.appengine.ext import ndb

import cloudstorage
from rogerthat.rpc import users
from rogerthat.utils import read_file_in_chunks
from solutions.common.consts import OCA_FILES_BUCKET
from solutions.common.models.forms import UploadedFile


def upload_image(service_user, uploaded_file, prefix, reference=None):
    # type: (users.User, FieldStorage, str, ndb.Key) -> UploadedFile
    content_type = uploaded_file.type or 'image/jpeg'
    extension = '.jpg' if content_type == 'image/jpeg' else '.png'
    image_id = UploadedFile.allocate_ids(1)[0]
    cloudstorage_path = '/%(bucket)s/services/%(service)s/%(prefix)s/%(image_id)d%(extension)s' % {
        'bucket': OCA_FILES_BUCKET,
        'service': service_user.email(),
        'prefix': prefix,
        'image_id': image_id,
        'extension': extension
    }
    image_model = UploadedFile(key=UploadedFile.create_key(service_user, image_id),
                               reference=reference,
                               content_type=content_type,
                               cloudstorage_path=cloudstorage_path)
    with cloudstorage.open(image_model.cloudstorage_path, 'w', content_type=content_type) as f:
        for chunk in read_file_in_chunks(uploaded_file.file):
            f.write(chunk)
    image_model.put()
    return image_model


def list_images(service_user, folder):
    # type: (users.User, str) -> list[cloudstorage.GCSFileStat]
    prefix = '/%s/services/%s/%s' % (OCA_FILES_BUCKET, service_user.email(), folder)
    return [f for f in cloudstorage.listbucket(prefix)]
