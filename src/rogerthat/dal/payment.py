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

from google.appengine.ext import ndb
from mcfw.rpc import returns, arguments
from rogerthat.models.payment import PaymentUser, PaymentProvider, PaymentService
from rogerthat.rpc import users


@returns([PaymentProvider])
@arguments()
def get_payment_providers():
    return PaymentProvider.query().fetch(None)


@returns(ndb.Key)
@arguments(provider_id=unicode)
def get_payment_provider_key(provider_id):
    return PaymentProvider.create_key(provider_id)


@returns(PaymentProvider)
@arguments(provider_id=unicode)
def get_payment_provider(provider_id):
    """
    Returns:
        PaymentProvider
    """
    return get_payment_provider_key(provider_id).get()

@returns(ndb.Key)
@arguments(app_user=users.User)
def get_payment_user_key(app_user):
    return PaymentUser.create_key(app_user)


@returns(PaymentUser)
@arguments(app_user=users.User)
def get_payment_user(app_user):
    """
    Args:
        app_user (users.User)
    Returns:
        PaymentUser
    """
    return get_payment_user_key(app_user).get()


@returns(ndb.Key)
@arguments(service_identity_user=users.User)
def get_payment_service_key(service_identity_user):
    return PaymentService.create_key(service_identity_user)


@returns(PaymentService)
@arguments(service_identity_user=users.User)
def get_payment_service(service_identity_user):
    """
    Args:
        service_identity_user (users.User)
    Returns:
        PaymentService
    """
    return get_payment_service_key(service_identity_user).get()
