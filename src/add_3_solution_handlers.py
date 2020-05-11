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

import importlib
import pkgutil


def register_solution_callback_api_handlers():
    from rogerthat.rpc.solutions import service_api_callback_handler_functions

    try:
        import solutions
    except ImportError:
        pass  # there are no solutions
    else:
        for _, sln, is_package in pkgutil.iter_modules(solutions.__path__):
            if is_package:
                try:
                    api_callback_handlers = importlib.import_module("solutions.%s.api_callback_handlers" % sln)
                except ImportError:
                    pass  # there are no api_callback_handlers module
                else:
                    service_api_callback_handler_functions(api_callback_handlers)
