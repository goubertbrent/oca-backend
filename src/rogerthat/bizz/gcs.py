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

from __future__ import unicode_literals

from urllib import quote

import cloudstorage
from google.appengine.api.blobstore import blobstore

from rogerthat.consts import DEBUG, ROGERTHAT_ATTACHMENTS_BUCKET
from rogerthat.settings import get_server_settings
from rogerthat.utils import read_file_in_chunks


def upload_to_gcs(file_data, content_type, file_name):
    """
    Args:
        file_data (str or file-like object)
        content_type (unicode)
        file_name (unicode)
    Returns:
        blob_key (unicode): An encrypted `BlobKey` string.
    """
    # this can fail on the devserver for some reason
    with cloudstorage.open(file_name, 'w', content_type=content_type) as f:
        if isinstance(file_data, basestring):
            f.write(file_data)
        else:
            try:
                for chunk in read_file_in_chunks(file_data):
                    f.write(chunk)
            except AttributeError:
                raise ValueError('file_data must be a file-like object')

    return blobstore.create_gs_key('/gs' + file_name).decode('utf-8')


def get_serving_url(filename):
    """
    Args:
        filename (unicode)
    """
    path, file_name = filename.rsplit('/', 1)
    full_path = '%s/%s' % (path, quote(file_name))
    if DEBUG:
        return '%s/_ah/gcs%s' % (get_server_settings().baseUrl, full_path)
    return 'https://storage.googleapis.com%s' % full_path


def get_blobstore_cloudstorage_path(blob_key):
    return '%s/blobstore/%s' % (ROGERTHAT_ATTACHMENTS_BUCKET, blob_key)
