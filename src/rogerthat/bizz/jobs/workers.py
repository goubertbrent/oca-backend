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

import logging

from google.appengine.api import urlfetch

from mcfw.properties import azzert
from rogerthat.settings import get_server_settings


def create_job_offer_matches(job_id):
    server_settings = get_server_settings()
    if not server_settings.worker_service_url:
        logging.error('create_job_offer_matches skipped no worker_service_url')
        return
    url = '{}/jobs/v1/matches/{}'.format(server_settings.worker_service_url, job_id)
    response = urlfetch.fetch(url, method=urlfetch.PUT, deadline=5, follow_redirects=False)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))


def remove_job_offer_matches(job_id):
    server_settings = get_server_settings()
    if not server_settings.worker_service_url:
        logging.error('create_job_offer_matches skipped no worker_service_url')
        return
    url = '{}/jobs/v1/matches/{}'.format(server_settings.worker_service_url, job_id)
    response = urlfetch.fetch(url, method=urlfetch.DELETE, deadline=5, follow_redirects=False)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))


def re_index_job_offer(job_id):
    server_settings = get_server_settings()
    if not server_settings.worker_service_url:
        logging.error('re_index_job_offer skipped no worker_service_url')
        return
    url = '{}/jobs/v1/reindex/{}'.format(server_settings.worker_service_url, job_id)
    response = urlfetch.fetch(url, method=urlfetch.PUT, deadline=5, follow_redirects=False)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))


def create_user_matches(app_user):
    server_settings = get_server_settings()
    if not server_settings.worker_service_url:
        logging.error('create_user_matches skipped no worker_service_url')
        return
    url = '{}/jobs/v1/users/{}/matches'.format(server_settings.worker_service_url, app_user.email())
    response = urlfetch.fetch(url, method=urlfetch.PUT, deadline=5, follow_redirects=False)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))


def cleanup_jobs_data(app_user):
    server_settings = get_server_settings()
    if not server_settings.worker_service_url:
        logging.error('cleanup_jobs_data skipped no worker_service_url')
        return
    url = '{}/jobs/v1/users/{}'.format(server_settings.worker_service_url, app_user.email())
    response = urlfetch.fetch(url, method=urlfetch.DELETE, deadline=5, follow_redirects=False)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))