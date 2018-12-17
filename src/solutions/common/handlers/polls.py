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
import json
from rogerthat.rpc import users
from shop.handlers import PublicPageHandler
from solutions.common.models.polls import Poll


class PollResultsHandler(PublicPageHandler):

    def get(self):
        service_user = self.request.get('service_user')
        poll_id = self.request.get('poll_id')

        if not service_user or not poll_id:
            return self.abort(404)

        service_user = users.User(service_user)
        poll_id = long(poll_id)
        poll = Poll.create_key(service_user, poll_id).get()
        if not poll:
            return self.abort(404)
        self.response.out.write(
            self.render('poll_results', poll=json.dumps(poll.to_dict()))
        )
