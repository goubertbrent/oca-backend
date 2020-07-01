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

import json
import logging

from google.appengine.api import urlfetch

from mcfw.properties import azzert
from rogerthat.settings import get_server_settings


# def add_user_group(group_id):
#     server_settings = get_server_settings()
#     if not server_settings.worker_service_url:
#         logging.error('add_user_group skipped no worker_service_url')
#         return
#     url = '{}/news/v1/group/{}'.format(server_settings.worker_service_url, group_id)
#     response = urlfetch.fetch(url, method=urlfetch.PUT, deadline=5, follow_redirects=False)
#     azzert(response.status_code == 200,
#            "Got response status code %s and response content: %s" % (response.status_code, response.content))
# 
# 
# def delete_user_group(app_id, group_id):
#     server_settings = get_server_settings()
#     if not server_settings.worker_service_url:
#         logging.error('delete_news_matches skipped no worker_service_url')
#         return
#     url = '{}/news/v1/app/{}/group/{}'.format(server_settings.worker_service_url, app_id, group_id)
#     response = urlfetch.fetch(url, method=urlfetch.DELETE, deadline=5, follow_redirects=False)
#     azzert(response.status_code == 200,
#            "Got response status code %s and response content: %s" % (response.status_code, response.content))


def create_news_matches(news_id, old_group_ids, should_create_notification=False):
    server_settings = get_server_settings()
    if not server_settings.worker_service_url:
        logging.error('create_news_matches skipped no worker_service_url')
        return
    data = {
        'news_id': news_id,
        'old_group_ids': old_group_ids,
        'should_create_notification': should_create_notification
    }
    payload = json.dumps(data)
    url = '{}/news/v1/matches/create'.format(server_settings.worker_service_url)
    response = urlfetch.fetch(url, payload=payload, method=urlfetch.PUT, deadline=5, follow_redirects=False)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))
    
    # create_matches_for_news_item


def delete_news_matches(news_id):
    server_settings = get_server_settings()
    if not server_settings.worker_service_url:
        logging.error('delete_news_matches skipped no worker_service_url')
        return
    data = {
        'news_id': news_id
    }
    payload = json.dumps(data)
    url = '{}/news/v1/matches/delete'.format(server_settings.worker_service_url, news_id)
    response = urlfetch.fetch(url, payload=payload, method=urlfetch.PUT, deadline=5, follow_redirects=False)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))
    
    # delete_news_matches


def update_service_visibility(service_identity_user, visible):
    server_settings = get_server_settings()
    if not server_settings.worker_service_url:
        logging.error('update_service_visibility skipped no worker_service_url')
        return
    data = {
        'service_identity_email': service_identity_user.email(),
        'visible': visible
    }
    payload = json.dumps(data)
    url = '{}/news/v1/service/visibility'.format(server_settings.worker_service_url)
    response = urlfetch.fetch(url, payload=payload, method=urlfetch.PUT, deadline=5, follow_redirects=False)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))
    
    # update_visibility_news_items
    # _worker_update_visibility_news_items
    # update_visibility_news_matches


def create_user_matches(app_user, group_ids):
    server_settings = get_server_settings()
    if not server_settings.worker_service_url:
        logging.error('update_news_visibility skipped no worker_service_url')
        return
    data = {
        'user_id': app_user.email(),
        'group_ids': group_ids
    }
    payload = json.dumps(data)
    url = '{}/news/v1/users/matches'.format(server_settings.worker_service_url)
    response = urlfetch.fetch(url, payload=payload, method=urlfetch.PUT, deadline=5, follow_redirects=False)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))
    
    # create_matches_for_user


# def delete_user_matches(app_user, group_id):
#     pass # delete_matches_for_user
# # '/news/v1/users/<user_id:[^/]+>/groups/<group_id:[^/]+>', 'delete'


def block_user_matches(app_user, service_identity_user, group_id):
    server_settings = get_server_settings()
    if not server_settings.worker_service_url:
        logging.error('update_news_visibility skipped no worker_service_url')
        return
    data = {
        'user_id': app_user.email(),
        'service_identity_email': service_identity_user.email(),
        'group_id': group_id
    }
    payload = json.dumps(data)
    url = '{}/news/v1/users/matches/block'.format(server_settings.worker_service_url)
    response = urlfetch.fetch(url, payload=payload, method=urlfetch.PUT, deadline=5, follow_redirects=False)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))
    
    # block_matches


def unblock_user_matches(app_user, service_identity_user, group_id):
    server_settings = get_server_settings()
    if not server_settings.worker_service_url:
        logging.error('update_news_visibility skipped no worker_service_url')
        return
    data = {
        'user_id': app_user.email(),
        'service_identity_email': service_identity_user.email(),
        'group_id': group_id
    }
    payload = json.dumps(data)
    url = '{}/news/v1/users/matches/unblock'.format(server_settings.worker_service_url)
    response = urlfetch.fetch(url, payload=payload, method=urlfetch.PUT, deadline=5, follow_redirects=False)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))
    
    # reactivate_blocked_matches
    
    
def cleanup_user(app_user):
    server_settings = get_server_settings()
    if not server_settings.worker_service_url:
        logging.error('cleanup_user skipped no worker_service_url')
        return
    data = {
        'user_id': app_user.email()
    }
    payload = json.dumps(data)
    url = '{}/news/v1/users/cleanup'.format(server_settings.worker_service_url)
    response = urlfetch.fetch(url, payload=payload, method=urlfetch.PUT, deadline=5, follow_redirects=False)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))