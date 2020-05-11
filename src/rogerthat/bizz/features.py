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

from functools import total_ordering

from google.appengine.ext import db

from mcfw.consts import MISSING
from mcfw.properties import long_property, typed_property
from mcfw.rpc import returns, arguments
from mcfw.utils import Enum
from rogerthat.dal.mobile import get_mobile_settings_cached
from rogerthat.rpc.models import Mobile


@total_ordering  # @total_ordering uses __lt__ and __eq__ to create __gt__, __ge__, __le__ and __ne__
class Version(object):
    major = long_property('1')  # actually minor
    minor = long_property('2')  # actually patch

    def __init__(self, major=MISSING, minor=MISSING):
        if major is not MISSING:
            self.major = major
        if minor is not MISSING:
            self.minor = minor

    def __eq__(self, other):
        return (self.major, self.minor) == (other.major, other.minor)

    def __lt__(self, other):
        return (self.major, self.minor) < (other.major, other.minor)

    def __str__(self):
        return '%s.%s' % (self.major, self.minor)

    __repr__ = __str__


class Feature(object):
    ios = typed_property('1', Version)
    android = typed_property('2', Version)

    def __init__(self, ios=MISSING, android=MISSING):
        if ios is not MISSING:
            self.ios = ios
        if android is not MISSING:
            self.android = android


class Features(Enum):
    FRIEND_SET = Feature(ios=Version(0, 162), android=Version(0, 1003))
    BROADCAST_VIA_FLOW_CODE = Feature(ios=Version(0, 765), android=Version(0, 1626))
    ADVANCED_ORDER = Feature(ios=Version(0, 765), android=Version(0, 1626))
    NEWS = Feature(ios=Version(0, 1334), android=Version(0, 2448))
    ASSETS = Feature(ios=Version(0, 1334), android=Version(0, 2448))
    LOOK_AND_FEEL = Feature(ios=Version(0, 1623), android=Version(0, 2680))
    SPLIT_USER_DATA = Feature(ios=Version(1, 2517), android=Version(1, 3608))
    PAYMENTS = Feature(ios=Version(1, 2637), android=Version(1, 3874))  # TODO bump to newest version
    EMBEDDED_APPS = Feature(ios=Version(1, 2637), android=Version(1, 3883))
    MULTIPLE_NEWS_FEEDS = Feature(ios=Version(1, 2697), android=Version(1, 3939))
    ASK_TOS = Feature(ios=Version(1, 2729), android=Version(1, 3989))
    FORMS = Feature(ios=Version(1, 3383), android=Version(1, 4890))
    EMBEDDED_APPS_IN_SMI = Feature(ios=Version(1, 3793), android=Version(1, 5558))


@returns(bool)
@arguments(mobile=Mobile, feature=Feature)
def mobile_supports_feature(mobile, feature):
    if mobile.is_ios:
        version = feature.ios
    elif mobile.is_android:
        version = feature.android
    else:
        return True

    @db.non_transactional
    def get_mobile_settings():
        return get_mobile_settings_cached(mobile)

    mobile_settings = get_mobile_settings()
    return Version(mobile_settings.majorVersion, mobile_settings.minorVersion) >= version


@returns(bool)
@arguments(mobiles=[Mobile], feature=Feature)
def all_mobiles_support_feature(mobiles, feature):
    return all((mobile_supports_feature(mobile, feature) for mobile in mobiles))
