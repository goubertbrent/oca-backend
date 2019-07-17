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
from mimetypes import guess_extension

from google.appengine.ext import ndb

import cloudstorage
from mcfw.exceptions import HttpBadRequestException
from rogerthat.rpc import users
from rogerthat.to.messaging import AttachmentTO
from rogerthat.utils import read_file_in_chunks
from solutions.common.consts import OCA_FILES_BUCKET
from solutions.common.models.forms import UploadedFile


def upload_file(service_user, uploaded_file, prefix, reference=None):
    # type: (users.User, FieldStorage, str, ndb.Key) -> UploadedFile
    content_type = uploaded_file.type
    if content_type not in AttachmentTO.CONTENT_TYPES:
        raise HttpBadRequestException('oca.attachment_must_be_of_type')
    extension = guess_extension(content_type)
    if not extension:
        raise HttpBadRequestException('oca.attachment_must_be_of_type')
    file_id = UploadedFile.allocate_ids(1)[0]
    cloudstorage_path = '/%(bucket)s/services/%(service)s/%(prefix)s/%(file_id)d%(extension)s' % {
        'bucket': OCA_FILES_BUCKET,
        'service': service_user.email(),
        'prefix': prefix,
        'file_id': file_id,
        'extension': extension
    }
    uploaded_file.file.seek(0, 2)
    size = uploaded_file.file.tell()
    uploaded_file.file.seek(0)
    file_model = UploadedFile(key=UploadedFile.create_key(service_user, file_id),
                              reference=reference,
                              content_type=content_type,
                              size=size,
                              cloudstorage_path=cloudstorage_path)
    with cloudstorage.open(file_model.cloudstorage_path, 'w', content_type=content_type) as f:
        for chunk in read_file_in_chunks(uploaded_file.file):
            f.write(chunk)
    file_model.put()
    return file_model


def list_files(service_user):
    # type: (users.User) -> list[UploadedFile]
    return UploadedFile.list_by_user(service_user)