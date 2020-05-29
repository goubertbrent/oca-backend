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
from collections import defaultdict
from datetime import datetime
from email.MIMEText import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from os import path

import jinja2
from google.appengine.ext import ndb
from typing import List, Dict

import solutions
from rogerthat.dal.app import get_app_by_id
from rogerthat.models import App
from rogerthat.rpc import users
from rogerthat.service.api import system
from rogerthat.settings import get_server_settings
from rogerthat.utils import send_mail_via_mime
from solutions import translate, SOLUTION_COMMON
from solutions.common.dal import get_solution_settings
from solutions.common.jobs.models import JobsSettings, JobNotificationType, JobSolicitation, OcaJobOffer
from solutions.common.jobs.to import JobsSettingsTO
from solutions.common.models import SolutionSettings
from solutions.jinja_extensions import TranslateExtension

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader([path.join(path.dirname(__file__), '..', 'templates', 'emails')]),
    extensions=[TranslateExtension])


def get_jobs_settings(service_user):
    # type: (users.User) -> JobsSettings
    key = JobsSettings.create_key(service_user)
    settings = key.get()
    if not settings:
        settings = JobsSettings(key=key, emails=[], notifications=JobNotificationType.all())
    return settings


def update_jobs_settings(service_user, data):
    # type: (users.User, JobsSettingsTO) -> JobsSettings
    settings = get_jobs_settings(service_user)
    settings.notifications = data.notifications
    settings.emails = data.emails
    settings.put()
    return settings


def send_job_notifications_for_service(jobs_settings_key, min_date, max_date):
    # type: (ndb.Key, datetime, datetime) -> None
    jobs_settings = jobs_settings_key.get()  # type: JobsSettings
    if not jobs_settings.emails:
        logging.debug('No emails set, not sending jobs notifications')
        return
    service_user = users.User(jobs_settings_key.parent().id())
    solicitations = JobSolicitation.list_unseen_by_service(service_user, min_date, max_date) \
        .fetch(None)  # type: List[JobSolicitation]
    if not solicitations:
        logging.debug('No new updates for jobs from service %s', service_user)
        return
    sln_settings = get_solution_settings(jobs_settings.service_user)
    language = sln_settings.main_language

    jobs = ndb.get_multi({solicitation.job_key for solicitation in solicitations})  # type: List[OcaJobOffer]
    updates_per_job = defaultdict(int)
    for solicitation in solicitations:
        updates_per_job[solicitation.job_key.id()] += 1

    subject = _get_subject_for_update_count(language, len(jobs), len(solicitations))
    html_body, text_body = _get_body_for_job_updates(language, jobs, updates_per_job)
    _send_email_for_notification(sln_settings, jobs_settings, subject, html_body, text_body)


def _get_subject_for_update_count(lang, jobs_count, updates_count):
    # type: (unicode, int, int) -> unicode
    if jobs_count == 1:
        if updates_count == 1:
            return translate(lang, SOLUTION_COMMON, 'there_is_an_update_about_your_job')
        else:
            return translate(lang, SOLUTION_COMMON, 'there_are_some_update_about_your_job')
    else:
        return translate(lang, SOLUTION_COMMON, 'there_are_some_update_about_your_jobs')


def _get_body_for_job_updates(lang, jobs, updates_per_job):
    # type: (unicode, List[OcaJobOffer], Dict[int, int]) -> tuple[unicode, unicode]
    html_body = []
    text_body = []
    if len(jobs) == 1:
        job_name = jobs[0].function.title
        html_job_name = '<b>%s</b>' % job_name
        update_count = updates_per_job[jobs[0].id]
        if update_count == 1:
            html_body.append(translate(lang, SOLUTION_COMMON, 'jobs_one_new_update_message', job_name=html_job_name))
            text_body.append(translate(lang, SOLUTION_COMMON, 'jobs_one_new_update_message', job_name=job_name))
        else:
            html_body.append(translate(lang, SOLUTION_COMMON, 'jobs_some_updates_message', job_name=html_job_name))
            text_body.append(translate(lang, SOLUTION_COMMON, 'jobs_some_updates_message', job_name=job_name))
    else:
        msg = translate(lang, SOLUTION_COMMON, 'jobs_multiple_updates_message')
        html_body.append(msg)
        html_body.append('<ul>')
        text_body.append(msg)
        text_body.append('')
        for job in jobs:
            update_count = updates_per_job[job.id]
            if update_count == 1:
                update_line = translate(lang, SOLUTION_COMMON, 'one_new_update')
            else:
                update_line = translate(lang, SOLUTION_COMMON, 'x_new_updates', count=update_count)
            html_body.append('<li><b>%s:</b> %s</li>' % (job.function.title, update_line))
            text_body.append('* %s: %s' % (job.function.title, update_line))
        html_body.append('</ul>')
    return '<br>'.join(html_body), '\n'.join(text_body)


def _send_email_for_notification(sln_settings, jobs_settings, subject, html_body, text_body):
    # type: (SolutionSettings, JobsSettings, unicode, unicode, unicode) -> None

    def transl(key, **params):
        return translate(sln_settings.main_language, SOLUTION_COMMON, key, **params)

    settings = get_server_settings()

    with users.set_user(jobs_settings.service_user):
        si = system.get_identity()

    app = get_app_by_id(si.app_ids[0])

    mime_root = MIMEMultipart('related')
    mime_root['Subject'] = subject
    if app.type == App.APP_TYPE_ROGERTHAT:
        mime_root['From'] = settings.senderEmail
    else:
        mime_root['From'] = '%s <%s>' % (app.name, app.dashboard_email_address)
    mime_root['To'] = ', '.join(jobs_settings.emails)

    mime = MIMEMultipart('alternative')
    mime_root.attach(mime)

    button_css = 'display: inline-block; margin-left: 0.5em; margin-right: 0.5em; -webkit-border-radius: 6px;' \
                 ' -moz-border-radius: 6px; border-radius: 6px; font-family: Arial; color: #ffffff; font-size: 14px;' \
                 ' background: #3abb9e; padding: 8px 16px 8px 16px; text-decoration: none;'
    signin_url = settings.get_signin_url(app.app_id)
    if sln_settings.login:
        signin_url += '?email=%s' % sln_settings.login.email()
    btn = u'<a href="%(signin_url)s" style="%(button_css)s">%(dashboard)s</a>' % {
        'signin_url': signin_url,
        'button_css': button_css,
        'dashboard': transl('dashboard')
    }
    action_text = transl('if-email-body-3-button', dashboard_button=btn)

    footer_text = transl('jobs_notification_footer', service_name=sln_settings.name, app_name=app.name,
                         dashboard_url='%s (%s)' % (transl('dashboard').lower(), signin_url))
    footer_html = transl('jobs_notification_footer', service_name=sln_settings.name, app_name=app.name,
                         dashboard_url='<a href="%s">%s</a>' % (signin_url, transl('dashboard').lower()))

    html_params = {
        'message': html_body,
        'action_text': action_text,
        'footer': footer_html.replace('\n', '<br>'),
    }

    url_txt = transl('if-email-body-3-url', dashboard_url=signin_url)
    text_params = {
        'message': text_body,
        'url_text': url_txt,
        'footer': footer_text,
    }
    body_html = JINJA_ENVIRONMENT.get_template('solicitation_message_html.tmpl').render(html_params)
    body = JINJA_ENVIRONMENT.get_template('solicitation_message.tmpl').render(text_params)

    mime.attach(MIMEText(body.encode('utf-8'), 'plain', 'utf-8'))
    mime.attach(MIMEText(body_html.encode('utf-8'), 'html', 'utf-8'))

    with open(path.join(path.dirname(solutions.__file__), 'common', 'templates', 'emails', 'oca-email-header.png'), 'r') as f:
        img_data = f.read()

    img = MIMEImage(img_data, 'png')
    img.add_header('Content-Id', '<osa-footer>')
    img.add_header('Content-Disposition', 'inline', filename='Onze Stad App footer')
    mime_root.attach(img)

    send_mail_via_mime(settings.senderEmail, sln_settings.inbox_mail_forwarders, mime_root)
