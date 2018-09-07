# -*- coding: utf-8 -*-
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
# @@license_version:1.4@@
from rogerthat.bizz.embedded_applications import create_embedded_application
from rogerthat.bizz.payment import create_payment_provider
from rogerthat.models.apps import EmbeddedApplicationType, EmbeddedApplicationTag
from rogerthat.to.app import CreateEmbeddedApplicationTO
from rogerthat.to.payment import PaymentProviderTO, ConversionRatioTO, ConversionRatioValueTO

TEST_PROVIDER_ID = 'payconiq'
TEST_CURRENCY = 'USD'


def setup_payment_providers():
    e = create_embedded_application(CreateEmbeddedApplicationTO(name=u'test',
                                                                file=u'base64,R0lGODlhAQABAAAAACw=',
                                                                tags=[EmbeddedApplicationTag.PAYMENTS],
                                                                url_regexes=[],
                                                                title=u'Test embedded app',
                                                                description=u'embedded app description',
                                                                types=[EmbeddedApplicationType.CHAT_PAYMENT,
                                                                       EmbeddedApplicationType.WIDGET_PAY],
                                                                ))
    obj = PaymentProviderTO(
        id=TEST_PROVIDER_ID,
        name='Payconiq',
        logo=None,
        version=1,
        description=u'Payconiq description',
        oauth_settings=None,
        background_color=None,
        text_color=None,
        button_color=None,
        black_white_logo=None,
        asset_types=[],
        currencies=[],
        settings={'a': 1},
        embedded_application=e.name,
        app_ids=[],
        conversion_ratio=ConversionRatioTO(
            base=TEST_CURRENCY,
            values=[ConversionRatioValueTO(currency='EUR', rate=.5),
                    ConversionRatioValueTO(currency='TFT', rate=0.1)]
        )
    )
    create_payment_provider(obj)
    return obj
