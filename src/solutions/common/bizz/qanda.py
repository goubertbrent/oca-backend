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

from rogerthat.utils import bizz_check
from google.appengine.api import search
from google.appengine.ext import db
from mcfw.rpc import returns, arguments
from mcfw.utils import normalize_search_string
from solutions.common.models.qanda import Question


QUESTION_INDEX = 'QUESTION_INDEX'

@returns(tuple)
@arguments(language=unicode, search_string=unicode, count=(int, long), cursor=unicode)
def search_question(language, search_string, count, cursor):
    question_index = search.Index(name=QUESTION_INDEX)

    query = search.Query(query_string='%s question_language:%s' % (normalize_search_string(search_string), language),
                         options=search.QueryOptions(limit=count,
                                                     cursor=search.Cursor(cursor)))

    search_result = question_index.search(query)
    cursor = search_result.cursor.web_safe_string if search_result.cursor else None
    return Question.get([result.doc_id for result in search_result.results]), cursor

@returns()
@arguments(question_key=db.Key)
def re_index_question(question_key):
    question_index = search.Index(name=QUESTION_INDEX)

    # cleanup any previous index entry
    try:
        question_index.delete([str(question_key)])
    except ValueError:
        pass  # no index found for this customer yet

    # re-add index
    question = Question.get(question_key)
    bizz_check(question)

    fields = [search.AtomField(name='question_key', value=str(question_key)),
              search.TextField(name='question_language', value=question.language),
              search.TextField(name='question_title', value=question.title),
              search.TextField(name='question_description', value=question.description),
              search.TextField(name='question_tags', value=" ".join(question.modules)),
              ]

    for qr in question.replies(False):
        question_reply_id = qr.id
        fields.extend([search.TextField(name='question_reply_description_%s' % question_reply_id, value=qr.description),
                       ])

    question_index.put(search.Document(doc_id=str(question_key), fields=fields))
