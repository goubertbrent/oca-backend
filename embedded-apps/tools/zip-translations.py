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
import zipfile
from os import listdir
from os.path import join, dirname, exists

projects_dir = join(dirname(__file__), '..', 'projects')
dist_dir = join(dirname(__file__), '..', 'dist')
projects = listdir(projects_dir)

for project in projects:
    project_dir = join(projects_dir, project)
    i18n_dir = join(project_dir, 'src', 'assets', 'i18n')
    if exists(i18n_dir):
        with zipfile.ZipFile(join(dist_dir, 'i18n-' + project + '.zip'), 'w', zipfile.ZIP_DEFLATED) as f:
            for filename in listdir(i18n_dir):
                f.write(join(i18n_dir, filename), filename)
