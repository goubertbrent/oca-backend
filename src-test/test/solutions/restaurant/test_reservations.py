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

import datetime
import os

from google.appengine.ext import db

from mcfw.consts import MISSING
import oca_unittest
from rogerthat.bizz.service import create_service
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import ServiceProfile
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.to.service import UserDetailsTO
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import get_epoch_from_datetime
from solutions.common.bizz.menu import get_item_image_url
from solutions.common.bizz.reservation import availability_and_shift, STATUS_AVAILABLE, STATUS_TOO_MANY_PEOPLE, \
    cancel_reservation, move_reservation, edit_reservation
from solutions.common.models import SolutionSettings, SolutionMainBranding,\
    RestaurantMenu
from solutions.common.models.reservation import RestaurantReservation, RestaurantSettings
from solutions.common.models.reservation.properties import ShiftTO
from solutions.common.to import MenuTO
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

        root_proj = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
        branding_url = os.path.join(root_proj, 'src-test', 'rogerthat_tests', 'mobicage', 'bizz',
                                    'nuntiuz.zip')

        email = u"resto_soluton@foo.com"
        name = u"resto_soluton"
        service_user = users.User(email)

        create_service(email=email, name=name, password=u"test1", languages=[u"en"], solution=SOLUTION_FLEX,
                       organization_type=ServiceProfile.ORGANIZATION_TYPE_PROFIT)

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

        settings.shifts = None
        shifts = {}
        shift = ShiftTO()
        shift.name = u'shift-lunch'
        shift.capacity = 50
        shift.max_group_size = 6
        shift.leap_time = 30
        shift.threshold = 70
        shift.start = 12 * 60 * 60
        shift.end = 14 * 60 * 60
        shift.days = [1, 2, 3, 4, 5, 6, 7]
        shift.comment = u'shift-comment0'
        shifts[shift.name] = shift

        shift = ShiftTO()
        shift.name = u'shift-dinner'
        shift.capacity = 50
        shift.max_group_size = 6
        shift.leap_time = 30
        shift.threshold = 70
        shift.start = 18 * 60 * 60
        shift.end = 21 * 60 * 60
        shift.days = [1, 2, 3, 4, 5, 6, 7]
        shift.comment = u'shift-comment1'
        shifts[shift.name] = shift
        settings.save_shifts(shifts)
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

        menu_settings = RestaurantMenu(key=RestaurantMenu.create_key(solutionSettings.service_user, solutionSettings.solution))
        menu_settings.categories_json = u'{"a46472d3-4ba6-a583-e527-7a7046a867e0":{"index":0,"name":"Tuinonderhoud","predescription":"Snoeiwerken","items":[{"name":"haag snoeien","price":3900,"custom_unit":5,"step":1,"visible_in":3,"has_price":true,"id":"c6696ba4-de8b-436d-bfa4-61628f8adee3","unit":5,"description":""}],"postdescription":null,"id":"a46472d3-4ba6-a583-e527-7a7046a867e0"}}'
        menu_settings.predescription = u'Dit is de uitleiding van jouw menu'
        menu_settings.postdescription = u'Dit is de inleiding van jouw menu'
        menu_settings.name = None
        menu_settings.is_default = False
        menu_settings.put()

        server_settings = get_server_settings()
        menu = MenuTO.fromMenuObject(RestaurantMenu.get(RestaurantMenu.create_key(solutionSettings.service_user, solutionSettings.solution)))
        for cat in menu.categories:
            cat.has_visible = False
            cat.has_visible_with_pay = False
            for item in cat.items:
                if item.image_id and item.image_id is not MISSING:
                    item.image_url = get_item_image_url(item.image_id, server_settings)
                else:
                    item.image_url = None
                self.assertEqual(None, item.image_url)
