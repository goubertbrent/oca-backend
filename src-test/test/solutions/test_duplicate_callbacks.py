# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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

import mc_unittest


class TestCase(mc_unittest.TestCase):

    def test_no_duplicate_solution_callbacks(self):
        from add_3_solution_handlers import register_solution_callback_api_handlers
        register_solution_callback_api_handlers()
        register_solution_callback_api_handlers()
