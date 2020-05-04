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
import json
import logging

from google.appengine.ext import ndb
from google.appengine.ext.deferred import deferred
from typing import List, Optional

from rogerthat.consts import MC_RESERVED_TAG_PREFIX
from rogerthat.models import NdbUserProfile, Message
from rogerthat.models.jobs import JobOffer, JobMatch, JobOfferSourceType
from rogerthat.rpc import users
from rogerthat.service.api import messaging
from rogerthat.to.jobs import CreateJobChatRequestTO
from rogerthat.to.messaging import MemberTO, AttachmentTO, AnswerTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import try_or_defer, date_to_iso_format
from rogerthat.utils.app import get_app_user_tuple
from solutions import translate, SOLUTION_COMMON
from solutions.common.dal import get_solution_settings
from solutions.common.jobs.models import JobSolicitation, JobSolicitationMessage, JobSolicitationStatus, OcaJobOffer, \
    JobsSettings, JobNotificationType, JobOfferStatistics
from solutions.common.jobs.notifications import _send_email_for_notification
from solutions.common.jobs.to import JobSolicitationTO, JobUserInfoTO, JobOfferStatisticsTO
from solutions.common.utils import send_client_action


def get_solicitations(service_user, job_id):
    # type: (users.User, int) -> List[JobSolicitationTO]
    lang = get_solution_settings(service_user).main_language
    solicitations = JobSolicitation.list_by_job(service_user, job_id).fetch()  # type: List[JobSolicitation]
    keys = []
    for solicitation in solicitations:
        if not solicitation.anonymous:
            keys.append(NdbUserProfile.createKey(users.User(solicitation.user_id)))
        keys.append(solicitation.last_message_key)
    models = {model.key: model for model in ndb.get_multi(keys)}
    results = []
    for solicitation in solicitations:
        message = models[solicitation.last_message_key]
        app_user = solicitation.app_user
        user_profile = models.get(NdbUserProfile.createKey(app_user))  # type: Optional[NdbUserProfile]
        info = JobUserInfoTO()
        if user_profile:
            info.name = user_profile.name
            info.email = user_profile.user.email().decode('utf-8')
            info.avatar_url = user_profile.avatarUrl
        else:
            info.name = translate(lang, SOLUTION_COMMON, 'anonymous_user')
        results.append(JobSolicitationTO.from_model(solicitation, message, info))
    return results


def get_solicitation_messages(service_user, job_id, solicitation_id):
    # type: (users.User, int, int) -> List[JobSolicitationMessage]
    # Side effect: fetching the messages marks this conversation as 'read'
    stats = JobOfferStatistics.create_key(service_user, job_id).get()  # type: JobOfferStatistics
    changed = stats.remove_unread(JobSolicitation.create_key(service_user, job_id, solicitation_id))
    if changed:
        stats.put()
    return JobSolicitationMessage.list_by_solicitation(service_user, job_id, solicitation_id)


@ndb.transactional()
def send_solicitation_message(service_user, job_id, solicitation_id, message, from_service):
    # type: (users.User, int, int, str, bool) -> JobSolicitationMessage
    solicitation_key = JobSolicitation.create_key(service_user, job_id, solicitation_id)
    stats_key = JobOfferStatistics.create_key(service_user, job_id)
    solicitation, stats = ndb.get_multi([solicitation_key, stats_key])  # type: JobSolicitation, JobOfferStatistics
    if solicitation.status == JobSolicitationStatus.INITIALIZING:
        solicitation.status = JobSolicitationStatus.UNREAD
        stats.add_unread(solicitation_key)
        ndb.put_multi([solicitation, stats])
        new_message = solicitation.last_message_key.get()
    else:
        new_message = JobSolicitationMessage(parent=solicitation_key)
        new_message.reply = from_service
        new_message.message = message.strip()
        new_message.put()
        solicitation.last_message_key = new_message.key
        solicitation.status = JobSolicitationStatus.READ if new_message.reply else JobSolicitationStatus.UNREAD
        to_put = [solicitation]
        if new_message.reply:
            # Send by the service, add the message to the chat in the app
            deferred.defer(_send_message_to_chat, solicitation.service_user, users.User(solicitation.user_id),
                           solicitation.id, solicitation.chat_key, new_message.message, _transactional=True)
            stats_changed = stats.remove_unread(solicitation_key)
        else:
            stats_changed = stats.add_unread(solicitation_key)
        if stats_changed:
            to_put.append(stats)
        ndb.put_multi(to_put)
    deferred.defer(_send_new_message_to_dashboard, service_user, solicitation, new_message, stats, _transactional=True)
    return new_message


def _send_message_to_chat(service_user, app_user, solicitation_id, chat_key, message):
    # type: (users.User, users.User, int, str, str) -> None
    with users.set_user(service_user):
        messaging.send_chat_message(chat_key, message)


def _send_new_message_to_dashboard(service_user, solicitation, message, stats):
    # type: (users.User, JobSolicitation, JobSolicitationMessage, JobOfferStatistics) -> None
    action = {
        'type': '[jobs] New solicitation message received',
        'payload': {
            'jobId': message.job_key.id(),
            'solicitation': JobSolicitationTO.from_partial_model(solicitation, message).to_dict(),
            'statistics': JobOfferStatisticsTO.from_model(stats).to_dict(),
        }
    }
    send_client_action(service_user, action)


def _send_solicitation_disabled_to_dashboard(service_user, solicitation):
    # type: (users.User, JobSolicitation) -> None
    action = {
        'type': '[jobs] Solicitation updated',
        'payload': {
            'jobId': solicitation.job_key.id(),
            'solicitationId': solicitation.id,
            'solicitation': {
                'status': solicitation.status,
                'update_date': date_to_iso_format(solicitation.update_date),
                'chat_key': solicitation.chat_key,
            }
        }
    }
    send_client_action(service_user, action)


def chat_send_job_solicitation_message(service_user, parent_message_key, message_key, sender, message, answers,
                                       timestamp, tag, service_identity, attachments):
    # type: (users.User, unicode, unicode, UserDetailsTO, unicode, List[AnswerTO], int, unicode, unicode, List[AttachmentTO]) -> None
    tag_dict = json.loads(tag)
    solicitation_id = tag_dict['solicitation_id']
    job_id = tag_dict['job_id']
    send_solicitation_message(service_user, job_id, solicitation_id, message, False)


def chat_disable_solicitation(service_user, parent_message_key, member, timestamp, service_identity, tag):
    # type: (users.User, unicode, UserDetailsTO, int, unicode, unicode) -> None
    # User deleted the chat
    tag_dict = json.loads(tag)
    solicitation_id = tag_dict['solicitation_id']
    job_id = tag_dict['job_id']
    logging.debug('Removing chat for job %d, solicitation %d', job_id, solicitation_id)
    offer = JobOffer.get_by_source(JobOfferSourceType.OCA, str(job_id))  # type: JobOffer
    keys = [JobMatch.create_key(member.toAppUser(), offer.id),
            JobSolicitation.create_key(service_user, job_id, solicitation_id)]
    job_match, solicitation = ndb.get_multi(keys)  # type: JobMatch, JobSolicitation
    job_match.chat_key = None
    solicitation.status = JobSolicitationStatus.DISABLED
    solicitation.chat_key = None
    solicitation.put()
    ndb.put_multi([job_match, solicitation])
    try_or_defer(_send_solicitation_disabled_to_dashboard, service_user, solicitation)
    messaging.delete_chat(parent_message_key)


def create_job_solicitation(app_user, job_offer, request):
    # type: (users.User, JobOffer, CreateJobChatRequestTO) -> unicode
    from solutions.common.bizz.messaging import MESSAGE_TAG_CHAT_JOB_SOLICITATION
    service_user = users.User(job_offer.service_email)
    user_email = app_user.email()
    oca_job_id = long(job_offer.source.id)
    solicitation = JobSolicitation.list_by_job_and_user(service_user, oca_job_id, user_email) \
        .get()  # type: JobSolicitation
    if solicitation and solicitation.chat_key:
        return solicitation.chat_key

    solicitation = solicitation or JobSolicitation(parent=JobSolicitation.create_parent_key(service_user, oca_job_id))
    solicitation.user_id = user_email
    solicitation.anonymous = request.anonymous
    solicitation.status = JobSolicitationStatus.UNREAD
    solicitation.put()

    lang = get_solution_settings(service_user).main_language
    with users.set_user(service_user):
        alert_flags = Message.ALERT_FLAG_SILENT
        user, app_id = get_app_user_tuple(app_user)
        user_member = MemberTO()
        user_member.member = user.email()
        user_member.app_id = app_id
        user_member.alert_flags = alert_flags
        members = [user_member]
        tag = json.dumps({
            '%s.tag' % MC_RESERVED_TAG_PREFIX: MESSAGE_TAG_CHAT_JOB_SOLICITATION,
            'solicitation_id': solicitation.id,
            'job_id': oca_job_id
        })
        topic = translate(lang, SOLUTION_COMMON, 'solicitation_x', title=job_offer.info.function.title)
        chat_key = messaging.start_chat(members, topic, request.message, tag=tag, default_sticky=True,
                                        alert_flags=alert_flags, sender=app_user.email())

    first_message = JobSolicitationMessage(parent=solicitation.key)
    first_message.message = request.message
    first_message.reply = False
    first_message.put()

    solicitation.chat_key = chat_key
    solicitation.status = JobSolicitationStatus.INITIALIZING
    solicitation.last_message_key = first_message.key
    solicitation.put()
    try_or_defer(send_new_solicitation_notification, service_user, first_message.job_key)
    return chat_key


def send_new_solicitation_notification(service_user, job_key):
    # type: (users.User, ndb.Key) -> None
    jobs_settings_key = JobsSettings.create_key(service_user)
    job_offer, jobs_settings = ndb.get_multi([job_key, jobs_settings_key])  # type: OcaJobOffer, JobsSettings
    if JobNotificationType.NEW_SOLICITATION in jobs_settings.notifications:
        sln_settings = get_solution_settings(service_user)
        subject = translate(sln_settings.main_language, SOLUTION_COMMON, 'jobs_email_new_job_subject')
        text_body = translate(sln_settings.main_language, SOLUTION_COMMON, 'jobs_email_new_message_body',
                              job_offer_title=job_offer.function.title)
        html_body = translate(sln_settings.main_language, SOLUTION_COMMON, 'jobs_email_new_message_body',
                              job_offer_title='<b>%s</b>' % job_offer.function.title)
        _send_email_for_notification(sln_settings, jobs_settings, subject, html_body, text_body)
