# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

import test  # @UnusedImport
from rogerthat.consts import DEBUG
from rogerthat.translations import DEFAULT_LANGUAGE
from solutions.jinja_extensions import TranslateExtension
import jinja2
import mc_unittest
import os

class TestTranslationExtension(mc_unittest.TestCase):

    def test_translation_extension(self):
        sln_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src', 'solutions')
        JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(sln_dir, 'common', 'templates')),
                                               extensions=[TranslateExtension])

        template = JINJA_ENVIRONMENT.get_template('reservations.html')
        template.render({'language': DEFAULT_LANGUAGE,
                         'debug': DEBUG})
