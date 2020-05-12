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

from datetime import datetime

from google.appengine.ext.deferred import deferred

import cloudstorage
from mcfw.utils import chunks

OLD_BUCKET = '/rogerthat-protocol-logs'
NEW_BUCKET = '/log-monitoring'


def _get_folder_name(date):
    return '%04d-%02d-%02d %02d:00:00' % (date.year, date.month, date.day, date.hour)


def _get_files():
    files = []
    for f in cloudstorage.listbucket(OLD_BUCKET):
        split = f.filename.split('/protocol-logs-')[1].split('.')
        date_str = split[0]
        date = datetime.strptime(date_str, '%Y%m%d')
        if split[-1] == 'processed' or date < datetime(2016, 3, 17):
            continue
        files.append(f.filename)
    return files


def migrate():
    files = _get_files()
    for files_list in chunks(files, 50):
        deferred.defer(_do_move_logs, files_list)


def _do_move_logs(files):
    for filename in files:
        split = filename.split('/protocol-logs-')[1].split('.')
        date_str, number = split[0], split[1]
        date = datetime.strptime(date_str, '%Y%m%d')
        if split[-1] == 'processed' or date < datetime(2016, 3, 17):
            continue
        folder_name = _get_folder_name(date)
        new_filename = '%s/%s/rogerthat-server-%s.json' % (NEW_BUCKET, folder_name, number)
        cloudstorage.copy2(filename, new_filename)
