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
from rogerthat.consts import DEBUG

OUR_CITY_APP_COLOUR = u'5BC4BF'

UNIT_PIECE = 1
UNIT_LITER = 2
UNIT_KG = 3
UNIT_GRAM = 4
UNIT_HOUR = 5
UNIT_MINUTE = 6
UNIT_DAY = 7
UNIT_PERSON = 8
UNIT_SESSION = 9
UNIT_PLATTER = 10
UNIT_WEEK = 11
UNIT_MONTH = 12
# values are the translation keys
UNITS = {
    UNIT_PIECE: 'piece',
    UNIT_LITER: 'liter',
    UNIT_KG: 'kilogram',
    UNIT_GRAM: 'gram',
    UNIT_HOUR: 'hour',
    UNIT_MINUTE: 'minute',
    UNIT_DAY: 'day',
    UNIT_WEEK: 'week',
    UNIT_MONTH: 'month',
    UNIT_PERSON: 'person',
    UNIT_SESSION: 'session',
    UNIT_PLATTER: 'platter'
}

# values are translation keys except for the official symbols (liter, kg, gram, ..)
UNIT_SYMBOLS = {
    UNIT_PIECE: 'piece_short',
    UNIT_LITER: 'l',
    UNIT_KG: 'kg',
    UNIT_GRAM: 'g',
    UNIT_HOUR: 'h',
    UNIT_MINUTE: 'min',
    UNIT_DAY: 'day_short',
    UNIT_WEEK: 'week_short',
    UNIT_MONTH: 'month_short',
    UNIT_PERSON: 'person_short',
    UNIT_SESSION: 'session',
    UNIT_PLATTER: 'platter'
}

ORDER_TYPE_SIMPLE = 1
ORDER_TYPE_ADVANCED = 2

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = 3600
SECONDS_IN_DAY = 86400
SECONDS_IN_WEEK = 604800

CURRENCIES = ['EUR', 'USD', 'GBP', 'RON', 'ZAR']
CURRENCY_NAMES = {
    'RON': u'Leu',
}

OCA_FILES_BUCKET = 'oca-files'
OCA_DEV_BUCKET = 'rt-dev-debug'


def get_files_bucket():
    return OCA_DEV_BUCKET if DEBUG else OCA_FILES_BUCKET


AUTO_PUBLISH_MINUTES = 15


def get_currency_name(locale, currency_symbol):
    name = locale.currencies.get(currency_symbol)
    return name or CURRENCY_NAMES.get(currency_symbol, currency_symbol)


# Translations used on the web clients with a prefix
TRANSLATION_MAPPING = {
    'oca': {
        'Add new',
        'Alert',
        'All',
        'Attachment',
        'Broadcast',
        'Cancel',
        'Change logo',
        'Close',
        'Confirm',
        'Content',
        'Currency',
        'Date',
        'Edit',
        'Email',
        'Enabled',
        'Error',
        'Icon',
        'Label',
        'Load more',
        'Logo',
        'Maximum',
        'Minimum',
        'Next',
        'No',
        'Optional',
        'PDF',
        'Phone number',
        'Remove',
        'Retry',
        'RSS imports',
        'Save',
        'Search',
        'Settings',
        'Time',
        'Type',
        'Url',
        'View',
        'Website',
        'Yes',
        'action',
        'action_button',
        'active',
        'add-attachment',
        'address',
        'age',
        'age-max',
        'age-min',
        'age-min-max-less',
        'amount',
        'app',
        'associations',
        'attachment_must_be_of_type',
        'back',
        'broadcast-budget-explanation',
        'broadcast-estimated-cost',
        'broadcast-estimated-reach',
        'broadcast-locally',
        'broadcast-locally-description',
        'broadcast-map-explanation',
        'broadcast-regionally',
        'broadcast-regionally-description',
        'budget',
        'care',
        'category',
        'charge_budget',
        'city',
        'city_select_default_city',
        'city_select_selected',
        'city_select_unselected',
        'city_select_unsupported',
        'confirm_delete_news',
        'confirm_delete_x',
        'connected_users_only',
        'contact',
        'community_services',
        'country',
        'coupon',
        'create',
        'created',
        'date_must_be_in_future',
        'delete',
        'description',
        'details',
        'end_time',
        'error-occured-unknown-try-again',
        'export',
        'first_name',
        'follow',
        'follower_name_or_email',
        'gender',
        'gender-female',
        'gender-male',
        'gender-male-female',
        'inactive',
        'invisible',
        'import',
        'jobs',
        'like',
        'message',
        'merchants',
        'name-attachment',
        'news_action_button_explanation',
        'news_content_explanation',
        'news_image_explanation',
        'news_items',
        'news_item_saved',
        'news_item_scheduled_for_datetime',
        'news_item_published',
        'news_label_explanation',
        'news_schedule_explanation',
        'news_target_audience_explanation',
        'news_type',
        'news_type_explanation',
        'news_review_all_sent_to_review',
        'no_previous_news_items',
        'none',
        'normal',
        'map',
        'opening-hours',
        'our-city-app',
        'page',
        'password',
        'phone_number',
        'please_select_attachment',
        'postal_code',
        'publish',
        'publish_later',
        'publish_now',
        'please_enter_at_least_x_characters',
        'reached',
        'reservation-name',
        'schedule',
        'scheduled_for_datetime',
        'search-dot-dot-dot',
        'search-keywords-hint',
        'send_notifications',
        'service-visible',
        'services',
        'settings-general',
        'statistics',
        'status',
        'street',
        'target_audience',
        'this_field_is_required',
        'title',
        'unknown',
        'unlimited',
        'use_cover_photo',
        'visible',
        'zip_code',
        'whitelist',
        'merchant_registered',
        'reservation-approve',
        'reservation-decline',
        'services',
        'denied',
        'refresh',
        'vat',
    },
    'web': {
        'Close',
        'Error',
        'News',
        'Retry',
        'error-occured-unknown-try-again',
    }
}
