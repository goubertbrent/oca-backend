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

import webapp2

from rogerthat.rpc import users
from rogerthat.pages.login import SessionHandler
from solutions.common.bizz import SolutionModule
from solutions.common.bizz.menu import export_menu_to_excel
from solutions.common.dal import get_solution_settings
from solutions.common.models import FileBlob
from solutions.flex import SOLUTION_FLEX


class ViewMenuItemImageHandler(webapp2.RequestHandler):

    def get(self, image_id):
        image_id = long(image_id)
        image = FileBlob.get_by_id(image_id)
        if not image:
            self.error(404)
        else:
            self.response.headers['Cache-Control'] = 'public, max-age=31536000'
            self.response.headers['Content-Type'] = 'image/jpeg'
            self.response.write(image.content)


class ExportMenuHandler(SessionHandler):

    def get(self):
        service_user = users.get_current_user()
        sln_settings = get_solution_settings(service_user)
        if not sln_settings or not sln_settings.solution == SOLUTION_FLEX:
            return self.abort(400)

        if SolutionModule.MENU not in sln_settings.modules and SolutionModule.ORDER not in sln_settings.modules:
            return self.abort(403)

        self.response.headers['Content-Type'] = 'application/vnd.ms-excel'
        self.response.headers['Content-Disposition'] = str('attachment; filename=menu.xls')
        self.response.write(export_menu_to_excel(service_user, sln_settings))
