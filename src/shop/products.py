# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

from google.appengine.ext import db

from add_1_monkey_patches import DEBUG
from mcfw.properties import azzert
from rogerthat.models import ServiceProfile
from shop.dal import get_mobicage_legal_entity
from shop.models import Product


# XXX: We really need a better method to obtain these values
MC_TELECOM_LEGAL_ENTITY_ID = 5789858167521280 if not DEBUG else 5832209105682432


def add_all_products(mobicage_entity=None):
    if mobicage_entity:
        azzert(mobicage_entity.is_mobicage)
    else:
        mobicage_entity = get_mobicage_legal_entity()
    mobicage_legal_entity_id = mobicage_entity.key().id()
    to_put = []
    to_put.append(create_beac_product(mobicage_legal_entity_id))
    to_put.append(create_demo_product(mobicage_legal_entity_id))
    to_put.append(create_kfup_product(mobicage_legal_entity_id))
    to_put.append(create_ksup_product(mobicage_legal_entity_id))
    to_put.append(create_kspp_product(mobicage_legal_entity_id))
    to_put.append(create_mssu_product(mobicage_legal_entity_id))
    to_put.append(create_ocap_product(mobicage_legal_entity_id))
    to_put.append(create_msup_product(mobicage_legal_entity_id))
    to_put.append(create_msub_product(mobicage_legal_entity_id))
    to_put.append(create_ssup_product(mobicage_legal_entity_id))
    to_put.append(create_visi_product(mobicage_legal_entity_id))
    to_put.append(create_sszp_product(mobicage_legal_entity_id))
    to_put.append(create_setu_product(mobicage_legal_entity_id))
    to_put.append(create_xtra_product(mobicage_legal_entity_id))
    to_put.append(create_xtrb_product(mobicage_legal_entity_id))
    to_put.append(create_cred_product(mobicage_legal_entity_id))
    to_put.append(create_sjup_product(mobicage_legal_entity_id))
    to_put.append(create_sgup_product(mobicage_legal_entity_id))
    to_put.append(create_sx6m_product(mobicage_legal_entity_id))
    to_put.append(create_sxdm_product(mobicage_legal_entity_id))
    to_put.append(create_posm_product(mobicage_legal_entity_id))
    to_put.append(create_csub_product(mobicage_legal_entity_id))
    to_put.append(create_csux_product(mobicage_legal_entity_id))
    to_put.append(create_loya_product(mobicage_legal_entity_id))
    to_put.append(create_lsup_product(mobicage_legal_entity_id))
    to_put.append(create_klup_product(mobicage_legal_entity_id))
    to_put.append(create_xcty_product(mobicage_legal_entity_id))
    to_put.append(create_a3ct_product(mobicage_legal_entity_id))
    to_put.append(create_ilos_product(mobicage_legal_entity_id))
    to_put.append(create_setx_product(mobicage_legal_entity_id))
    to_put.append(create_bnnr_product(mobicage_legal_entity_id))
    to_put.append(create_updi_product(mobicage_legal_entity_id))
    to_put.append(create_vsdi_product(mobicage_legal_entity_id))
    to_put.append(create_term_product(mobicage_legal_entity_id))
    to_put.append(create_otrm_product(mobicage_legal_entity_id))
    to_put.append(create_kkrt_product(mobicage_legal_entity_id))
    to_put.append(create_subx_product(mobicage_legal_entity_id))
    to_put.append(create_suby_product(mobicage_legal_entity_id))
    to_put.append(create_news_product(mobicage_legal_entity_id))
    to_put.append(create_drc_stud_product())
    to_put.append(create_drc_sb_product())
    to_put.append(create_drc_hefl_product())
    to_put.append(create_drc_corp_product())
    db.put(to_put)

"""
Dependency logic explanation:
each element in the array is a required product
| => one or more of the products need to be in the order, or in any previous order
: => the amount of the product has to be exactly the number after the colon. Set to -1 to ignore the amount.
"""


def create_ilos_product(legal_entity_id):
    p = Product(key_name='ILOS')
    p.price = 7500
    p.default_count = 1
    p.default = False
    p.possible_counts = [1]
    p.is_subscription = False
    p.is_subscription_discount = False
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_xcty_product(legal_entity_id):
    p = Product(key_name=Product.PRODUCT_EXTRA_CITY)
    p.price = 500
    p.default_count = 1
    p.default = False
    p.possible_counts = range(1, 37)
    p.is_subscription = False
    p.is_subscription_discount = False
    p.is_subscription_extension = True
    p.organization_types = []
    p.product_dependencies = ['MSUP:-1|MSSU:-1|SSUP:-1|SSZP:-1|OCAP:-1']
    p.picture_url = ""
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_a3ct_product(legal_entity_id):
    p = Product(key_name=Product.PRODUCT_ACTION_3_EXTRA_CITIES)
    p.price = 1000
    p.default_count = 1
    p.default = False
    p.possible_counts = range(1, 37)
    p.is_subscription = False
    p.is_subscription_discount = False
    p.is_subscription_extension = True
    p.organization_types = []
    p.product_dependencies = ['MSUP:-1|MSSU:-1|SSUP:-1|SSZP:-1|OCAP:-1']
    p.picture_url = ""
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_beac_product(legal_entity_id):
    p = Product(key_name=Product.PRODUCT_BEACON)
    p.price = 3500
    p.default_count = 1
    p.default = False
    p.possible_counts = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    p.is_subscription = False
    p.is_subscription_discount = False
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.picture_url = "/static/images/solutions/flex/BEACON_PRESENTATIE.jpg"
    p.legal_entity_id = legal_entity_id
    return p


def create_msub_product(legal_entity_id):
    p = Product(key_name='MSUB')
    p.price = 25000
    p.default_count = 12
    p.default = False
    p.possible_counts = [1, 12, 24, 36]
    p.is_subscription = True
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.description_translation_key = 'MSUP.description'
    p.default_comment_translation_key = 'MSSU.default_comment'
    p.legal_entity_id = legal_entity_id
    return p


def create_msup_product(legal_entity_id):
    p = Product(key_name='MSUP')
    p.price = 5000
    p.default_count = 12
    p.default = True
    p.possible_counts = [1, 12, 24, 36]
    p.is_subscription = True
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.default_comment_translation_key = 'MSSU.default_comment'
    p.legal_entity_id = legal_entity_id
    return p


def create_sx6m_product(legal_entity_id):
    p = Product(key_name='SX6M')
    p.price = 0
    p.default_count = 24
    p.default = False
    p.possible_counts = [24]
    p.is_subscription = False
    p.is_subscription_discount = True
    p.module_set = 'ALL'
    p.organization_types = []
    p.product_dependencies = ['MSUP|MSSU|SSUP|SSZP']
    p.visible = False
    p.extra_subscription_months = 6
    p.default_comment_translation_key = ''
    p.legal_entity_id = legal_entity_id
    return p


def create_sxdm_product(legal_entity_id):
    p = Product(key_name='SXDM')
    p.price = 0
    p.default_count = 36
    p.default = False
    p.possible_counts = [36]
    p.is_subscription = False
    p.is_subscription_discount = True
    p.module_set = 'ALL'
    p.organization_types = []
    p.product_dependencies = ['MSUP|MSSU|SSUP|SSZP']
    p.visible = False
    p.extra_subscription_months = 12
    p.default_comment_translation_key = ''
    p.legal_entity_id = legal_entity_id
    return p


def create_setu_product(legal_entity_id):
    p = Product(key_name='SETU')
    p.price = 7500
    p.default_count = 1
    p.default = True
    p.possible_counts = [1]
    p.is_subscription = False
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_setx_product(legal_entity_id):  # Used for the platinum subscription
    p = Product(key_name='SETX')
    p.price = 0
    p.default_count = 1
    p.default = True
    p.possible_counts = [1]
    p.is_subscription = False
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_cred_product(legal_entity_id):
    p = Product(key_name=Product.PRODUCT_ONE_TIME_CREDIT_CARD_PAYMENT_DISCOUNT)
    p.price = -1000
    p.default_count = 1
    p.default = False
    p.possible_counts = [1]
    p.is_subscription = False
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = []
    p.product_dependencies = []
    p.visible = False
    p.legal_entity_id = legal_entity_id
    return p


def create_xtra_product(legal_entity_id):
    p = Product(key_name='XTRA')
    p.price = 7500
    p.default_count = 1
    p.default = False
    p.possible_counts = range(1, 101)
    p.is_subscription = False
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_xtrb_product(legal_entity_id):
    p = Product(key_name='XTRB')
    p.price = 10000
    p.default_count = 1
    p.default = False
    p.possible_counts = range(1, 101)
    p.is_subscription = False
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = []
    p.product_dependencies = []
    p.description_translation_key = 'XTRA.description'
    p.default_comment_translation_key = 'XTRA.default_comment'
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_kfup_product(legal_entity_id):
    p = Product(key_name='KFUP')
    p.price = -1500
    p.default_count = 1
    p.default = True
    p.possible_counts = [1]
    p.is_subscription = False
    p.is_subscription_discount = True
    p.organization_types = []
    p.product_dependencies = ['MSUP']
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_ksup_product(legal_entity_id):
    p = Product(key_name='KSUP')
    p.price = -1500
    p.default_count = 24
    p.default = True
    p.possible_counts = [12, 24, 36]
    p.is_subscription = False
    p.is_subscription_discount = True
    p.organization_types = []
    p.product_dependencies = ['MSUP']
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_vsdi_product(legal_entity_id):
    p = Product(key_name='VSDI')
    p.price = -1500
    p.default_count = 12
    p.default = True
    p.possible_counts = [12, 24, 36]
    p.is_subscription = False
    p.is_subscription_discount = True
    p.organization_types = []
    p.product_dependencies = ['MSUP:-1|LSUP:-1']
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_kspp_product(legal_entity_id):
    p = Product(key_name='KSPP')
    p.price = -1500
    p.default_count = 36
    p.default = True
    p.possible_counts = [12, 24, 36]
    p.is_subscription = False
    p.is_subscription_discount = True
    p.organization_types = []
    p.product_dependencies = ['MSUP']
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_mssu_product(legal_entity_id):
    p = Product(key_name='MSSU')
    p.price = 1000
    p.default_count = 12
    p.default = False
    p.possible_counts = [12, 24, 36]
    p.is_subscription = True
    p.is_subscription_discount = False
    p.module_set = 'STATIC_MODULES'
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_ocap_product(legal_entity_id):
    p = Product(key_name=Product.PRODUCT_FREE_PRESENCE)
    p.price = 0
    p.default_count = 1
    p.default = False
    p.possible_counts = [1]
    p.is_subscription = True
    p.is_subscription_discount = False
    p.module_set = 'STATIC_MODULES'
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.default_comment_translation_key = ''
    p.legal_entity_id = legal_entity_id
    return p


def create_demo_product(legal_entity_id):
    p = Product(key_name='DEMO')
    p.price = 0
    p.default_count = 3
    p.default = False
    p.possible_counts = [3]
    p.is_subscription = True
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = []
    p.product_dependencies = []
    p.visible = False
    p.legal_entity_id = legal_entity_id
    return p


def create_ssup_product(legal_entity_id):
    p = Product(key_name='SSUP')
    p.price = 1000
    p.default_count = 12
    p.default = False
    p.possible_counts = [12, 24, 36]
    p.is_subscription = True
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = [ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT]
    p.product_dependencies = []
    p.visible = False
    p.default_comment_translation_key = 'MSSU.default_comment'
    p.legal_entity_id = legal_entity_id
    return p


def create_sjup_product(legal_entity_id):
    p = Product(key_name='SJUP')
    p.price = 0
    p.default_count = 1
    p.default = False
    p.possible_counts = [1]
    p.is_subscription = True
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = [ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT]
    p.product_dependencies = []
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_sgup_product(legal_entity_id):
    p = Product(key_name='SGUP')
    p.price = 49500
    p.default_count = 1
    p.default = False
    p.possible_counts = [1]
    p.is_subscription = False
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = [ServiceProfile.ORGANIZATION_TYPE_CITY]
    p.product_dependencies = ['CSUB:-1|MSUP:-1']
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_sszp_product(legal_entity_id):
    p = Product(key_name='SSZP')
    p.price = 1000
    p.default_count = 12
    p.default = False
    p.possible_counts = [12, 24, 36]
    p.is_subscription = True
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = [ServiceProfile.ORGANIZATION_TYPE_EMERGENCY]
    p.product_dependencies = []
    p.visible = True
    p.default_comment_translation_key = 'MSSU.default_comment'
    p.legal_entity_id = legal_entity_id
    return p


def create_visi_product(legal_entity_id):
    p = Product(key_name='VISI')
    p.price = 30
    p.default_count = 250
    p.default = False
    p.possible_counts = [250, 500, 750]
    p.is_subscription = False
    p.is_subscription_discount = False
    p.organization_types = []
    p.product_dependencies = []
    p.visible = False
    p.legal_entity_id = legal_entity_id
    return p


def create_posm_product(legal_entity_id):
    p = Product(key_name=Product.PRODUCT_FLYERS)
    p.price = 6
    p.default_count = 250  # 15 euro per 250
    p.default = False
    p.possible_counts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500]
    p.is_subscription = False
    p.is_subscription_discount = False
    p.organization_types = []
    p.product_dependencies = []
    p.visible = False
    p.picture_url = "/static/images/solutions/flex/FLYERS_PRESENTATIE.jpg"
    p.legal_entity_id = legal_entity_id
    return p


def create_csub_product(legal_entity_id):
    p = Product(key_name='CSUB')
    p.price = 0
    p.default_count = 12
    p.default = False
    p.possible_counts = [12]
    p.is_subscription = True
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = [ServiceProfile.ORGANIZATION_TYPE_CITY]
    p.product_dependencies = ['SGUP:-1']
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_csux_product(legal_entity_id):
    p = Product(key_name='CSUX')
    p.price = 0
    p.default_count = 12
    p.default = False
    p.possible_counts = [12]
    p.is_subscription = True
    p.is_subscription_discount = False
    p.module_set = 'ALL'
    p.organization_types = [ServiceProfile.ORGANIZATION_TYPE_CITY]
    p.product_dependencies = []
    p.visible = True
    p.default_comment_translation_key = 'CSUB.default_comment'
    p.legal_entity_id = legal_entity_id
    return p


def create_loya_product(legal_entity_id):
    p = Product(key_name='LOYA')
    p.price = 30000
    p.default_count = 1
    p.default = False
    p.possible_counts = [1, 2, 3, 4]
    p.is_subscription = False
    p.is_subscription_discount = False
    p.organization_types = []
    p.product_dependencies = ['MSUP:-1']
    p.visible = False
    p.legal_entity_id = legal_entity_id
    return p


def create_lsup_product(legal_entity_id):
    p = Product(key_name='LSUP')
    p.price = 60000
    p.default_count = 1
    p.default = False
    p.possible_counts = [1]
    p.is_subscription = False
    p.is_subscription_discount = True
    p.organization_types = []
    p.product_dependencies = ['MSUP:-1']
    p.visible = True
    p.extra_subscription_months = 12
    p.default_comment_translation_key = 'LOYA.default_comment'
    p.legal_entity_id = legal_entity_id
    return p


def create_klup_product(legal_entity_id):
    p = Product(key_name='KLUP')
    p.price = -18000
    p.default_count = 1
    p.default = False
    p.possible_counts = [1]
    p.is_subscription = False
    p.is_subscription_discount = False
    p.organization_types = []
    p.product_dependencies = ['LSUP', 'KSUP:-1']
    p.visible = False
    p.default_comment_translation_key = ''
    p.legal_entity_id = legal_entity_id
    return p


def create_updi_product(legal_entity_id):
    p = Product(key_name='UPDI')
    p.price = -1000
    p.default_count = 1
    p.default = False
    p.possible_counts = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    p.is_subscription = False
    p.is_subscription_discount = False
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_bnnr_product(legal_entity_id):
    p = Product(key_name=Product.PRODUCT_ROLLUP_BANNER)
    p.price = 10000
    p.default_count = 1
    p.default = False
    p.possible_counts = [1, 2, 3, 4, 5]
    p.is_subscription = False
    p.is_subscription_discount = False
    p.organization_types = [ServiceProfile.ORGANIZATION_TYPE_CITY]
    p.product_dependencies = []
    p.visible = True
    p.picture_url = "/static/images/solutions/flex/rollup_banner.jpg"
    p.legal_entity_id = legal_entity_id
    return p


def create_term_product(legal_entity_id):
    p = Product(key_name='TERM')
    p.price = 27400
    p.default_count = 1
    p.default = False
    p.possible_counts = range(1, 50)
    p.is_subscription = False
    p.is_subscription_discount = False
    p.is_subscription_extension = False
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_otrm_product(legal_entity_id):
    p = Product(key_name='OTRM')
    p.price = 19900
    p.default_count = 1
    p.default = False
    p.possible_counts = range(1, 50)
    p.is_subscription = False
    p.is_subscription_discount = False
    p.is_subscription_extension = False
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_kkrt_product(legal_entity_id):
    p = Product(key_name=Product.PRODUCT_CARDS)
    p.price = 1750
    p.default_count = 2
    p.default = False
    p.possible_counts = range(1, 6)
    p.is_subscription = False
    p.is_subscription_extension = False
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.picture_url = "/static/images/solutions/flex/loyalty_cards.jpg"
    p.legal_entity_id = legal_entity_id
    return p


def create_subx_product(legal_entity_id):
    p = Product(key_name='SUBX')
    p.price = 60000
    p.default_count = 1
    p.default = False
    p.possible_counts = [1]
    p.is_subscription = False
    p.is_subscription_extension = True
    p.extra_subscription_months = 12
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.legal_entity_id = legal_entity_id
    return p


def create_suby_product(legal_entity_id):
    p = Product(key_name='SUBY')
    p.price = 12000
    p.default_count = 1
    p.default = False
    p.possible_counts = [1]
    p.is_subscription = False
    p.is_subscription_extension = True
    p.extra_subscription_months = 12
    p.organization_types = []
    p.product_dependencies = []
    p.visible = True
    p.legal_entity_id = legal_entity_id
    p.default_comment_translation_key = u'SUBX.default_comment'
    return p


def create_news_product(legal_entity_id):
    p = Product(key_name=Product.PRODUCT_NEWS_PROMOTION)
    p.price = 5000
    p.default_count = 1
    p.default = False
    p.possible_counts = [2, 4, 7]
    p.is_subscription = False
    p.organization_types = []
    p.product_dependencies = []
    p.visible = False  # Only orderable via dashboard when creating a newsfeed item
    p.legal_entity_id = legal_entity_id
    return p


################################################# MC TELECOM PRODUCTS #################################################

def create_drc_stud_product():
    p = Product(key_name='DRC_STUD')
    p.price = 1000
    p.default_count = 1
    p.possible_counts = [1, 12]
    p.is_subscription = True
    p.visible = True
    p.organization_types = []
    p.module_set = 'ALL'
    p.legal_entity_id = MC_TELECOM_LEGAL_ENTITY_ID
    p.is_multilanguage = False
    p.default_comment_translation_key = u'Abonnement mensuel Ville Connect\xe9e pour \xe9tudiants'
    p.description_translation_key = u'Abonnement Ville Connect\xe9e pour \xe9tudiants'
    return p


def create_drc_hefl_product():
    p = Product(key_name='DRC_HEFL')
    p.price = 2000
    p.default_count = 1
    p.possible_counts = [1, 12]
    p.is_subscription = True
    p.visible = True
    p.organization_types = []
    p.module_set = 'ALL'
    p.legal_entity_id = MC_TELECOM_LEGAL_ENTITY_ID
    p.is_multilanguage = False
    p.default_comment_translation_key = u'Abonnement mensuel Ville Connect\xe9e pour les entreprises travaillant \xe0 domicile, entrepreneur ou pigistes'
    p.description_translation_key = u'Abonnement pour les entreprises travaillant \xe0 domicile, entrepreneur ou pigistes'
    return p


def create_drc_sb_product():
    p = Product(key_name='DRC_SB')
    p.price = 3000
    p.default_count = 1
    p.possible_counts = [1, 12]
    p.is_subscription = True
    p.visible = True
    p.organization_types = []
    p.module_set = 'ALL'
    p.legal_entity_id = MC_TELECOM_LEGAL_ENTITY_ID
    p.is_multilanguage = False
    p.default_comment_translation_key = u'Abonnement mensuel Ville Connect\xe9e pour les petites entreprises'
    p.description_translation_key = u'Abonnement pour les petites entreprises'
    return p


def create_drc_corp_product():
    p = Product(key_name='DRC_CORP')
    p.price = 4166
    p.default_count = 12
    p.possible_counts = [12]
    p.is_subscription = True
    p.visible = True
    p.organization_types = []
    p.module_set = 'ALL'
    p.legal_entity_id = MC_TELECOM_LEGAL_ENTITY_ID
    p.is_multilanguage = False
    p.default_comment_translation_key = u'Abonnement annuel Ville Connect\xe9e pour les entreprises'
    p.description_translation_key = u'Abonnement Ville Connect\xe9e pour entreprises'
    return p
