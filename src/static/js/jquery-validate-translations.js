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