# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

import datetime
import logging
import urllib
from cgi import FieldStorage
from mimetypes import guess_extension

import webapp2

from rogerthat.bizz.gcs import upload_to_gcs, get_serving_url
from rogerthat.consts import ROGERTHAT_ATTACHMENTS_BUCKET
from rogerthat.rpc.service import BusinessException
from rogerthat.rpc.users import get_current_user
from rogerthat.to.messaging import AttachmentTO
from rogerthat.utils import channel, guid
from solutions import SOLUTION_COMMON, translate
from solutions.common.dal import get_solution_settings


class UploadAttachmentHandler(webapp2.RequestHandler):

    def post(self):
        max_upload_size_mb = 5
        max_upload_size = max_upload_size_mb * 1048576  # 1 MB
        service_user = get_current_user()
        sln_settings = get_solution_settings(service_user)
        name = unicode(self.request.get("name"))
        logging.info('%s uploads an attachment for broadcasting', service_user.email())
        uploaded_file = self.request.POST.get('attachment-files')  # type: FieldStorage
        try:
            if not isinstance(uploaded_file, FieldStorage):
                raise BusinessException(
                    translate(sln_settings.main_language, SOLUTION_COMMON, 'please_select_attachment'))
            file_content = uploaded_file.value
            if len(file_content) > max_upload_size:
                raise BusinessException(translate(sln_settings.main_language, SOLUTION_COMMON, 'attachment_too_big',
                                                  max_size=max_upload_size_mb))
            content_type = uploaded_file.type
            if content_type not in AttachmentTO.CONTENT_TYPES:
                raise BusinessException(
                    translate(sln_settings.main_language, SOLUTION_COMMON, 'attachment_must_be_of_type'))
            date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
            extension = guess_extension(content_type)
            filename = '%s/news/%s/%s_%s%s' % (ROGERTHAT_ATTACHMENTS_BUCKET, service_user.email(), date, guid(),
                                               extension)
            blob_key = upload_to_gcs(file_content, content_type, filename)
            logging.debug('blob key: %s', blob_key)
            filename = '/'.join(map(urllib.quote, filename.split('/')))
            channel.send_message(service_user, 'solutions.common.broadcast.attachment.upload.success',
                                 url=get_serving_url(filename),
                                 name=name)

        except BusinessException as ex:
            channel.send_message(service_user, 'solutions.common.broadcast.attachment.upload.failed',
                                 message=ex.message)
