# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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

import datetime
import os

from google.appengine.ext import db

import oca_unittest
from rogerthat.bizz.service import create_service
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import ServiceProfile
from rogerthat.rpc import users
from rogerthat.to.service import UserDetailsTO
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import get_epoch_from_datetime
from solutions.common.bizz.reservation import availability_and_shift, STATUS_AVAILABLE, STATUS_TOO_MANY_PEOPLE, \
    cancel_reservation, move_reservation, edit_reservation
from solutions.common.models import SolutionSettings, SolutionMainBranding
from solutions.common.models.reservation import RestaurantReservation, RestaurantSettings
from solutions.common.models.reservation.properties import Shifts, Shift
from solutions.flex import SOLUTION_FLEX

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class Test(oca_unittest.TestCase):

    def _test_reserve_table(self, service_user, service_identity, user_details, date, people, name, phone, comment, force=False):
        # TODO: race conditions?
        status, shift_start = availability_and_shift(service_user, None, user_details, date, people, force)
        if status != STATUS_AVAILABLE:
            return status

        date = datetime.datetime.utcfromtimestamp(date)
        rogerthat_user = users.User(user_details[0].email) if user_details else None
        reservation = RestaurantReservation(service_user=service_user,
                                            user=rogerthat_user, name=name or "John Doe", phone=phone, date=date,
                                            people=people, comment=comment, shift_start=shift_start,
                                            creation_date=datetime.datetime.now())
        reservation.put()
        key_ = reservation.key()
        return unicode(key_), STATUS_AVAILABLE

    def test_create_restaurant_identity(self):
        self.set_datastore_hr_probability(1)

        root_proj = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')
        branding_url = os.path.join(root_proj, 'mobicage-backend', 'src-test', 'rogerthat_tests', 'mobicage', 'bizz',
                                    'nuntiuz.zip')

        email = u"resto_soluton@foo.com"
        name = u"resto_soluton"
        service_user = users.User(email)

        create_service(email=email, name=name, password=u"test1", languages=[u"en"], solution=SOLUTION_FLEX,
                       category_id=None, organization_type=ServiceProfile.ORGANIZATION_TYPE_PROFIT,
                       fail_if_exists=False)

        solutionSettings = SolutionSettings(key=SolutionSettings.create_key(service_user), name=name,
                            menu_item_color=None, address=u"lochristi", phone_number=None,
                            currency=u"EUR", main_language=DEFAULT_LANGUAGE, solution=SOLUTION_FLEX)

        settings = RestaurantSettings(key=RestaurantSettings.create_key(service_user))
        settings.language = DEFAULT_LANGUAGE

        stream = StringIO()
        stream.write(open(branding_url).read())
        stream.seek(0)

        main_branding = SolutionMainBranding(key=SolutionMainBranding.create_key(service_user))
        main_branding.blob = db.Blob(stream.read())
        main_branding.branding_key = None

        settings.shifts = Shifts()

        shift = Shift()
        shift.name = u'shift-lunch'
        shift.capacity = 50
        shift.max_group_size = 6
        shift.leap_time = 30
        shift.threshold = 70
        shift.start = 12 * 60 * 60
        shift.end = 14 * 60 * 60
        shift.days = [1, 2, 3, 4, 5, 6, 7]
        shift.comment = u'shift-comment0'
        settings.shifts.add(shift)

        shift = Shift()
        shift.name = u'shift-dinner'
        shift.capacity = 50
        shift.max_group_size = 6
        shift.leap_time = 30
        shift.threshold = 70
        shift.start = 18 * 60 * 60
        shift.end = 21 * 60 * 60
        shift.days = [1, 2, 3, 4, 5, 6, 7]
        shift.comment = u'shift-comment1'
        settings.shifts.add(shift)

        put_and_invalidate_cache(solutionSettings, settings, main_branding)

        date_ = datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=10), datetime.datetime.min.time())
        date_ = date_ + datetime.timedelta(hours=19)
        today_ = get_epoch_from_datetime(date_)
        service_identity = None

        user_detail = UserDetailsTO.fromUserProfile(get_user_profile(users.get_current_user()))

        reservationOkKey, reservationOk = \
            self._test_reserve_table(service_user, service_identity, user_details=[user_detail], date=today_, people=3,
                                     name=u"text Name", phone=None, comment=u"comment", force=False)
        reservationTooMany = self._test_reserve_table(service_user, service_identity, user_details=[user_detail],
                                                      date=today_, people=50, name=u"text Name", phone=None,
                                                      comment=u"comment", force=False)

        self.assertEqual(STATUS_AVAILABLE, reservationOk)
        self.assertEqual(STATUS_TOO_MANY_PEOPLE, reservationTooMany)

        editReservationOk = edit_reservation(service_user, reservationOkKey, people=4, comment=None, force=False)
        self.assertEqual(STATUS_AVAILABLE, editReservationOk)

        cancel_reservation(service_user, reservationOkKey, notified=False)
        move_reservation(service_user, None, reservationOkKey, u'shift-lunch')
