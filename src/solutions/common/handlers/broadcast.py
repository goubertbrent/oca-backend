# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import logging

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.settings import get_server_settings
from rogerthat.to.messaging import AttachmentTO
from rogerthat.utils import bizz_check, now, channel
from solutions import SOLUTION_COMMON, translate
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionTempBlob


class UploadAttachmentHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        max_upload_size_mb = 5
        max_upload_size = max_upload_size_mb * 1048576  # 1 MB
        service_user_email = self.request.get("service_user_email")
        service_user = users.User(service_user_email)
        sln_settings = get_solution_settings(service_user)
        name = unicode(self.request.get("name"))
        logging.info('%s uploads an attachment for broadcasting', service_user.email())
        upload_files = self.get_uploads("attachment-files")
        logging.debug('amount of uploaded files: %d', len(upload_files))
        try:
            bizz_check(len(upload_files) != 0, translate(sln_settings.main_language,
                                                         SOLUTION_COMMON, 'please_select_attachment'))
            bizz_check(len(upload_files) == 1,
                       translate(sln_settings.main_language, SOLUTION_COMMON,
                                 'only_one_attachment_allowed'))

            blob_key = None
            for blob in upload_files:
                if not blob.content_type in AttachmentTO.CONTENT_TYPES:
                    blob.delete()
                    raise BusinessException(translate(sln_settings.main_language, SOLUTION_COMMON,
                                                      'attachment_must_be_of_type'))
                elif blob.size > max_upload_size:
                    blob.delete()
                    raise BusinessException(
                        translate(sln_settings.main_language, SOLUTION_COMMON, 'attachment_too_big',
                                  max_size=max_upload_size_mb))
                else:
                    blob_key = unicode(blob.key())
            logging.debug('blob key: %s', blob_key)
            temp_blob = SolutionTempBlob()
            temp_blob.timeout = now() + 86400 * 180  # Store this blob for 6 months
            temp_blob.blob_key = blob_key
            temp_blob.put()
            logging.debug('temp blob created, sending channel message..')
            channel.send_message(service_user, 'solutions.common.broadcast.attachment.upload.success',
                                 url=get_server_settings().baseUrl + '/solutions/common/public/attachment/view/' + blob_key,
                                 name=name)

        except BusinessException, ex:
            channel.send_message(service_user, 'solutions.common.broadcast.attachment.upload.failed',
                                 message=ex.message)


class ViewAttachmentHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, key):
        if not blobstore.get(key):
            self.error(404)
        else:
            self.send_blob(key)
