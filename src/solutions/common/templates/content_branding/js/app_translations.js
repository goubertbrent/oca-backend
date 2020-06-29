/*
 * Copyright 2020 Green Valley Belgium NV
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
 * @@license_version:1.7@@
 */

var Translations = {
    ADD_LOYALTY_POINTS :"{% translate language, 'Add loyalty points' %}",
    ADD_POINTS_DISABLED_REDEEM_FIRST : "{% translate language, 'add-points-disabled-redeem-first' %}",
    ADD_STAMPS_DISABLED_REDEEM_FIRST : "{% translate language, 'add-stamps-disabled-redeem-first' %}",
    ADDING_LOYALTY_POINTS : "{% translate language, 'Adding loyalty points' %}",
    ADDING_STAMPS : "{% translate language, 'Adding stamps' %}",
    CANCEL : "{% translate language, 'Cancel' %}",
    CONTACT_OWNER_TO_REDEEM : "{% translate language, 'loyalty-lottery-redeem-price' %}",
    ERROR_OCCURED_UNKNOWN : "{% translate language, 'error-occured-unknown' %}",
    HELLO_TEXT_TABLET : "{% translate language, 'hello-text-tablet' %}",  // REPLACE {0}
    INTERNET_SLOW_CONTINUE : "{% translate language, 'internet-slow-continue' %}",
    INTERNET_SLOW_RETRY : "{% translate language, 'internet-slow-retry' %}",
    INVALID_EMAIL_FORMAT : "{% translate language, 'invalid_email_format', '_duplicate_backslashes=true' %}", // REPLACE %(email)s
    LOADING_USER_INFO : "{% translate language, 'Loading user info' %}",
    LOYALTY_LOTTERY_VISIT_ONLY_ONCE : "{% translate language, 'loyalty-lottery-visit-only-once' %}",
    LOYALTY_TERMINAL_FOOTER_TEXT : "{% translate language, 'loyalty_terminal_footer_text' %}", // REPLACE %(app_name)s %(name)s
    MAXIMUM : "{% translate language, 'Maximum' %}",
    MINIMUM : "{% translate language, 'Minimum' %}",
    NAME_REQUIRED : "{% translate language, 'name-required' %}",
    NO_INTERNET_CONNECTION : "{% translate language, 'no-internet-connection' %}",
    PRICE : "{% translate language, 'Price' %}",
    PRICE_IS_NOT_A_NUMBER : "{% translate language, 'Price is not a number' %}",
    REDEEM_LOYALTY_POINTS : "{% translate language, 'Redeem loyalty points' %}",
    REDEEM_POINTS_DISABLED_ADD_FIRST : "{% translate language, 'redeem-points-disabled-add-first' %}",
    REDEEM_STAMPS_DISABLED_ADD_FIRST : "{% translate language, 'redeem-stamps-disabled-add-first' %}",
    REDEEM_TEXT_DISCOUNT : "{% translate language, 'redeem-text-discount' %}",  // REPLACE {0} {1} {2}
    REDEEM_TEXT_STAMPS_ONE : "{% translate language, 'redeem-text-stamps-one' %}",
    REDEEM_TEXT_STAMPS_MORE : "{% translate language, 'redeem-text-stamps-more' %}", // REPLACE %(count)s
    ROGERTHAT_FUNCTION_UNSUPPORTED_UPDATE : "{% translate language, 'rogerthat_function_unsupported_update' %}",
    REDEEMING_LOYALTY_POINTS : "{% translate language, 'Redeeming loyalty points' %}",
    REDEEMING_STAMPS : "{% translate language, 'Redeeming stamps' %}",
    REDEEMING_VOUCHER : "{% translate language, 'Redeeming voucher' %}",
    REMAINING_VALUE : "{% translate language, 'Remaining value' %}",
    REQUIRED_FIELDS_MISSING : "{% translate language, 'required' %}",
    SAVING_DOT_DOT_DOT : "{% translate language, 'saving-dot-dot-dot' %}",
    TNX_LOYALTY_LOTTERY_VISIT : "{% translate language, 'tnx-loyalty-lottery-visit' %}",  // REPLACE %(name)s $(date)s
    TNX_LOYALTY_LOTTERY_VISIT_NO_DATE : "{% translate language, 'tnx-loyalty-lottery-visit-no-date' %}",  // REPLACE %(name)s
    TRANSACTION_SUCCESSFUL : "{% translate language, 'Transaction successful' %}",
    UNKNOWN_QR_CODE_SCANNED : "{% translate language, 'Unknown QR code scanned' %}",
    VALIDATING : "{% translate language, 'Validating' %}",
    WELCOME : "{% translate language, 'Welcome' %}",
    YOU_ARE_THE_WINNER: "{% translate language, 'loyalty-lottery-winner' %}",
    coupon: '{% translate language, "coupon", "_duplicate_backslashes=true" %}',
    coupon_redeemed: '{% translate language, "coupon_redeemed", "_duplicate_backslashes=true" %}',
    loading_coupon: '{% translate language, "loading_coupon", "_duplicate_backslashes=true" %}',
    redeem_coupon_for_user: '{% translate language, "redeem_coupon_for_user", "_duplicate_backslashes=true" %}',
    redeem_coupon: '{% translate language, "redeem_coupon", "_duplicate_backslashes=true" %}',
    redeeming_coupon: '{% translate language, "redeeming_coupon", "_duplicate_backslashes=true" %}',
    Confirm: '{% translate language, "Confirm", "_duplicate_backslashes=true" %}'
};

BootstrapDialog.DEFAULT_TEXTS[BootstrapDialog.TYPE_DEFAULT] = '{% translate language, "info", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS[BootstrapDialog.TYPE_INFO] = '{% translate language, "info", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS[BootstrapDialog.TYPE_PRIMARY] = '{% translate language, "info", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS[BootstrapDialog.TYPE_SUCCESS] = '{% translate language, "Success", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS[BootstrapDialog.TYPE_WARNING] = '{% translate language, "warning", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS[BootstrapDialog.TYPE_DANGER] = '{% translate language, "Error", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS['OK'] = '{% translate language, "Done", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS['CANCEL'] = '{% translate language, "Cancel", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS['CONFIRM'] = '{% translate language, "Confirm", "_duplicate_backslashes=true" %}';

function T(translationKey, args) {
    var translation = Translations[translationKey];
    if (!translation) {
        var msg = 'Missing translation for key \'' + translationKey + '\'';
        console.warn(msg);
        if (!DEBUG) {
            sln.logError(msg, new Error(msg));
        }
        return translationKey;
    }
    if (args) {
        for (var key in args) {
            if (args.hasOwnProperty(key)) {
                translation = replaceAll(translation, '%(' + key + ')s', args[key]);
            }
        }
    }
    return translation;
}
function replaceAll(string, str1, str2, ignore) {
    return string.replace(new RegExp(str1.replace(/([\/\,\!\\\^\$\{\}\[\]\(\)\.\*\+\?\|\<\>\-\&])/ig, "\\$&"), (ignore ? "g" : "g")), (typeof(str2) == "string") ? str2.replace(/\$/g, "$$$$") : str2);
}
