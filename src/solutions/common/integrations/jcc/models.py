# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley NV
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
from google.appengine.ext import ndb

from mcfw.utils import Enum
from rogerthat.dal import parent_ndb_key
from rogerthat.models import NdbModel
from rogerthat.rpc import users
from typing import List


class JccApiMethod(Enum):
    GET_APPOINTMENTS = 'jcc.get_appointments'
    ADD_TO_CALENDAR = 'jcc.add_to_calendar'
    EnableSecureAppointmentLinks = 'EnableSecureAppointmentLinks'
    GetAppIdBySecureLink = 'GetAppIdBySecureLink'
    GetAppointmentFieldSettings = 'GetAppointmentFieldSettings'
    GetAppointmentFields = 'GetAppointmentFields'
    GetAppointmentQRCodeText = 'GetAppointmentQRCodeText'
    GetDayPartPeriods = 'GetDayPartPeriods'
    GetLanguages = 'GetLanguages'
    GetRequiredClientFieldsExtended = 'GetRequiredClientFieldsExtended'
    GetRequiredClientFields = 'GetRequiredClientFields'
    GetSecureLinkIdByAppId = 'GetSecureLinkIdByAppId'
    MidofficeRequest = 'MidofficeRequest'
    RequestAddAppointment = 'RequestAddAppointment'
    RequestRemoveAppointment = 'RequestRemoveAppointment'
    RequestUpdateAppointment = 'RequestUpdateAppointment'
    SendAppointmentEmail = 'SendAppointmentEmail'
    SetGovCaseIDToAppointmentID = 'SetGovCaseIDToAppointmentID'
    bookGovAppointmentExtendedDetails = 'bookGovAppointmentExtendedDetails'
    bookGovAppointment = 'bookGovAppointment'
    deleteGovAppointment = 'deleteGovAppointment'
    getGovAppointmentDetails = 'getGovAppointmentDetails'
    getGovAppointmentDuration = 'getGovAppointmentDuration'
    getGovAppointmentExtendedDetails = 'getGovAppointmentExtendedDetails'
    getGovAppointmentTimeUnit = 'getGovAppointmentTimeUnit'
    getGovAppointmentsBSN = 'getGovAppointmentsBSN'
    getGovAppointmentsByClientID = 'getGovAppointmentsByClientID'
    getGovAppointmentsCase = 'getGovAppointmentsCase'
    getGovAppointments = 'getGovAppointments'
    getGovAvailableDays = 'getGovAvailableDays'
    getGovAvailableProductsByProduct = 'getGovAvailableProductsByProduct'
    getGovAvailableProducts = 'getGovAvailableProducts'
    getGovAvailableTimesPerDay = 'getGovAvailableTimesPerDay'
    getGovLatestPlanDate = 'getGovLatestPlanDate'
    getGovLocationDetails = 'getGovLocationDetails'
    getGovLocationsForProduct = 'getGovLocationsForProduct'
    getGovLocations = 'getGovLocations'
    getGovProductDetails = 'getGovProductDetails'
    updateGovAppointmentExtendedDetails = 'updateGovAppointmentExtendedDetails'
    updateGovAppointment = 'updateGovAppointment'
    updateGovAppointmentWithFieldsExtendedDetails = 'updateGovAppointmentWithFieldsExtendedDetails'
    updateGovAppointmentWithFields = 'updateGovAppointmentWithFields'


class JCCSettings(NdbModel):
    url = ndb.StringProperty()
    enabled = ndb.BooleanProperty(default=False)

    @property
    def service_user(self):
        return users.User(self.key.parent().id())

    @classmethod
    def create_key(cls, service_user):
        return ndb.Key(cls, service_user.email(), parent=parent_ndb_key(service_user))


class JCCAppointment(NdbModel):
    id = ndb.StringProperty()
    start_date = ndb.DateTimeProperty()


class JCCUserAppointments(NdbModel):
    appointments = ndb.StructuredProperty(JCCAppointment, repeated=True)  # type: List[JCCAppointment]

    @classmethod
    def create_key(cls, service_user, app_user):
        return ndb.Key(cls,  app_user.email(), parent=parent_ndb_key(service_user))
