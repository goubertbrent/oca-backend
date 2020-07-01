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

from google.appengine.api import users

from common.mcfw.consts import REST_TYPE_TO
from common.mcfw.restapi import rest
from common.mcfw.rpc import returns, arguments
from workers.news.cleanup import cleanup_news_data
from workers.news.to import CreateMatchesTO, UpdateServiceVisibilityTO,\
    CreateUserMatchesTO, BlockUserMatchesTO, DeleteMatchesTO, CleanupUserTO


# @rest('/news/v1/group/<group_id:[^/]+>', 'put', silent=True, silent_result=True)
# @returns(dict)
# @arguments(group_id=unicode)
# def rest_add_user_group(group_id):
#     return {'group_id': group_id}
# 
# 
# @rest('/news/v1/app/<app_id:[^/]+>/group/<group_id:[^/]+>', 'delete', silent=True, silent_result=True)
# @returns(dict)
# @arguments(app_id=unicode, group_id=unicode)
# def rest_delete_user_group(app_id, group_id):
#     return {'group_id': group_id, 'app_id': app_id}
@rest('/news/v1/matches/create', 'put', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns(dict)
@arguments(data=CreateMatchesTO)
def rest_create_matches(data):
    return data.to_dict()


@rest('/news/v1/matches/delete', 'put', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns(dict)
@arguments(data=DeleteMatchesTO)
def rest_delete_matches(data):
    return data.to_dict()


@rest('/news/v1/service/visibility', 'put', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns(dict)
@arguments(data=UpdateServiceVisibilityTO)
def rest_update_visibility(data):
    return data.to_dict()


@rest('/news/v1/users/matches', 'put', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns(dict)
@arguments(data=CreateUserMatchesTO)
def rest_create_user_matches(data):
    return data.to_dict()


@rest('/news/v1/users/matches/block', 'put', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns(dict)
@arguments(data=BlockUserMatchesTO)
def rest_block_user_matches(data):
    return data.to_dict()


@rest('/news/v1/users/matches/unblock', 'put', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns(dict)
@arguments(data=BlockUserMatchesTO)
def rest_unblock_user_matches(data):
    return data.to_dict()


@rest('/news/v1/users/cleanup', 'put', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns(dict)
@arguments(data=CleanupUserTO)
def rest_cleanup_user(data):
    cleanup_news_data(users.User(data.user_id))
    return data.to_dict()