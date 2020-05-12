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

def configure():
    from rogerthat.bizz.friends import FRIEND_INVITATION_REQUEST, REQUEST_LOCATION_SHARING, UPDATE_PROFILE, \
        INVITE_SERVICE_ADMIN, FRIEND_ACCEPT_FAILED, INVITE_FACEBOOK_FRIEND, FRIEND_SHARE_SERVICE_REQUEST
    from rogerthat.bizz.friends import ackInvitation, ackRequestLocationSharing, ack_share_service
    from rogerthat.bizz.friends import ack_invitation_by_secret_failed
    from rogerthat.bizz.job.app_broadcast import APP_BROADCAST_TAG
    from rogerthat.bizz.messaging import ackListeners
    from rogerthat.bizz.messaging import process_mfr_email_reply_rogerthat_reply, REPLY_ON_FOLLOW_UP_MESSAGE
    from rogerthat.bizz.profile import ack_facebook_invite
    from rogerthat.bizz.service import ack_service_in_trouble, SERVICE_IN_TROUBLE_TAG
    from rogerthat.bizz.service.broadcast import BROADCAST_TEST_MESSAGE_ID, ack_test_broadcast

    ackListeners[APP_BROADCAST_TAG] = ackInvitation
    ackListeners[FRIEND_INVITATION_REQUEST] = ackInvitation
    ackListeners[REQUEST_LOCATION_SHARING] = ackRequestLocationSharing
    ackListeners[FRIEND_ACCEPT_FAILED] = ack_invitation_by_secret_failed
    ackListeners[INVITE_FACEBOOK_FRIEND] = ack_facebook_invite
    ackListeners[FRIEND_SHARE_SERVICE_REQUEST] = ack_share_service
    ackListeners[SERVICE_IN_TROUBLE_TAG] = ack_service_in_trouble
    ackListeners[BROADCAST_TEST_MESSAGE_ID] = ack_test_broadcast
    ackListeners[REPLY_ON_FOLLOW_UP_MESSAGE] = process_mfr_email_reply_rogerthat_reply


configure()
