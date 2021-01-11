# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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

from google.appengine.api import users as gusers
from google.appengine.ext import ndb

from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.utils import now, send_mail
from shop.models import Customer
from solutions.common.dal import get_solution_settings
from solutions.common.q_and_a.models import QuestionReply, Question, QuestionStatus


@rest('/internal/shop/rest/question/title', 'post')
@returns()
@arguments(question_id=(int, long), title=unicode)
def set_question_title(question_id, title):
    question = Question.get_by_id(question_id)
    question.title = title
    question.put()


@rest('/internal/shop/rest/question/modules', 'post')
@returns()
@arguments(question_id=(int, long), modules=[unicode])
def set_question_modules(question_id, modules):
    question = Question.get_by_id(question_id)
    question.modules = modules
    question.put()


@rest('/internal/shop/rest/question/status', 'post')
@returns()
@arguments(question_id=(int, long), status=(int, long))
def set_question_status(question_id, status):
    question = Question.get_by_id(question_id)
    question.status = status
    question.put()


@rest('/internal/shop/rest/question/reply', 'post')
@returns()
@arguments(question_id=(int, long), description=unicode, author_name=unicode, close=bool)
def send_reply(question_id, description, author_name, close=False):
    question = Question.get_by_id(question_id)
    settings = get_server_settings()

    if close:
        question.status = QuestionStatus.RESOLVED
    else:
        question.status = QuestionStatus.WAITING_FOR_REPLY

    qr = QuestionReply(parent=question.key)
    qr.author = gusers.get_current_user()
    qr.timestamp = now()
    qr.description = description
    qr.author_role = QuestionReply.ROLE_STAFF
    qr.author_name = author_name
    qr.visible = True

    ndb.put_multi([question, qr])
    to_email = question.author.email()
    customer = Customer.get_by_service_email(question.author.email())
    if customer:
        to_email = customer.user_email

    service_user = users.User(question.author.email())
    sln_settings = get_solution_settings(service_user)
    subject = "RE: %s" % question.title
    message = """Dear,

please login on %s to see the reply for your question titled '%s'.

Kind regards,

The Rogerthat team.""" % (sln_settings.login.email() if sln_settings.login else question.author.email(), question.title)
    send_mail(settings.senderEmail, to_email, subject, message)
