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

import logging

from google.appengine.ext.webapp import template
from typing import Union

from rogerthat.translations import DEFAULT_LANGUAGE
from solutions.common import SOLUTION_COMMON
from solutions.common.consts import UNIT_SYMBOLS
from solutions.common.localizer import translations
from solutions.flex import SOLUTION_FLEX

template.register_template_library('solutions.templates.filter')


def get_supported_languages():
    return translations.keys()


def translate(language, key, suppress_warning=False, _duplicate_backslashes=False, **kwargs):
    # type: (basestring, basestring, bool, bool, **Union[unicode, int, long]) -> str
    language = (language or DEFAULT_LANGUAGE).replace('-', '_')
    if language not in translations:
        if '_' in language:
            language = language.split('_')[0]
            if language not in translations:
                language = DEFAULT_LANGUAGE
        else:
            language = DEFAULT_LANGUAGE
    if key in translations[language]:
        s = translations[language][key]
    else:
        if key not in translations[DEFAULT_LANGUAGE]:
            raise ValueError("Translation key '%s' not found for default language" % key)
        if not suppress_warning:
            logging.warn("Translation key '%s' not found for language '%s' - fallback to default" % (key, language))
        s = translations[DEFAULT_LANGUAGE][key]

    if kwargs:
        s = s % kwargs

    if _duplicate_backslashes:
        s = s.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t').replace("'", "\\'").replace('"', '\\"')

    return s


def translate_unit_symbol(language, unit):
    try:
        return translate(language, UNIT_SYMBOLS[unit])
    except ValueError:
        return UNIT_SYMBOLS[unit]


COMMON_JS_KEYS = {
    'ABUSE': 'Abuse',
    'ADD': 'reservation-add',
    'ADD_SHIFT': 'settings-add-shift',
    'ADD_TABLE': 'settings-add-table',
    'ADD_URL': 'add-url',
    'AJAX_ERROR_MESSAGE': 'ajax-error-message',
    'ALERT': 'Alert',
    'ALL': 'All',
    'APP': 'app',
    'ASSIGN_REDEEM_LOYALTY_POINTS': 'assign-redeem-loyalty-points',
    'ATTACHMENT': 'Attachment',
    'ATTACHMENTS': 'Attachments',
    'AUTHORIZE': 'Authorize',
    'AUTO_IMPORT': 'Auto import',
    'BACKGROUND_COLOR_IS_REQUIRED': 'Background color is required',
    'BOOKING_THRESHOLD': 'Booking Threshold',
    'BRAND': 'Brand',
    'BROWSER_NOT_FULLY_SUPPORTED': 'browser-not-fully-supported',
    'BROWSER_NOT_SUPPORT_ORDER_SIGNING': 'browser-not-support-order-signing',
    'BROWSER_SWITCH_TO_CHROME': 'browser-switch-to-chrome',
    'BY': 'By',
    'CANCEL': 'Cancel',
    'CAPACITY': 'Capacity',
    'CAPACITY_IS_REQUIRED': 'Capacity is required',
    'CARD_NUMBER': 'Card number',
    'CATEGORY_DUPLICATE_NAME': 'category_duplicate_name',
    'CHANNEL_DISCONNECTED_RELOAD_BROWSER': 'channel-disconnected-reload-browser',
    'CLICK_TO_ENLARGE': 'click-to-enlarge',
    'CLOSE': 'Close',
    'CONFIGURE': 'Configure',
    'CONFIRM': 'Confirm',
    'CONFIRM_DELETE_STATIC_CONTENT': 'confirm-delete-static-content',
    'CONTACT_PARTICIPANTS': 'participants-contact',
    'CONTACT_YOUR_X_FOR_MORE_INFO': 'contact-your-x-for-more-info',
    'CONTENT_IS_REQUIRED': 'Content is required',
    'CREATE_GROUP_PURCHASE': 'group-purchase-create',
    'CUSTOMERS': 'Customers',
    'DEFAULT_MENU_NAME': 'menu',
    'DELETE': 'delete',
    'DELETE_ADMIN_CONFIRMATION': 'delete-admin-confirm',
    'DELETE_SLIDE_CONFIRM': 'delete-slide-confirm',
    'DELETE_VISIT_TOOLTIP': 'delete-visit-tooltip',
    'DELETE_WITHOUT_NOTICE': 'delete-without-notice',
    'DESCRIPTION_IS_REQUIRED': 'Description is required',
    'DISCOUNT': 'Discount',
    'DISCOUNT_IS_AN_INVALID_NUMBER': 'Discount is an invalid number',
    'DISCOUNT_NEEDS_TO_BE_BETWEEN_0_AND_100': 'Discount needs to be between 0 and 100',
    'DONE': 'Done',
    'DOWNLOAD': 'Download',
    'DOWNLOAD_GOOGLE_CHROME': 'Download Google Chrome',
    'EDIT': 'Edit',
    'EDIT_DESCRIPTION': 'edit-description',
    'EDIT_SHIFT': 'settings-edit-shift',
    'EDIT_TABLE': 'settings-edit-table',
    'EMAIL': 'Email',
    'EMAIL_REMINDERS_DISABLED': 'Email reminders disabled',
    'EMAIL_REMINDERS_ENABLED': 'Email reminders enabled',
    'END': 'End',
    'END_DATE_24H_IN_FUTURE': 'end-date-24h-in-future',
    'ENTER_DOT_DOT_DOT': 'enter-dot-dot-dot',
    'ERROR': 'Error',
    'ERROR_OCCURED_CREDIT_CARD_LINKING': 'error-occured-credit-card-linking',
    'ERROR_OCCURED_UNKNOWN': 'error-occured-unknown',
    'EVENT_DATE': 'Date',
    'EVENT_ORGANIZER': 'events-organizer',
    'EVENT_PLACE': 'events-place',
    'EXPIRES': 'Expires',
    'FAILED': 'Failed',
    'FEATURE_DISABLED': 'feature-disabled',
    'FEATURE_NOT_ENABLED_ACCOUNT': 'feature-not-enabled-account',
    'FROM': 'inbox-from',
    'GROUP_PURCHASE_DELETE_CONFIRMATION': 'grouppurchase-delete-confirmation',
    'GROUP_PURCHASE_DISABLED': 'group-purchase-disabled',
    'GROUP_PURCHASE_ENABLED': 'group-purchase-enabled',
    'GROUP_SIZE': 'Group Size',
    'HELP': 'Help',
    'HIDE_PRICES': 'Hide prices',
    'HINT': 'Hint',
    'ICON_IS_REQUIRED': 'Icon is required',
    'INBOX_DELETE_MESSAGE_CONFIRMATION': 'delete-message-confirmation',
    'INPUT': 'Input',
    'INVALID_COLOR': 'Invalid color',
    'INVISIBLE': 'invisible',
    'INVOICE_VIEW': 'invoice-view',
    'KEY': 'Key',
    'LABEL_IS_REQUIRED': 'Label is required',
    'LANGUAGE': 'Language',
    'LEAPTIME': 'Leaptime',
    'LINK_CREDIT_CARD': 'Link credit card',
    'LOADING_DOT_DOT_DOT': 'loading-dot-dot-dot',
    'LOGOUT': 'Logout',
    'LOTTERY_NOT_REDEEMED': 'lottery-not-redeemed',
    'LOTTERY_NOT_REDEEMED_NEXT_WINNER': 'lottery-not-redeemed-next-winner',
    'LOTTERY_TEXT_DISCOUNT': 'lottery-text-discount',
    'LOTTERY_WITH_DATE': 'Lottery with date',
    'MANAGE_CREDIT_CARD': 'manage-credit-card',
    'MAXIMUM_UNITS_IS_AN_INVALID_NUMBER': 'Maximum units is an invalid number',
    'MAXIMUM_UNITS_IS_REQUIRED': 'Maximum units is required',
    'MENU_CATEGORY_DELETE_CONFIRMATION': 'menu-category-delete-confirmation',
    'MENU_CATEGORY_ITEM_DELETE_CONFIRMATION': 'menu-category-item-delete-confirmation',
    'MENU_CATEGORY_NEW': 'menu-category-new',
    'MENU_ITEM_NAME': 'menu-item-name',
    'MENU_NAME': 'menu-name',
    'MINIMUM_UNITS_IS_AN_INVALID_NUMBER': 'Minimum units is an invalid number',
    'MINIMUM_UNITS_IS_REQUIRED': 'Minimum units is required',
    'NAME': 'reservation-name',
    'NAME_AT_TIME': 'name-at-time',
    'NAME_IS_REQUIRED': 'Name is required',
    'NAME_REQUIRED': 'name-required',
    'NEW_CREDIT_CARD': 'New credit card',
    'NO': 'No',
    'NO_CALENDARS_FOUND': 'No calendars found',
    'NO_DAYS_SELECTED_FOR_THIS_SHIFT': 'No days selected for this shift',
    'NO_SHIFST_FOR_THIS_TIME': 'no-shifts-for-this-time',
    'NUMBER_OF_STAMPS': 'Number of stamps',
    'NUMBER_OF_STAMPS_IS_AN_INVALID_NUMBER': 'Number of stamps is an invalid number',
    'NUMBER_OF_STAMPS_NEEDS_TO_BE_AT_LEAST_1': 'Number of stamps needs to be at least 1',
    'NUMBER_OF_WINNERS_IS_AN_INVALID_NUMBER': 'Number of winners is an invalid number',
    'OKAY_I_GOT_IT': 'okay-i-got-it',
    'OPTIONAL_BRACES': '(optional)',
    'OPTIONS': 'Options',
    'ORDER_CANCEL': 'Cancel order',
    'ORDER_DELETE_CONFIRMATION': 'order-delete-confirmation',
    'OUR_CITY_APP': 'our-city-app',
    'OUR_CITY_APP_SUBSCRIPTION': 'our-city-app-subscription',
    'PARSING_DOT_DOT_DOT': 'parsing-dot-dot-dot',
    'PARTICIPANTS': 'participants',
    'PDF_IS_REQUIRED': 'PDF is required',
    'PERSONS': 'persons',
    'PHONE_NUMBER': 'Phone number',
    'PICTURE': 'picture',
    'PICTURE_SIZE_TOO_LARGE_20MB': 'picture-size-too-large-20mb',
    'PLEASE_ENTER_A_MESSAGE': 'please-enter-a-message',
    'PLEASE_ENTER_THE_WINNINGS': 'please-enter-the-winnings',
    'PLEASE_SELECT_A_PICTURE': 'Please select a picture',
    'POSITION_IS_REQUIRED': 'Position is required',
    'PREVIEW': 'Preview',
    'PRICE_IS_AN_INVALID_NUMBER': 'Price is an invalid number',
    'PRICE_P_UNIT': 'price-p-unit',
    'PRICE_REQUIRED': 'Price required',
    'PRODUCT_DUPLICATE_NAME': 'product_duplicate_name',
    'PUBLISHING_DOT_DOT_DOT': 'publishing-dot-dot-dot',
    'QANDA_SUCCESS_FORWARDED': 'qanda-success-forwarded',
    'READY': 'ready',
    'READY_FOR_COLLECTION': 'ready-for-collection',
    'READY_WITHOUT_NOTICE': 'ready-without-notice',
    'REDEEM': 'Redeem',
    'REDEEM_CONFIRMATION': 'redeem-confirmation',
    'REGION': 'Region',
    'REMARKS': 'order-remarks',
    'REMOVE': 'Remove',
    'REPAIR_DELETE_CONFIRMATION': 'repair-delete-confirmation',
    'REPLY': 'inbox-reply',
    'REPLY_ORDER_CANCEL': 'order-cancel',
    'REPLY_ORDER_READY': 'order-ready',
    'REPLY_REPAIR_CANCEL': 'repair-cancel',
    'REPLY_REPAIR_READY': 'repair-ready',
    'REPLY_TO_MORE_INFO': 'reply-to-more-info',
    'REQUIRED_LOWER': 'required-lower',
    'RESERVATIONS_OF_TABLE': 'Reservations of table',
    'RESERVATION_IN_CONNECTION_WITH': 'reservation-in-connection-with',
    'RESERVATION_REPLY_ON': 'reservation-reply-on',
    'RESTAURANT_RESERVATIONS_CANCEL_BROKEN': 'restaurant-reservations-cancel-broken',
    'RETRY': 'Retry',
    'SANDWICHES_DELETE_CONFIRMATION': 'sandwiches-delete-confirmation',
    'SAVE': 'Save',
    'SAVING_DOT_DOT_DOT': 'saving-dot-dot-dot',
    'SCAN': 'Scan',
    'SEARCH_DOT_DOT_DOT': 'search-dot-dot-dot',
    'SECRET': 'Secret',
    'SELECT_CONTACT': 'Select contact',
    'SELECT_TIMEZONE': 'select-timezone',
    'SEND': 'Send',
    'SENDING_DOT_DOT_DOT': 'sending-dot-dot-dot',
    'SETTINGS': 'Settings',
    'SHIFT_BOOKING_THRESHOLD': 'shift-booking-threshold',
    'SHIFT_LEAP_TIME': 'shift-leap-time',
    'SHIFT_MAX_GROUP_SIZE': 'shift-max-group-size',
    'SHIFT_MAX_PEOPLE': 'shift-max-people',
    'SHIFT_REMOVE_CONFIRMATION': 'shift-remove-confirmation',
    'SHOW_PRICES': 'Show prices',
    'SIGN_USING_KEYBOARD': 'Sign using keyboard',
    'SLIDESHOW': 'Slideshow',
    'SPENT': 'Spent',
    'STAFF': 'Staff',
    'STATIC_CONTENT_UPDATE': 'static-content-update',
    'STATUS_DISABLED': 'Status disabled',
    'STATUS_ENABLED': 'Status enabled',
    'SUBMIT': 'Submit',
    'SUBSCRIBE': 'Subscribe',
    'SUCCESS': 'Success',
    'TABLES_STILL_HAS_REVERVATIONS': 'tables-still-has-revervations',
    'TABLE_REMOVE_CONFIRMATION': 'table-remove-confirmation',
    'TABLE_REMOVE_REPLACE_BY_OTHER': 'table-remove-replace-by-other',
    'TEXT_COLOR_IS_REQUIRED': 'Text color is required',
    'THERE_ARE_NOT_ENOUGH_UNITS': 'new-group-subscription-failure-insufficient-units',
    'TIME': 'Time',
    'TIMEFRAME_CREATE': 'appointment-create',
    'TIMEFRAME_UPDATE': 'appointment-update',
    'TIME_IN_SECONDS': 'time-in-seconds',
    'TIME_START_END_EQUAL': 'time-start-end-equal',
    'TIME_START_END_SMALLER': 'time-start-end-smaller',
    'TITLE': 'title',
    'TITLE_IS_REQUIRED': 'Title is required',
    'TODO': 'Todo',
    'TOPPING': 'Topping',
    'TOTAL_NUMBER_OF_CUSTOMERS': 'Total number of customers:',
    'TOTAL_NUMBER_OF_UNITS_IS_REQUIRED': 'Total number of units is required',
    'TOTAL_UNITS_IS_AN_INVALID_NUMBER': 'Total units is an invalid number',
    'TYPE': 'Type',
    'UNASSIGN_TABLE_FROM_ALL_RESERVATIONS': 'Unassign table from all reservations',
    'UNITS': 'Units',
    'UNITS_IS_AN_INVALID_NUMBER': 'units-is-an-invalid-number',
    'UNIT_DESCRIPTION_IS_REQUIRED': 'Unit description is required',
    'UNIT_PRICE_IS_AN_INVALID_NUMBER': 'Unit price is an invalid number',
    'UNIT_PRICE_IS_REQUIRED': 'Unit price is required',
    'UNKNOWN': 'unknown',
    'UNTIL': 'Until',
    'UPDATE': 'Update',
    'UPDATE_GROUP_PURCHASE': 'group-purchase-update',
    'UPLOADING_TAKE_A_FEW_SECONDS': 'uploading-take-a-few-seconds',
    'URL': 'Url',
    'USED': 'Used',
    'USER': 'User', 'GOOGLE_CALENDAR': 'Google calendar',
    'USERS': 'users',
    'USE_THIS_LOCATION': 'Use this location',
    'VALIDATING': 'Validating',
    'VIEW': 'View',
    'VIEW_ORDER': 'order-view',
    'VIEW_REPAIR_ORDER': 'repair-order-view',
    'VISITS_IS_AN_INVALID_NUMBER': 'Visits is an invalid number',
    'VISITS_NEEDS_TO_BE_AT_LEAST_1': 'Visits needs to be at least 1',
    'WARNING': 'warning',
    'WEBSITE': 'Website',
    'WHAT_CAN_YOU_WIN': 'What can you win',
    'WINNER': 'Winner',
    'YES': 'Yes',
    'YOU_CANNOT_MAKE_A_GROUP_PURCHASE_IN_THE_PAST': 'You cannot make a group purchase in the past',
    'YOU_NEED_TO_PURCHASE_AT_LEAST_1_UNIT': 'You need to purchase at least 1 unit',
    'background_color': 'Background color',
    'color_scheme': 'Color scheme',
    'dark': 'Dark', 'TOTAL_NUMBER_OF_PARTICIPANTS': 'Total number of participants:',
    'light': 'Light',
    'link_cc': 'Link credit card',
    'menu_item_color': 'Menu item color',
    'name_visible': 'Name visible',
    'option': 'Option',
    'price': 'Price', 'DELETE_TABLE': 'Delete table',
    'text_color': 'Text color',
    'upload_picture_here': 'Upload a picture here',
    'use_your_smartphone': 'Use your smartphone',
}
