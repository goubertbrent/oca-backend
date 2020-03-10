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

from datetime import datetime

import oca_unittest
from rogerthat.models import OpeningHours
from rogerthat.rpc import users
from solutions.common.bizz.opening_hours import opening_hours_to_text
from solutions.common.bizz.paddle import _update_opening_hours_from_paddle
from solutions.common.to.paddle import PaddleOrganizationUnitDetails


class PaddleTest(oca_unittest.TestCase):

    def test_opening_hours_to_str(self):
        # @formatter:off
        paddle_data = {"path":"organizational_units\/403","node":{"nid":"403","title":"Gemeentehuis","last_updated":"21-09-2018 10:46:42","summary":"","body":"","featured_image":"","head_of_unit":"","twitter":"","facebook":"","linked_in":"","website":"","fax":"","telephone":"09 382 82 82","email":"secretariaat@nazareth.be","vat_number":"BE 0207.453.801","address":{"name_line":"","thoroughfare":"Dorp 1","premise":"","postal_code":"9810","locality":"Nazareth","country":"BE"}},"opening_hours":{"regular":{"monday":[{"start":"08:30","end":"12:00","description":""},{"start":"14:00","end":"18:30","description":""}],"tuesday":[{"start":"08:30","end":"12:00","description":""},{"start":"14:00","end":"16:00","description":"Enkel telefonisch"}],"wednesday":[{"start":"08:30","end":"12:00","description":""},{"start":"14:00","end":"16:30","description":""}],"thursday":[{"start":"08:30","end":"12:00","description":""},{"start":"14:00","end":"16:00","description":"Enkel telefonisch"}],"friday":[{"start":"08:30","end":"12:00","description":""},{"start":"14:00","end":"16:00","description":"Enkel telefonisch"}]},"closing_days":[{"start":"25-12-2019","end":"","description":"Kerstmis"},{"start":"26-12-2019","end":"","description":"2e Kerstdag"},{"start":"01-01-2020","end":"","description":"Nieuwjaar"},{"start":"13-04-2020","end":"","description":"Paasmaandag"},{"start":"01-05-2020","end":"","description":"Dag van de Arbeid"},{"start":"21-05-2020","end":"22-05-2020","description":"O.L.H. Hemelvaart + brugdag"},{"start":"01-06-2020","end":"","description":"Pinkstermaandag"},{"start":"11-07-2019","end":"","description":"Feest van de Vlaamse Gemeenschap"},{"start":"21-07-2020","end":"","description":"Nationale feestdag"},{"start":"15-08-2020","end":"","description":"O.L.V. Hemelvaart"},{"start":"01-11-2020","end":"","description":"Allerheiligen"},{"start":"11-11-2020","end":"","description":"Wapenstilstand"},{"start":"25-12-2020","end":"","description":"Kerstdag"},{"start":"01-01-2021","end":"","description":"Nieuwjaar"}],"exceptional_opening_hours":[{"start":"19-12-2019","end":"","description":"Uitzonderlijk gesloten vanaf 15:00","opening_hours":[]},{"start":"24-12-2019","end":"","description":"Kerstavond","opening_hours":{"tuesday":[{"start":"08:30","end":"12:00","description":"Enkel open in de voormiddag"},{"start":"14:00","end":"16:00","description":"Uitzonderlijk gesloten"}]}},{"start":"31-12-2019","end":"","description":"Oudejaar","opening_hours":{"tuesday":[{"start":"08:30","end":"12:00","description":"Enkel in de voormiddag open"},{"start":"14:00","end":"16:00","description":"Uitzonderlijk gesloten"}]}},{"start":"01-07-2020","end":"30-08-2020","description":"Zomervakantie - afwijkende openingsuren op maandag","opening_hours":{"monday":[{"start":"08:30","end":"12:00","description":""},{"start":"14:00","end":"16:30","description":""}],"tuesday":[{"start":"08:30","end":"12:00","description":""},{"start":"14:00","end":"16:00","description":"Enkel telefonisch"}],"wednesday":[{"start":"08:30","end":"12:00","description":""},{"start":"14:00","end":"16:30","description":""}],"thursday":[{"start":"08:30","end":"12:00","description":""},{"start":"14:00","end":"16:00","description":"Enkel telefonisch"}],"friday":[{"start":"08:30","end":"12:00","description":""},{"start":"14:00","end":"16:00","description":"Enkel telefonisch"}]}},{"start":"25-09-2020","end":"","description":"Uitzonderlijk  gesloten in de namiddag","opening_hours":{"friday":[{"start":"08:30","end":"12:00","description":"Enkel in de voormiddag open"},{"start":"14:00","end":"16:00","description":"Uitzonderlijk gesloten"}]}},{"start":"24-12-2020","end":"","description":"Kerstavond","opening_hours":{"monday":[{"start":"08:00","end":"12:00","description":"Enkel in de voormiddag open"},{"start":"14:00","end":"18:30","description":"Uitzonderlijk gesloten"}],"thursday":[{"start":"08:30","end":"12:00","description":""},{"start":"14:00","end":"16:00","description":"Uitzonderlijk gesloten"}]}},{"start":"31-12-2020","end":"","description":"Oudejaar","opening_hours":{"monday":[{"start":"08:30","end":"12:00","description":"Enkel in de voormiddag open"},{"start":"14:00","end":"18:30","description":"Uitzonderlijk gesloten"}],"thursday":[{"start":"08:00","end":"12:00","description":""},{"start":"14:00","end":"16:00","description":"Uitzonderlijk gesloten"}]}}]}}
        # @formatter:on

        expected = u"""maandag
08:30 — 12:00
14:00 — 18:30

dinsdag
08:30 — 12:00
14:00 — 16:00 Enkel telefonisch

woensdag
08:30 — 12:00
14:00 — 16:30

donderdag
08:30 — 12:00
14:00 — 16:00 Enkel telefonisch

vrijdag
08:30 — 12:00
14:00 — 16:00 Enkel telefonisch

Afwijkende openingstijden

25/12/19 Kerstmis — Gesloten
26/12/19 2e Kerstdag — Gesloten
31/12/19 Oudejaar
dinsdag
08:30 — 12:00 Enkel in de voormiddag open
14:00 — 16:00 Uitzonderlijk gesloten
1/01/20 Nieuwjaar — Gesloten
13/04/20 Paasmaandag — Gesloten
1/05/20 Dag van de Arbeid — Gesloten
21/05/20 — 22/05/20 O.L.H. Hemelvaart + brugdag — Gesloten
1/06/20 Pinkstermaandag — Gesloten
1/07/20 — 30/08/20 Zomervakantie - afwijkende openingsuren op maandag
maandag
08:30 — 12:00
14:00 — 16:30

dinsdag
08:30 — 12:00
14:00 — 16:00 Enkel telefonisch

woensdag
08:30 — 12:00
14:00 — 16:30

donderdag
08:30 — 12:00
14:00 — 16:00 Enkel telefonisch

vrijdag
08:30 — 12:00
14:00 — 16:00 Enkel telefonisch
21/07/20 Nationale feestdag — Gesloten
15/08/20 O.L.V. Hemelvaart — Gesloten
25/09/20 Uitzonderlijk  gesloten in de namiddag
vrijdag
08:30 — 12:00 Enkel in de voormiddag open
14:00 — 16:00 Uitzonderlijk gesloten
1/11/20 Allerheiligen — Gesloten
11/11/20 Wapenstilstand — Gesloten
24/12/20 Kerstavond
maandag
08:00 — 12:00 Enkel in de voormiddag open
14:00 — 18:30 Uitzonderlijk gesloten

donderdag
08:30 — 12:00
14:00 — 16:00 Uitzonderlijk gesloten
25/12/20 Kerstdag — Gesloten
31/12/20 Oudejaar
maandag
08:30 — 12:00 Enkel in de voormiddag open
14:00 — 18:30 Uitzonderlijk gesloten

donderdag
08:00 — 12:00
14:00 — 16:00 Uitzonderlijk gesloten
1/01/21 Nieuwjaar — Gesloten"""
        data = PaddleOrganizationUnitDetails.from_dict(paddle_data)
        opening_hours = OpeningHours(key=OpeningHours.create_key(users.User('test@example.com'), '1'),
                                     type=OpeningHours.TYPE_TEXTUAL)
        changed, hours = _update_opening_hours_from_paddle(opening_hours, data)
        result = opening_hours_to_text(hours, 'nl_BE', datetime(2019, 12, 25))
        self.assertEqual(OpeningHours.TYPE_STRUCTURED, hours.type)
        self.assertEqual(expected, result)
        self.assertEqual(True, changed)
