# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

import logging

from google.appengine.ext import webapp

from rogerthat.translations import DEFAULT_LANGUAGE
from solutions.common import SOLUTION_COMMON
from solutions.common.consts import UNIT_SYMBOLS
from solutions.common.localizer import translations as common_translations
from solutions.djmatic import SOLUTION_DJMATIC
from solutions.djmatic.localizer import translations as djmatic_translations
from solutions.flex import SOLUTION_FLEX
from solutions.flex.localizer import translations as flex_translations

SOLUTIONS = [SOLUTION_DJMATIC, SOLUTION_FLEX]

translations = {
    SOLUTION_DJMATIC: djmatic_translations,
    SOLUTION_COMMON: common_translations,
    SOLUTION_FLEX: flex_translations
}

webapp.template.register_template_library('solutions.templates.filter')


def translate(language, lib, key, suppress_warning=False, _duplicate_backslashes=False, **kwargs):
    if not language:
        language = DEFAULT_LANGUAGE
    if not lib or not key:
        raise ValueError("lib and key are required arguments")
    if lib not in translations:
        raise ValueError("Unknown translation library '%s' requested" % lib)
    library = translations[lib]
    language = language.replace('-', '_')
    if not language in library:
        if '_' in language:
            language = language.split('_')[0]
            if not language in library:
                language = DEFAULT_LANGUAGE
        else:
            language = DEFAULT_LANGUAGE
    if key in library[language]:
        s = library[language][key]
    else:
        if key not in library[DEFAULT_LANGUAGE]:
            if lib != SOLUTION_COMMON:
                return translate(language, SOLUTION_COMMON, key, suppress_warning, **kwargs)
            else:
                raise ValueError("Translation key '%s' not found in library '%s' for default language" % (key, lib))
        if not suppress_warning:
            logging.warn("Translation key '%s' not found in library '%s' for language "
                         "'%s' - fallback to default" % (key, lib, language))
        s = library[DEFAULT_LANGUAGE][key]

    if kwargs:
        s = s % kwargs

    if _duplicate_backslashes:
        s = s.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t').replace("'", "\\'").replace('"', '\\"')

    return s


def translate_unit_symbol(language, unit):
    try:
        return translate(language, SOLUTION_COMMON, UNIT_SYMBOLS[unit])
    except ValueError:
        return UNIT_SYMBOLS[unit]

COMMON_JS_KEYS = {'SELECT_ICON': 'select-icon',
                  'STARTING_AT': 'starting_at',
                  'AGE': 'age',
                  'load_more': 'Load more',
                  'MENU_CATEGORY_DELETE_CONFIRMATION':
                  'menu-category-delete-confirmation',
                  'PRICE_REQUIRED': 'Price required',
                  'CONTENT_IS_REQUIRED': 'Content is required',
                  'CALENDAR_ADMINS': 'calendar-admins',
                  'OPENING_HOURS': 'opening-hours',
                  'NO_SHIFST_FOR_THIS_TIME': 'no-shifts-for-this-time',
                  'BROADCAST_TYPE': 'Broadcast type',
                  'SENDING_DOT_DOT_DOT': 'sending-dot-dot-dot',
                  'ERROR_OCCURED_UNKNOWN': 'error-occured-unknown',
                  'LOADING_DOT_DOT_DOT': 'loading-dot-dot-dot',
                  'WHAT_CAN_YOU_WIN': 'What can you win',
                  'TIME_START_END_SMALLER': 'time-start-end-smaller',
                  'NO_CALENDARS_FOUND': 'No calendars found',
                  'CONFIGURE': 'Configure',
                  'ERROR_OCCURED_CREDIT_CARD_LINKING': 'error-occured-credit-card-linking',
                  'BRAND': 'Brand',
                  'AGENDA_ENABLED': 'agenda-enabled',
                  'VIEW': 'View',
                  'USED': 'Used',
                  'REPLY_ORDER_CANCEL': 'order-cancel',
                  'REPLY_TO_MORE_INFO': 'reply-to-more-info',
                  'use_your_smartphone': 'Use your smartphone',
                  'DISCOUNT_IS_AN_INVALID_NUMBER': 'Discount is an invalid number',
                  'SHIFT_MAX_GROUP_SIZE': 'shift-max-group-size',
                  'TABLE_REMOVE_CONFIRMATION': 'table-remove-confirmation',
                  'GROUP_PURCHASE_ENABLED': 'group-purchase-enabled',
                  'SET_FACEBOOK_PAGE_AND_START_SHARING': 'set-facebook-page-start-sharing',
                  'CARD_NUMBER': 'Card number',
                  'MANAGE_CREDIT_CARD': 'manage-credit-card',
                  'ADD_ATTACHMENT': 'add-attachment',
                  'SEARCH_KEYWORDS_HINT': 'search-keywords-hint',
                  'LOGOUT': 'Logout',
                  'PREVIEW': 'Preview',
                  'AUTHORIZE': 'Authorize',
                  'DISABLED': 'Disabled',
                  'EVENT_EDIT': 'event-edit',
                  'UNITS_IS_AN_INVALID_NUMBER': 'units-is-an-invalid-number',
                  'CLICK_TO_CHANGE': '(Click to change)',
                  'CALENDAR_ADMIN_ADD': 'calendar-admin-add',
                  'DELETE_SLIDE_CONFIRM': 'delete-slide-confirm',
                  'HOLIDAY_REMOVE_CONFIRMATION': 'holiday-remove-confirmation',
                  'TEXT_COLOR_IS_REQUIRED': 'Text color is required',
                  'CAPACITY': 'Capacity',
                  'GENDER': 'gender',
                  'EXPIRES': 'Expires',
                  'MINIMUM_UNITS_IS_AN_INVALID_NUMBER': 'Minimum units is an invalid number',
                  'SHIFT_BOOKING_THRESHOLD': 'shift-booking-threshold',
                  'INVOICE_VIEW': 'invoice-view',
                  'UNITS': 'Units',
                  'REPLY': 'inbox-reply',
                  'TWITTER_PAGE': 'Twitter page',
                  'BROADCAST_ENABLED': 'broadcast-enabled',
                  'ALL': 'All',
                  'PARSING_DOT_DOT_DOT': 'parsing-dot-dot-dot',
                  'AGENDA_DISABLED': 'agenda-disabled',
                  'INVALID_COLOR': 'Invalid color',
                  'TITLE_IS_REQUIRED': 'Title is required',
                  'CREATE_GROUP_PURCHASE': 'group-purchase-create',
                  'NUMBER_OF_STAMPS_NEEDS_TO_BE_AT_LEAST_1': 'Number of stamps needs to be at least 1',
                  'SERVICE_VISIBLE': 'service-visible',
                  'CONFIRM_DELETE_STATIC_CONTENT': 'confirm-delete-static-content',
                  'SETTINGS': 'Settings',
                  'LEAPTIME': 'Leaptime',
                  'REMOVE_FAILED': 'remove-failed',
                  'OUR_CITY_APP_SUBSCRIPTION': 'our-city-app-subscription',
                  'FEATURE_DISABLED': 'feature-disabled',
                  'PRICE_IS_AN_INVALID_NUMBER': 'Price is an invalid number',
                  'CANCEL': 'Cancel',
                  'UNIT_PRICE_IS_REQUIRED': 'Unit price is required',
                  'MENU_CATEGORY_ITEM_DELETE_CONFIRMATION': 'menu-category-item-delete-confirmation',
                  'light': 'Light',
                  'ALERT': 'Alert',
                  'AVATAR': 'Avatar',
                  'SAVING_DOT_DOT_DOT': 'saving-dot-dot-dot',
                  'BOOKING_THRESHOLD': 'Booking Threshold',
                  'SPENT': 'Spent',
                  'EDIT_SHIFT': 'settings-edit-shift',
                  'LINK_CREDIT_CARD': 'Link credit card',
                  'FACEBOOK_VISIBILITY_APP': 'facebook-visibility-app',
                  'CUSTOMERS': 'Customers',
                  'POSITION_IS_REQUIRED': 'Position is required',
                  'AUTO_IMPORT': 'Auto import',
                  'VISIBLE': 'visible',
                  'URL': 'Url',
                  'DELETE_WITHOUT_NOTICE': 'delete-without-notice',
                  'ADD_HOLIDAY': 'settings-add-holiday',
                  'UNASSIGN_TABLE_FROM_ALL_RESERVATIONS': 'Unassign table from all reservations',
                  'PRODUCT_DUPLICATE_NAME': 'product_duplicate_name',
                  'TOPPING': 'Topping',
                  'APP': 'app', 'INSUFFICIENT_PERMISSIONS': 'insufficient-permissions',
                  'TABLE_REMOVE_REPLACE_BY_OTHER': 'table-remove-replace-by-other',
                  'ADDRESS': 'address',
                  'SAVE': 'Save',
                  'REGION': 'Region',
                  'DELETE': 'inbox-delete',
                  'WEB_ADDRESS': 'web-address',
                  'DELETE_ADMIN_CONFIRMATION': 'delete-admin-confirm',
                  'MENU_CATEGORY_NEW': 'menu-category-new',
                  'DONE': 'Done',
                  'EVENT_DATE': 'Date',
                  'WEBSITE': 'Website',
                  'FACEBOOK_PAGE': 'Facebook page',
                  'HIDE_PRICES': 'Hide prices',
                  'REQUIRED': 'required',
                  'SLIDESHOW': 'Slideshow',
                  'SEND_INVITATION_TO_X_EMAILS': 'send-invitation-to-x-emails',
                  'INVISIBLE': 'invisible',
                  'END': 'End',
                  'UPDATE': 'Update',
                  'MAXIMUM_UNITS_IS_AN_INVALID_NUMBER': 'Maximum units is an invalid number',
                  'SCHEDULE_BROADCAST': 'Schedule broadcast',
                  'DETAILS': 'usage-detail',
                  'GROUP_PURCHASE_DELETE_CONFIRMATION': 'grouppurchase-delete-confirmation',
                  'SHIFT_LEAP_TIME': 'shift-leap-time',
                  'LABEL_IS_REQUIRED': 'Label is required',
                  'CREATE_NEW_CALENDAR': 'create-new-calendar',
                  'PUBLISH_CHANGES': 'publish-changes',
                  'TRY': 'Try',
                  'TIME': 'Time',
                  'UNIT_PRICE_IS_AN_INVALID_NUMBER': 'Unit price is an invalid number',
                  'FACEBOOK_ADMIN_REQUIRED': 'facebook-admin-required',
                  'UNKNOWN': 'unknown',
                  'GENDER_FEMALE': 'gender-female',
                  'TIME_START_END_EQUAL': 'time-start-end-equal',
                  'PICTURE_SIZE_TOO_LARGE_20MB': 'picture-size-too-large-20mb',
                  'SELECT_TIMEZONE': 'select-timezone',
                  'background_color': 'Background color',
                  'LOTTERY_NOT_REDEEMED_NEXT_WINNER': 'lottery-not-redeemed-next-winner',
                  'GATHER_EVENTS_ENABLED': 'Show events of merchants and associations',
                  'EMAIL_REMINDERS_DISABLED': 'Email reminders disabled',
                  'CONTINUE_WITHOUT_FACEBOOK_POST': 'continue-without-facebook-post',
                  'SHIFT_MAX_PEOPLE': 'shift-max-people',
                  'BROADCAST_PLANNED_SUCCESSFULLY': 'broadcast-planned-successfully',
                  'option': 'Option',
                  'SUCCESS': 'Success',
                  'CHANNEL_DISCONNECTED_RELOAD_BROWSER': 'channel-disconnected-reload-browser',
                  'STATUS_DISABLED': 'Status disabled',
                  'SHIFT_REMOVE_CONFIRMATION': 'shift-remove-confirmation',
                  'MINIMUM_UNITS_IS_REQUIRED': 'Minimum units is required',
                  'AGE_MIN_MAX_LESS': 'age-min-max-less',
                  'EVENT_REMIND_ME': 'events-reminder',
                  'REDEEMED': 'Redeemed',
                  'KEY': 'Key',
                  'SECRET': 'Secret',
                  'EVENTS_UIT_ACTOR': 'event-uit-actor',
                  'USER': 'User', 'GOOGLE_CALENDAR': 'Google calendar',
                  'SET_NOW': 'Set now',
                  'DOWNLOAD_GOOGLE_CHROME': 'Download Google Chrome',
                  'OPTIONS': 'Options',
                  'PICTURE': 'picture',
                  'SERVICE_INVISIBLE': 'service-invisible',
                  'VIEW_ORDER': 'order-view',
                  'ASSIGN_REDEEM_LOYALTY_POINTS': 'assign-redeem-loyalty-points',
                  'PARTICIPANTS': 'participants',
                  'REMARKS': 'order-remarks',
                  'CONTACT_PARTICIPANTS': 'participants-contact',
                  'GATHER_EVENTS_DISABLED': 'Hide events of merchants and associations',
                  'price': 'Price', 'DELETE_TABLE': 'Delete table',
                  'VISITS_NEEDS_TO_BE_AT_LEAST_1': 'Visits needs to be at least 1',
                  'OPTIONAL_BRACES': '(optional)',
                  'MAXIMUM_UNITS_IS_REQUIRED': 'Maximum units is required',
                  'REDEEM_CONFIRMATION': 'redeem-confirmation',
                  'FROM': 'inbox-from',
                  'UPLOADING_TAKE_A_FEW_SECONDS': 'uploading-take-a-few-seconds',
                  'link_cc': 'Link credit card',
                  'ADD_TABLE': 'settings-add-table',
                  'BROADCAST_DISABLED': 'broadcast-disabled',
                  'REPLY_ORDER_READY': 'order-ready',
                  'LOTTERY_TEXT_DISCOUNT': 'lottery-text-discount',
                  'ICON_IS_REQUIRED': 'Icon is required',
                  'REPAIR_DELETE_CONFIRMATION': 'repair-delete-confirmation',
                  'FEATURE_NOT_ENABLED_ACCOUNT': 'feature-not-enabled-account',
                  'DESCRIPTION_IS_REQUIRED': 'Description is required',
                  'LOTTERY_NOT_REDEEMED': 'lottery-not-redeemed',
                  'DELETE_VISIT_TOOLTIP': 'delete-visit-tooltip',
                  'URL_IS_REQUIRED': 'Url is required',
                  'VIEW_REPAIR_ORDER': 'repair-order-view',
                  'UPDATE_GROUP_PURCHASE': 'group-purchase-update',
                  'INVITES_SENT': 'Invites sent',
                  'CONTACT_YOUR_X_FOR_MORE_INFO': 'contact-your-x-for-more-info',
                  'TABLES_STILL_HAS_REVERVATIONS': 'tables-still-has-revervations',
                  'CATEGORY_DUPLICATE_NAME': 'category_duplicate_name',
                  'STATUS_ENABLED': 'Status enabled',
                  'SEND': 'Send',
                  'FACEBOOK_PLACE_REQUIRED': 'facebook-place-required',
                  'FAILED': 'Failed',
                  'ABUSE': 'Abuse',
                  'YOU_CANNOT_MAKE_A_GROUP_PURCHASE_IN_THE_PAST': 'You cannot make a group purchase in the past',
                  'YES': 'Yes',
                  'HELP': 'Help',
                  'PLEASE_ENTER_THE_WINNINGS': 'please-enter-the-winnings',
                  'CLICK_TO_ENLARGE': 'click-to-enlarge',
                  'SETTINGS_END': 'settings-end',
                  'VISITS_IS_AN_INVALID_NUMBER': 'Visits is an invalid number',
                  'PLEASE_ENTER_A_MESSAGE': 'please-enter-a-message',
                  'BY': 'By',
                  'NUMBER_OF_STAMPS_IS_AN_INVALID_NUMBER': 'Number of stamps is an invalid number',
                  'WARNING': 'warning',
                  'menu_item_color': 'Menu item color',
                  'EVENT_PLACE': 'events-place',
                  'EVENT_ADD': 'events-add',
                  'DOWNLOAD': 'Download',
                  'INPUT': 'Input',
                  'RESERVATIONS_OF_TABLE': 'Reservations of table',
                  'UNTIL': 'Until',
                  'CAPACITY_IS_REQUIRED': 'Capacity is required',
                  'ADD_URL': 'add-url',
                  'TOTAL_NUMBER_OF_UNITS_IS_REQUIRED': 'Total number of units is required',
                  'PDF_IS_REQUIRED': 'PDF is required',
                  'NEW_CREDIT_CARD': 'New credit card',
                  'SEARCH_DOT_DOT_DOT': 'search-dot-dot-dot',
                  'STAFF': 'Staff',
                  'TITLE': 'events-title',
                  'YOU_NEED_TO_PURCHASE_AT_LEAST_1_UNIT': 'You need to purchase at least 1 unit',
                  'name_visible': 'Name visible',
                  'RESTAURANT_RESERVATIONS_CANCEL_BROKEN': 'restaurant-reservations-cancel-broken',
                  'BACKGROUND_COLOR_IS_REQUIRED': 'Background color is required',
                  'DEFAULT_MENU_NAME': 'menu',
                  'RESERVATION_IN_CONNECTION_WITH': 'reservation-in-connection-with',
                  'PHONE_NUMBER': 'Phone number',
                  'BROADCAST_TYPE_REQUIRED': 'broadcast-type-required',
                  'LOTTERY_WITH_DATE': 'Lottery with date',
                  'text_color': 'Text color',
                  'BROADCAST_SEND_SUCCESSFULLY': 'broadcast-send-successfully',
                  'TOTAL_UNITS_IS_AN_INVALID_NUMBER': 'Total units is an invalid number',
                  'NOT_GOING': 'Not going',
                  'STATIC_CONTENT_UPDATE': 'static-content-update',
                  'GROUP_SIZE': 'Group Size',
                  'NAME': 'reservation-name',
                  'PUBLISHING_DOT_DOT_DOT': 'publishing-dot-dot-dot',
                  'PERSONS': 'persons',
                  'ATTACHMENT': 'Attachment',
                  'REQUIRED_LOWER': 'required-lower',
                  'TYPE': 'Type',
                  'LOGIN_WITH_FACEBOOK_FIRST': 'Login with facebook first',
                  'READY_FOR_COLLECTION': 'ready-for-collection',
                  'TIMEFRAME_CREATE': 'appointment-create',
                  'TIMEFRAME_UPDATE': 'appointment-update',
                  'GROUP_PURCHASE_DISABLED': 'group-purchase-disabled',
                  'SUBSCRIBE': 'Subscribe',
                  'SCAN': 'Scan',
                  'MAYBE': 'Maybe',
                  'GUESTS': 'Guests',
                  'RESERVATION_REPLY_ON': 'reservation-reply-on',
                  'ENTER_DOT_DOT_DOT': 'enter-dot-dot-dot',
                  'NAME_AT_TIME': 'name-at-time',
                  'AJAX_ERROR_MESSAGE': 'ajax-error-message',
                  'THERE_ARE_NOT_ENOUGH_UNITS': 'new-group-subscription-failure-insufficient-units',
                  'TIME_IN_SECONDS': 'time-in-seconds',
                  'DISCOUNT': 'Discount',
                  'ENTER_NAME_OR_EMAIL': 'enter-name-or-email',
                  'NAME_IS_REQUIRED': 'Name is required',
                  'EMAIL': 'Email',
                  'ORDER_CANCEL': 'Cancel order',
                  'HINT': 'Hint',
                  'NUMBER_OF_WINNERS_IS_AN_INVALID_NUMBER': 'Number of winners is an invalid number',
                  'dark': 'Dark', 'TOTAL_NUMBER_OF_PARTICIPANTS': 'Total number of participants:',
                  'LOGO': 'Logo',
                  'ALL_INVITES_WERE_SENT_SUCCESSFULLY': 'All invites were sent successfully',
                  'TODO': 'Todo',
                  'ATTACHMENTS': 'Attachments',
                  'EDIT': 'Edit',
                  'READY': 'ready',
                  'REPLY_REPAIR_CANCEL': 'repair-cancel',
                  'USE_THIS_LOCATION': 'Use this location',
                  'TOTAL_NUMBER_OF_CUSTOMERS': 'Total number of customers:',
                  'CALENDAR_REMOVE_FAILED_HAS_EVENTS': 'calendar-remove-failed-has-events',
                  'REDEEM': 'Redeem', 'GOING': 'Going',
                  'OUR_CITY_APP': 'our-city-app',
                  'GENDER_MALE': 'gender-male',
                  'LANGUAGE': 'Language',
                  'EMAIL_REMINDERS_ENABLED': 'Email reminders enabled',
                  'WINNER': 'Winner',
                  'SIGN_USING_KEYBOARD': 'Sign using keyboard',
                  'NUMBER_OF_STAMPS': 'Number of stamps',
                  'SANDWICHES_DELETE_CONFIRMATION': 'sandwiches-delete-confirmation',
                  'CONFIRM': 'Confirm',
                  'NO_DAYS_SELECTED_FOR_THIS_SHIFT': 'No days selected for this shift',
                  'MENU_NAME': 'menu-name',
                  'EDIT_TABLE': 'settings-edit-table',
                  'FACEBOOK_ADMIN_PERMISSIONS_REQUIRED': 'facebook-admin-permissions-required',
                  'ERROR': 'Error',
                  'INBOX_DELETE_MESSAGE_CONFIRMATION': 'inbox-delete-message-confirmation',
                  'REMOVE': 'Remove',
                  'BROWSER_NOT_FULLY_SUPPORTED': 'browser-not-fully-supported',
                  'MENU_ITEM_NAME': 'menu-item-name',
                  'ADD_SHIFT': 'settings-add-shift',
                  'PRICE_P_UNIT': 'price-p-unit',
                  'ADD_WEBSITE': 'add-website',
                  'PLEASE_SELECT_A_PICTURE': 'Please select a picture',
                  'QANDA_SUCCESS_FORWARDED': 'qanda-success-forwarded',
                  'ENABLED': 'Enabled', 'INBOX_MESSAGE': 'inbox-message',
                  'SHOW_PRICES': 'Show prices',
                  'NO': 'No',
                  'ADD_MOBILE_INBOX_FORWARDERS': 'add-mobile-inbox-forwarders',
                  'CLOSE': 'Close',
                  'READY_WITHOUT_NOTICE': 'ready-without-notice',
                  'ADD': 'reservation-add',
                  'END_TIME': 'End time',
                  'UNIT_DESCRIPTION_IS_REQUIRED': 'Unit description is required',
                  'EMAIL_ADDRESS': 'E-mail address',
                  'OR_SCAN_QRCODE_APP': 'or-scan-qr-code-app',
                  'SUBMIT': 'Submit',
                  'OKAY_I_GOT_IT': 'okay-i-got-it',
                  'SCHEDULED_BROADCAST_NOTE': 'scheduled-broadcast-note',
                  'BROWSER_NOT_SUPPORT_ORDER_SIGNING': 'browser-not-support-order-signing',
                  'RETRY': 'Retry',
                  'DISCOUNT_NEEDS_TO_BE_BETWEEN_0_AND_100': 'Discount needs to be between 0 and 100',
                  'upload_picture_here': 'Upload a picture here',
                  'SETTINGS_START': 'settings-start',
                  'REPLY_REPAIR_READY': 'repair-ready',
                  'SELECT_CONTACT': 'Select contact',
                  'FROM_X_TO_Y_ON_Z': 'from-x-to-y-on-z',
                  'USERS': 'users',
                  'BROWSER_SWITCH_TO_CHROME': 'browser-switch-to-chrome',
                  'EDIT_DESCRIPTION': 'edit-description',
                  'VALIDATING': 'Validating',
                  'NAME_REQUIRED': 'name-required',
                  'END_DATE_24H_IN_FUTURE': 'end-date-24h-in-future',
                  'color_scheme': 'Color scheme',
                  'TWITTER_PAGE_REQUIRED': 'twitter-place-required',
                  'ORDER_DELETE_CONFIRMATION': 'order-delete-confirmation',
                  'EVENT_ORGANIZER': 'events-organizer',
                  'START': 'Start',
                  'PHONE_REQUIRED': 'phone-required',
                  'NO_MORE_SANDWICHES': 'no-more-sandwiches',
                  'HISTORY': 'History',
                  'DESCRIPTION': 'events-description',
                  'PRICE': 'Price',
                  'NOTE': 'Note',
                  'URLS': 'Urls'}
