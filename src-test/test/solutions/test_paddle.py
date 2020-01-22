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

from __future__ import unicode_literals

import oca_unittest
from solutions.common.bizz.paddle import _opening_hours_to_str
from solutions.common.to.paddle import PaddleOrganizationUnitDetails


class PaddleTest(oca_unittest.TestCase):

    def test_opening_hours_to_str(self):
        # @formatter:off
        paddle_data = {"node": {"body": "", "website": "", "fax": "", "head_of_unit": "", "last_updated": "21-09-2018 10:46:42", "title": "Gemeentehuis", "twitter": "", "telephone": "09 382 82 82", "nid": "403", "summary": "", "facebook": "", "linked_in": "", "featured_image": "", "address": {"thoroughfare": "Dorp 1", "locality": "Nazareth", "country": "BE", "name_line": "", "postal_code": "9810", "premise": ""}, "vat_number": "BE 0207.453.801", "email": "secretariaat@nazareth.be"}, "path": "organizational_units\\/403", "opening_hours": {"exceptional_opening_hours": {"start": "31-12-2020", "end": "", "description": "Oudejaar", "opening_hours": {"thursday": [{"start": "08:00", "end": "12:00", "description": ""}, {"start": "14:00", "end": "16:00", "description": "Uitzonderlijk gesloten"}], "monday": [{"start": "08:30", "end": "12:00", "description": "Enkel in de voormiddag open"}, {"start": "14:00", "end": "18:30", "description": "Uitzonderlijk gesloten"}]}}, "regular": {"tuesday": [{"start": "08:30", "end": "12:00", "description": ""}, {"start": "14:00", "end": "16:00", "description": "Enkel telefonisch"}], "thursday": [{"start": "08:30", "end": "12:00", "description": ""}, {"start": "14:00", "end": "16:00", "description": "Enkel telefonisch"}], "friday": [{"start": "08:30", "end": "12:00", "description": ""}, {"start": "14:00", "end": "16:00", "description": "Enkel telefonisch"}], "wednesday": [{"start": "08:30", "end": "12:00", "description": ""}, {"start": "14:00", "end": "16:30", "description": ""}], "monday": [{"start": "08:30", "end": "12:00", "description": ""}, {"start": "14:00", "end": "18:30", "description": ""}]}, "closing_days": [{"start": "25-12-2019", "end": "", "description": "Kerstmis"}, {"start": "26-12-2019", "end": "", "description": "2e Kerstdag"}, {"start": "01-01-2020", "end": "", "description": "Nieuwjaar"}, {"start": "13-04-2020", "end": "", "description": "Paasmaandag"}, {"start": "01-05-2020", "end": "", "description": "Dag van de Arbeid"}, {"start": "21-05-2020", "end": "22-05-2020", "description": "O.L.H. Hemelvaart + brugdag"}, {"start": "01-06-2020", "end": "", "description": "Pinkstermaandag"}, {"start": "11-07-2019", "end": "", "description": "Feest van de Vlaamse Gemeenschap"}, {"start": "21-07-2020", "end": "", "description": "Nationale feestdag"}, {"start": "15-08-2020", "end": "", "description": "O.L.V. Hemelvaart"}, {"start": "01-11-2020", "end": "", "description": "Allerheiligen"}, {"start": "11-11-2020", "end": "", "description": "Wapenstilstand"}, {"start": "25-12-2020", "end": "", "description": "Kerstdag"}, {"start": "01-01-2021", "end": "", "description": "Nieuwjaar"}]}}
        # @formatter:on

        expected = u"""maandag
08:30 - 12:00
14:00 - 18:30

dinsdag
08:30 - 12:00
14:00 - 16:00 Enkel telefonisch

woensdag
08:30 - 12:00
14:00 - 16:30

donderdag
08:30 - 12:00
14:00 - 16:00 Enkel telefonisch

vrijdag
08:30 - 12:00
14:00 - 16:00 Enkel telefonisch

Sluitingsdagen
13-04-2020 Paasmaandag
01-05-2020 Dag van de Arbeid
21-05-2020 - 22-05-2020 O.L.H. Hemelvaart + brugdag
01-06-2020 Pinkstermaandag
21-07-2020 Nationale feestdag
15-08-2020 O.L.V. Hemelvaart
01-11-2020 Allerheiligen
11-11-2020 Wapenstilstand
25-12-2020 Kerstdag
01-01-2021 Nieuwjaar

Oudejaar: 31-12-2020
maandag
08:30 - 12:00 Enkel in de voormiddag open
14:00 - 18:30 Uitzonderlijk gesloten

donderdag
08:00 - 12:00
14:00 - 16:00 Uitzonderlijk gesloten"""
        data = PaddleOrganizationUnitDetails.from_dict(paddle_data)
        result = _opening_hours_to_str('nl', data.opening_hours)
        self.assertEqual(expected, result)
