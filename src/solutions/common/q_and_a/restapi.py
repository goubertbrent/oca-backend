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

from google.appengine.ext import db, ndb

from mcfw.restapi import rest
from mcfw.rpc import arguments, returns
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.to import ReturnStatusTO
from rogerthat.utils import now, send_mail
from shop.models import RegioManagerTeam
from solution_server_settings import get_solution_server_settings
from solutions import translate
from solutions.common.dal import get_solution_settings
from solutions.common.q_and_a.models import QuestionReply, Question, QuestionStatus
from solutions.common.q_and_a.to import QuestionTO, QuestionsWithCursorReturnStatusTO


@rest("/common/qanda/ask", "post")
@returns()
@arguments(title=unicode, description=unicode, modules=[unicode])
def ask_question(title, description, modules):
    solution_server_settings = get_solution_server_settings()
    default_team_id = RegioManagerTeam.get_mobicage().id

    def trans():
        sln_settings = get_solution_settings(users.get_current_user())

        Question(author=users.get_current_user(),
                 timestamp=now(),
                 title=title,
                 description=description,
                 modules=modules,
                 language=sln_settings.main_language,
                 status=QuestionStatus.NEW,
                 team_id=default_team_id).put()

        message = """Please reply to %s (%s) with the following link:
%s/internal/shop/questions

Title:
%s

Description:
%s""" % (sln_settings.login.email() if sln_settings.login else "", users.get_current_user(),
         get_server_settings().baseUrl, title, description)
        send_mail(get_server_settings().senderEmail, solution_server_settings.solution_qanda_info_receivers, title,
                  message, transactional=True)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


@rest("/common/qanda/reply", "post")
@returns(ReturnStatusTO)
@arguments(question_id=(int, long), description=unicode)
def reply_on_question(question_id, description):
    service_user = users.get_current_user()
    solution_server_settings = get_solution_server_settings()
    sln_settings = get_solution_settings(service_user)

    def trans():
        q = Question.get_by_id(question_id)
        q.status = QuestionStatus.REACTION_RECEIVED
        q.last_reply_date = datetime.now()
        q.put()
        if q:
            qr = QuestionReply(parent=q.key)
            qr.author = service_user
            qr.timestamp = now()
            qr.description = description
            qr.visible = False
            qr.put()
            message = """Please reply to %s (%s) with the following link:
%s/internal/shop/questions

Title:
%s

Description:
%s""" % (sln_settings.login.email() if sln_settings.login else "", users.get_current_user(),
         get_server_settings().baseUrl, q.title, description)
            send_mail(get_server_settings().senderEmail, solution_server_settings.solution_qanda_info_receivers,
                      q.title, message, transactional=True)

            return ReturnStatusTO.create(True, None)
        return ReturnStatusTO.create(False, translate(sln_settings.main_language, 'Could not find question'))

    return ndb.transaction(trans, xg=True)


@rest('/common/qanda/myquestions/load', 'get', read_only_access=True)
@returns(QuestionsWithCursorReturnStatusTO)
@arguments(count=(int, long), cursor=unicode)
def load_my_questions(count=10, cursor=None):
    service_user = users.get_current_user()
    start_cursor = ndb.Cursor.from_websafe_string(cursor) if cursor else None
    questions, new_cursor, _ = Question.get_my_questions(service_user, count, start_cursor)
    sln_settings = get_solution_settings(service_user)
    models = [QuestionTO.fromModel(q, sln_settings) for q in questions]
    return QuestionsWithCursorReturnStatusTO.create(True, None, models, new_cursor and new_cursor.to_websafe_string().decode('utf-8'))
