# -*- coding: utf-8 -*-
# Copyright 2021 Green Valley NV
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

import requests
from google.appengine.api.app_identity.app_identity import get_application_id
from typing import List, Optional

from rogerthat.consts import DEBUG
from rogerthat.settings import get_server_settings

IMAGING_SERVICE_URL = 'http://localhost:8334' if DEBUG else 'https://imageresizer-dot-%s.ew.r.appspot.com' % get_application_id()

encoding_mapping = {
    'image/png': 'PNG',
    'image/jpeg': 'JPEG',
}


class ImageRequest(object):
    def __init__(self, content_type, quality, max_size, bucket, filename):
        # type: (str, int, int, str, str) -> None
        self.encoding = encoding_mapping.get(content_type)
        if not self.encoding:
            raise Exception('Invalid file, content type %s not supported' % content_type)
        self.quality = quality
        self.max_size = max_size
        self.bucket = bucket
        self.filename = filename

    def to_dict(self):
        return {
            'encoding': self.encoding,
            'quality': self.quality,
            'max_size': self.max_size,
            'bucket': self.bucket,
            'filename': self.filename,
        }


class ResizedImage(object):
    def __init__(self, url, path, width, height, size, content_type):
        # type: (str, str, int, int, int, str) -> None
        self.url = url
        self.path = path
        self.width = width
        self.height = height
        self.size = size
        self.content_type = content_type


def generate_scaled_images(image_url, image_requests):
    # type: (str, List[ImageRequest]) -> List[Optional[ResizedImage]]
    content = {
        'url': image_url,
        'requests': [r.to_dict() for r in image_requests]
    }
    key = get_server_settings().imageResizerApiKey
    if not key:
        raise Exception('ServerSettings.imageResizerApiKey is not set')
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json',
        'X-API-Key': key,
    }
    response = requests.post(IMAGING_SERVICE_URL + '/resize', json=content, headers=headers, timeout=30)
    response.raise_for_status()
    # Can return None when the resized image would be larger than the original
    return [ResizedImage(**result) if result else None for result in response.json()['results']]
