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

import sys
from os import path
from google.appengine.ext import vendor, webapp

lib_dir = path.join(path.dirname(path.realpath(__file__)), 'lib')
vendor.add(lib_dir)
sys.path.insert(0, path.join(lib_dir, 'lib.zip'))

from add_1_monkey_patches import dummy2
from add_2_zip_imports import dummy
from add_3_solution_handlers import register_solution_callback_api_handlers

dummy2()
dummy()
register_solution_callback_api_handlers()

# Load custom Django template filters
webapp.template.register_template_library('rogerthat.templates.filter')
