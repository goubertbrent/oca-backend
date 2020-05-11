# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

import json

from typing import List

from mcfw.properties import unicode_property, typed_property
from rogerthat.to import TO


class AndroidNotification(TO):
    CHANNEL_DEFAULT = 'default'
    CHANNEL_CHAT_MESSAGE = 'chat-message'
    CHANNEL_NEWS = 'news'
    CHANNEL_JOBS = 'jobs'
    CHANNEL_LOCATION = 'location'

    # The notification's title. If present, it will override google.firebase.fcm.v1.Notification.title.
    title = unicode_property('title')
    # The notification's body text. If present, it will override google.firebase.fcm.v1.Notification.body.
    body = unicode_property('body')
    long_body = unicode_property('long_body')
    extras = unicode_property('extras')
    """Identifier used to replace existing notifications in the notification drawer.
If not specified, each request creates a new notification.
If specified and a notification with the same tag is already being shown, the new notification replaces the
existing one in the notification drawer."""
    tag = unicode_property('tag')
    """The action associated with a user click on the notification.
If specified, an activity with a matching intent filter is launched when a user clicks on the notification."""
    click_action = unicode_property('click_action')
    """The key to the body string in the app's string resources to use to localize the body text to the user's
current localization."""
    # The notification's channel id (new in Android O)
    channel_id = unicode_property('channel_id')


# See https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#Notification
# Not using 'notification' and 'android' properties because we handle them ourselves.
class PushData(TO):
    data = typed_property('data', AndroidNotification)


def remove_markdown(text):
    from markdown import markdown

    if not isinstance(text, unicode):
        text = text.decode('utf-8')
    html = markdown(text)
    return remove_html(html)


def remove_html(html):
    from bs4 import BeautifulSoup
    return ''.join(BeautifulSoup(html, features='lxml').findAll(text=True))


class NotificationAction(object):
    NEW_MESSAGE = 'newMessage'
    OPEN_NEWS = 'openNews'
    OPEN_NEWS_STREAM = 'openNewsStream'
    OPEN_MAP = 'openMap'
    START_LOCAL_FLOW = 'startLocalFlow'
    TEST_FORM = 'testForm'
    NEW_JOBS = 'newJobs'


class NewMessageNotification(PushData):

    def __init__(self, title, body, long_body, message_key):
        super(NewMessageNotification, self).__init__(
            data=AndroidNotification(
                title=title,
                body=remove_markdown(body),
                long_body=long_body,
                click_action=NotificationAction.NEW_MESSAGE,
                tag=message_key,
                channel=AndroidNotification.CHANNEL_CHAT_MESSAGE,
                extras=json.dumps({'messageKey': message_key,
                                   'launchInfo': 'showNewMessages'}),
            )
        )


class NewNewsNotification(PushData):

    def __init__(self, sender_name, title, message, news_id, feed_name):
        # type: (str, str, str, long, str) -> None
        super(NewNewsNotification, self).__init__(
            data=AndroidNotification(
                title=sender_name,
                body=title,
                long_body=u'%s\n%s' % (title, remove_markdown(message)),
                click_action=NotificationAction.OPEN_NEWS,
                tag=u'%s' % news_id,
                channel=AndroidNotification.CHANNEL_NEWS,
                extras=json.dumps({'id': news_id,
                                   'feed_name': feed_name}),
            )
        )


class NewsStreamNotification(PushData):

    def __init__(self, sender_name, title, message, news_id, group_id, service):
        # type: (str, str, str, long, str) -> None
        super(NewsStreamNotification, self).__init__(
            data=AndroidNotification(
                title=sender_name,
                body=title,
                long_body=u'%s\n%s' % (title, '' if message is None else remove_markdown(message)),
                click_action=NotificationAction.OPEN_NEWS_STREAM,
                tag=u'%s' % (news_id or group_id),
                channel=AndroidNotification.CHANNEL_NEWS,
                extras=json.dumps({'id': news_id,
                                   'group_id': group_id,
                                   'service': service}),
            )
        )


class OpenMapNotification(PushData):

    def __init__(self, title, message, tag, filter_):
        # type: (str, str, str, str) -> None
        super(OpenMapNotification, self).__init__(
            data=AndroidNotification(
                title=title,
                body=message,
                long_body=message,
                click_action=NotificationAction.OPEN_MAP,
                tag='map-%s' % tag,
                channel=AndroidNotification.CHANNEL_LOCATION,
                extras=json.dumps({'filter': filter_, 'tag': tag}),
            )
        )


class StartLocalFlowNotification(PushData):

    def __init__(self, title, message, tag=None):
        # type: (str, str, str) -> None
        super(StartLocalFlowNotification, self).__init__(
            data=AndroidNotification(
                title=title,
                body=message,
                click_action=NotificationAction.START_LOCAL_FLOW,
                tag=tag,
                channel=AndroidNotification.CHANNEL_CHAT_MESSAGE,
            )
        )


class TestFormNotification(PushData):

    def __init__(self, title, message, form_id, version):
        # type: (str, str, int, int) -> None
        super(TestFormNotification, self).__init__(
            data=AndroidNotification(
                title=title,
                body=message,
                click_action=NotificationAction.TEST_FORM,
                tag='%s-%s' % (form_id, version),
                channel=AndroidNotification.CHANNEL_DEFAULT,
                extras=json.dumps({'form_id': form_id, 'version': version}),
            )
        )


class NewJobsNotification(PushData):

    def __init__(self, title, message, job_ids):
        # type: (str, str, List[int]) -> None
        super(NewJobsNotification, self).__init__(
            data=AndroidNotification(
                title=title,
                body=message,
                click_action=NotificationAction.NEW_JOBS,
                tag='new_jobs',
                channel=AndroidNotification.CHANNEL_JOBS,
                extras=json.dumps({'ids': job_ids}),
            )
        )
