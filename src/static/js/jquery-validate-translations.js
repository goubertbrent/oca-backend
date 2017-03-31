/*
 * Copyright 2017 GIG Technology NV
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * @@license_version:1.3@@
 */

(function () {
    'use strict';
    $.extend($.validator.messages, {
        required: T('this_field_is_required'),
        remote: 'Please fix this field.',
        email: "Please enter a valid email address",
        url: "Please enter a valid url",
        date: "Please enter a valid date",
        dateISO: 'Please enter a valid date (ISO).',
        number: "Please enter a number",
        digits: 'Please enter only digits.',
        creditcard: 'Please enter a valid creditcard',
        equalTo: 'The values do not match',
        accept: 'Please enter a value with a valid extension.',
        maxlength: jQuery.validator.format(T('please_enter_no_more_than_x_characters').replace('%(characters)s', '{0}')),
        minlength: jQuery.validator.format(T('please_enter_at_least_x_characters').replace('%(characters)s', '{0}')),
        rangelength: jQuery.validator.format('Please enter a value between {0} and {1} characters long.'),
        range: jQuery.validator.format('Please enter a value between {0} and {1}.'),
        max: jQuery.validator.format('Please enter a value less than or equal to {0}.'),
        min: jQuery.validator.format('Please enter a value greater than or equal to {0}.')
    });
})();
