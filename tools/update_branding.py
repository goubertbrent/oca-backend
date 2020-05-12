# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley Belgium NV
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
# @@license_version:1.7@@

from __future__ import unicode_literals
import argparse
import base64
import logging
import os
import uuid
import zipfile
from StringIO import StringIO

import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def call_rogerthat(server_url, api_key, data):
    import urllib2
    import json
    data['id'] = str(uuid.uuid4())
    json_data = json.dumps(data)
    headers = {
        'Content-Type': 'application/json-rpc; charset=utf-8',
        'X-Nuntiuz-API-key': api_key
    }
    request = urllib2.Request(server_url, json_data, headers)
    response = urllib2.urlopen(request)
    if response.getcode() != 200:
        raise Exception(u'%s\n%s' % (response.getcode(), response.read()))
    result = response.read()
    return json.loads(result)


def zip_folder(folder_path):
    """Zip the contents of an entire folder (with that folder included in the archive).
     Empty subfolders will be included in the archive as well.
    """
    os.chdir(folder_path)
    parent_folder = os.path.dirname(folder_path)
    contents = os.walk(folder_path)
    stream = StringIO()
    zip_file = zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED)
    try:
        for root, folders, files in contents:
            # Include all subfolders, including empty ones.
            for folder_name in folders:
                absolute_path = os.path.join(root, folder_name)
                relative_path = absolute_path.replace(folder_path + os.sep, '')
                zip_file.write(absolute_path, relative_path)
            for file_name in files:
                if os.path.splitext(file_name)[1] == '.zip':
                    continue
                absolute_path = os.path.join(root, file_name)
                relative_path = absolute_path.replace(folder_path + os.sep, '')
                zip_file.write(absolute_path, relative_path)
    finally:
        zip_file.close()
    stream.seek(0)
    return stream.getvalue()


def update_branding(server_url, api_key, branding_path, description, position, icon_name, tag):
    if not (os.path.exists(branding_path) and os.path.isdir(branding_path)):
        raise Exception('Folder %s does not exist or is not a folder' % branding_path)
    branding_name = description or os.path.basename(os.path.dirname(branding_path + os.sep))
    branding_zip_content = base64.b64encode(zip_folder(branding_path))
    data = {
        'method': 'system.store_branding',
        'params': {
            'description': branding_name,
            'content': branding_zip_content
        }
    }
    branding_result = call_rogerthat(server_url, api_key, data)
    branding_id = branding_result['result']['id']
    put_menu_item_data = {
        'method': 'system.put_menu_item',
        'params': {
            'icon_name': icon_name,
            'label': branding_name,
            'tag': tag or branding_name,
            'coords': map(int, position.split(',')),
            'screen_branding': branding_id
        }
    }
    call_rogerthat(server_url, api_key, put_menu_item_data)
    publish_data = {
        'method': 'system.publish_changes',
        'params': {}
    }
    call_rogerthat(server_url, api_key, publish_data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--api_key', help='API key of the service')
    parser.add_argument('-b', '--branding', help='folder where the branding is located')
    parser.add_argument('-d', '--description', help='Description of the branding')
    parser.add_argument('-p', '--position', help='Coordinates of the menu item, comma separated')
    parser.add_argument('-u', '--server_url', help='Server url, only used for development',
                        default="https://rogerth.at/api/1")
    parser.add_argument('-t', '--tag')
    parser.add_argument('-i', '--icon_name')
    args = parser.parse_args()
    update_branding(args.server_url, args.api_key, args.branding, args.description, args.position, args.icon_name,
                    args.tag)
