import logging

from google.appengine.ext import deferred, db

from rogerthat.bizz.job import run_job
from rogerthat.consts import SCHEDULED_QUEUE
from rogerthat.utils import now

from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import timezone_offset
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionScheduledBroadcast
from solutions.common.bizz.messaging import _send_scheduled_broadcast
from solutions.common.bizz.news import post_to_social_media_scheduled


def _all_broadcast():
    return SolutionScheduledBroadcast.all(keys_only=True)


def _reschedule_broadcast_message(ssb):
    service_user = ssb.service_user
    sln_settings = get_solution_settings(service_user)
    countdown = (ssb.broadcast_epoch + timezone_offset(sln_settings.timezone)) - now()
    if countdown >= 0:
        logging.debug('Rescheduling of broadcast message, was scheduled at: %d', countdown)
        deferred.defer(_send_scheduled_broadcast, service_user, ssb.key_str,
                       _countdown=countdown, _queue=SCHEDULED_QUEUE,
                       _transactional=db.is_in_transaction())


def _reschedule_post_to_social_media(ssb):
    countdown = ssb.timestamp - now()
    if countdown >= 0:
        logging.debug('Rescheduling of post to social media, was scheduled at: %d', countdown)
        deferred.defer(post_to_social_media_scheduled, ssb.key_str,
                       _countdown=countdown, _queue=SCHEDULED_QUEUE,
                       _transactional=db.is_in_transaction())


def job():
    run_job(_all_broadcast, [], _reschedule, [])


def _reschedule(ssb_key):

    def trans():
        ssb = db.get(ssb_key)
        if ssb.broadcast_on_facebook or ssb.broadcast_on_twitter:
            _reschedule_post_to_social_media(ssb)
        else:
            _reschedule_broadcast_message(ssb)

    db.run_in_transaction(trans)
