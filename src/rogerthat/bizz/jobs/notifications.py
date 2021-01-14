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

import base64
import logging
from datetime import datetime

import pytz
from dateutil.relativedelta import relativedelta
from google.appengine.ext import ndb, db, deferred

from rogerthat.bizz.job import run_job
from rogerthat.bizz.news import create_notification_response_handler
from rogerthat.capi.news import createNotification
from rogerthat.consts import JOBS_NOTIFICATIONS_QUEUE, JOBS_WORKER_QUEUE, \
    JOBS_CONTROLLER_QUEUE
from rogerthat.dal.mobile import get_mobile_key_by_account
from rogerthat.dal.profile import get_user_profile
from rogerthat.models.jobs import JobMatchingCriteria, JobMatchingNotifications, \
    JobOffer, JobNotificationSchedule
from rogerthat.rpc import users
from rogerthat.rpc.rpc import CAPI_KEYWORD_ARG_PRIORITY, PRIORITY_HIGH, logError, \
    CAPI_KEYWORD_ARG_APPLE_PUSH_MESSAGE, CAPI_KEYWORD_PUSH_DATA
from rogerthat.to.jobs import JobOfferTO
from rogerthat.to.news import CreateNotificationRequestTO
from rogerthat.to.push import NewJobsNotification
from rogerthat.translations import localize
from rogerthat.utils import get_epoch_from_datetime, now
from rogerthat.utils.iOS import construct_push_notification


def calculate_next_reminder(app_user, should_clear=False):
    job_notifications_key = JobMatchingNotifications.create_key(app_user)
    criteria_key = JobMatchingCriteria.create_key(app_user)
    job_notifications, job_criteria = ndb.get_multi([job_notifications_key, criteria_key])
    if not job_notifications:
        job_notifications = JobMatchingNotifications(key=job_notifications_key)
    _calculate_next_reminder(job_criteria, job_notifications, should_clear)


def _calculate_next_reminder(job_criteria, job_notifications, should_clear=False, skip_today=False):
    # type: (JobMatchingCriteria, JobMatchingNotifications, bool, bool) -> None
    if should_clear:
        job_notifications.job_ids = []

    if not job_criteria.should_send_notifications:
        job_notifications.schedule_time = 0
    elif job_criteria.notifications.how_often in (JobNotificationSchedule.AT_MOST_ONCE_A_DAY,
                                                  JobNotificationSchedule.AT_MOST_ONCE_A_WEEK):
        dt_with_tz_now = datetime.now(tz=pytz.timezone(job_criteria.notifications.timezone))
        if skip_today:
            dt_with_tz_now = dt_with_tz_now + relativedelta(days=1)
        dt_with_tz = dt_with_tz_now.replace(hour=0, minute=0, second=0, microsecond=0)
        dt_with_tz = dt_with_tz + relativedelta(seconds=job_criteria.notifications.delivery_time)
        if dt_with_tz_now >= dt_with_tz:
            dt_with_tz = dt_with_tz + relativedelta(days=1)
        if job_criteria.notifications.how_often == JobNotificationSchedule.AT_MOST_ONCE_A_WEEK:
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            weekday = days.index(job_criteria.notifications.delivery_day)
            if weekday != dt_with_tz.weekday() or dt_with_tz_now >= dt_with_tz:
                days_ahead = weekday - dt_with_tz.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                dt_with_tz = dt_with_tz + relativedelta(days=days_ahead)

        logging.info('reminder date: %s', dt_with_tz)
        dt_without_tz = datetime(dt_with_tz.year, dt_with_tz.month, dt_with_tz.day, dt_with_tz.hour,
                                 dt_with_tz.minute, dt_with_tz.second)
        time_epoch = get_epoch_from_datetime(dt_without_tz)
        time_diff = int((dt_with_tz - pytz.UTC.localize(dt_without_tz)).total_seconds())
        job_notifications.schedule_time = time_epoch + time_diff
    elif job_criteria.notifications.how_often == JobNotificationSchedule.AS_IT_HAPPENS:
        if len(job_notifications.job_ids) > 0:
            # In 30 minutes
            job_notifications.schedule_time = now() + 30 * 60
        else:
            job_notifications.schedule_time = 0

    job_notifications.put()


def schedule_reminders():
    schedule_time = now() + 20 * 60
    run_job(schedule_reminders_query, [schedule_time], schedule_reminders_worker, [schedule_time],
            worker_queue=JOBS_WORKER_QUEUE, controller_queue=JOBS_CONTROLLER_QUEUE)


def schedule_reminders_query(schedule_time):
    return JobMatchingNotifications.list_scheduled(schedule_time)


def schedule_reminders_worker(key, schedule_time):
    app_user = users.User(key.parent().id())
    job_notifications, criteria = ndb.get_multi([key, JobMatchingCriteria.create_key(app_user)])
    if job_notifications.schedule_time >= schedule_time:
        # schedule_time changed due to a job being created, don't do anything
        logging.debug('Skipping reminder %s >= %s', job_notifications.schedule_time, schedule_time)
        return

    count = len(job_notifications.job_ids)
    if count > 0:
        seconds_before = job_notifications.schedule_time - now()
        if seconds_before < 0:
            seconds_before = 0
        logging.debug('Scheduling reminder message in %d seconds', seconds_before)
        deferred.defer(send_new_jobs_notification, job_notifications.app_user, count,
                       job_notifications.job_ids[0] if count == 1 else None,
                       _countdown=seconds_before, _queue=JOBS_NOTIFICATIONS_QUEUE)
    _calculate_next_reminder(criteria, job_notifications, True, True)


def send_new_jobs_notification(app_user, count, job_id):
    if job_id:
        user_profile = get_user_profile(app_user)
        job_offer = JobOffer.get_by_id(job_id)
        timestamp = now()
        job_offer_to = JobOfferTO.from_job_offer(job_offer, timestamp, user_profile.language, [])
    else:
        job_offer_to = None
    _send_new_job_notification(app_user, count, job_offer_to)



def _send_new_job_notification(app_user, count, item):
    # type: (users.User, int, JobOfferTO) -> None
    user_profile = get_user_profile(app_user)
    if not user_profile.get_mobiles():
        return

    mobiles = db.get([get_mobile_key_by_account(mobile_detail.account) for mobile_detail in user_profile.get_mobiles().values()])
    for mobile in mobiles:
        kwargs = {}
        if item:
            title = localize(user_profile.language, 'New job match')
            message = item.function.title
        else:
            title = localize(user_profile.language, 'New job matches')
            message = localize(user_profile.language, '%(count)s new matches', count=count)
        if mobile.is_ios and mobile.iOSPushId:
            kwargs[CAPI_KEYWORD_ARG_PRIORITY] = PRIORITY_HIGH
            args = {'job_ids': [item.job_id] if item else []}
            kwargs[CAPI_KEYWORD_ARG_APPLE_PUSH_MESSAGE] = base64.encodestring(
                create_push_notification(title, message, args))
        elif mobile.is_android:
            kwargs[CAPI_KEYWORD_PUSH_DATA] = NewJobsNotification(title, message, [item.job_id] if item else [])
        createNotification(create_notification_response_handler, logError, app_user,
                           request=CreateNotificationRequestTO(), MOBILE_ACCOUNT=mobile, **kwargs)


def create_push_notification(title, message, args):
    # type: (str, int, dict) -> dict
    from rogerthat.bizz.messaging import _ellipsize_for_json, _len_for_json
    smaller_args = lambda args, too_big: [title, _ellipsize_for_json(args[1], _len_for_json(args[1]) - too_big)]
    return construct_push_notification('NM', [title, message], 'n.aiff', smaller_args, **args)
