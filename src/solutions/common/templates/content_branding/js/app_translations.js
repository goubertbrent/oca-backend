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
 * @@license_version:1.2@@
 */

var Translations = {
    ADD_LOYALTY_POINTS :"{% translate language, 'common', 'Add loyalty points' %}",
    ADD_POINTS_DISABLED_REDEEM_FIRST : "{% translate language, 'common', 'add-points-disabled-redeem-first' %}",
    ADD_STAMPS_DISABLED_REDEEM_FIRST : "{% translate language, 'common', 'add-stamps-disabled-redeem-first' %}",
    ADDING_LOYALTY_POINTS : "{% translate language, 'common', 'Adding loyalty points' %}",
    ADDING_STAMPS : "{% translate language, 'common', 'Adding stamps' %}",
    CANCEL : "{% translate language, 'common', 'Cancel' %}",
    CONTACT_OWNER_TO_REDEEM : "{% translate language, 'common', 'loyalty-lottery-redeem-price' %}",
    ERROR_OCCURED_UNKNOWN : "{% translate language, 'common', 'error-occured-unknown' %}",
    HELLO_TEXT_TABLET : "{% translate language, 'common', 'hello-text-tablet' %}",  // REPLACE {0}
    INTERNET_SLOW_CONTINUE : "{% translate language, 'common', 'internet-slow-continue' %}",
    INTERNET_SLOW_RETRY : "{% translate language, 'common', 'internet-slow-retry' %}",
    INVALID_EMAIL_FORMAT : "{% translate language, 'common', 'invalid_email_format', '_duplicate_backslashes=true' %}", // REPLACE %(email)s
    LOADING_USER_INFO : "{% translate language, 'common', 'Loading user info' %}",
    LOYALTY_LOTTERY_VISIT_ONLY_ONCE : "{% translate language, 'common', 'loyalty-lottery-visit-only-once' %}",
    LOYALTY_TERMINAL_FOOTER_TEXT : "{% translate language, 'common', 'loyalty_terminal_footer_text' %}", // REPLACE %(app_name)s %(name)s
    MAXIMUM : "{% translate language, 'common', 'Maximum' %}",
    MINIMUM : "{% translate language, 'common', 'Minimum' %}",
    NAME_REQUIRED : "{% translate language, 'common', 'name-required' %}",
    NO_INTERNET_CONNECTION : "{% translate language, 'common', 'no-internet-connection' %}",
    PRICE : "{% translate language, 'common', 'Price' %}",
    PRICE_IS_NOT_A_NUMBER : "{% translate language, 'common', 'Price is not a number' %}",
    REDEEM_LOYALTY_POINTS : "{% translate language, 'common', 'Redeem loyalty points' %}",
    REDEEM_POINTS_DISABLED_ADD_FIRST : "{% translate language, 'common', 'redeem-points-disabled-add-first' %}",
    REDEEM_STAMPS_DISABLED_ADD_FIRST : "{% translate language, 'common', 'redeem-stamps-disabled-add-first' %}",
    REDEEM_TEXT_DISCOUNT : "{% translate language, 'common', 'redeem-text-discount' %}",  // REPLACE {0} {1} {2}
    REDEEM_TEXT_STAMPS_ONE : "{% translate language, 'common', 'redeem-text-stamps-one' %}",
    REDEEM_TEXT_STAMPS_MORE : "{% translate language, 'common', 'redeem-text-stamps-more' %}", // REPLACE %(count)s
    ROGERTHAT_FUNCTION_UNSUPPORTED_UPDATE : "{% translate language, 'common', 'rogerthat_function_unsupported_update' %}",
    REDEEMING_LOYALTY_POINTS : "{% translate language, 'common', 'Redeeming loyalty points' %}",
    REDEEMING_STAMPS : "{% translate language, 'common', 'Redeeming stamps' %}",
    REDEEMING_VOUCHER : "{% translate language, 'common', 'Redeeming voucher' %}",
    REMAINING_VALUE : "{% translate language, 'common', 'Remaining value' %}",
    REQUIRED_FIELDS_MISSING : "{% translate language, 'common', 'required' %}",
    SAVING_DOT_DOT_DOT : "{% translate language, 'common', 'saving-dot-dot-dot' %}",
    TNX_LOYALTY_LOTTERY_VISIT : "{% translate language, 'common', 'tnx-loyalty-lottery-visit' %}",  // REPLACE %(name)s $(date)s
    TNX_LOYALTY_LOTTERY_VISIT_NO_DATE : "{% translate language, 'common', 'tnx-loyalty-lottery-visit-no-date' %}",  // REPLACE %(name)s
    TRANSACTION_SUCCESSFUL : "{% translate language, 'common', 'Transaction successful' %}",
    UNKNOWN_QR_CODE_SCANNED : "{% translate language, 'common', 'Unknown QR code scanned' %}",
    VALIDATING : "{% translate language, 'common', 'Validating' %}",
    WELCOME : "{% translate language, 'common', 'Welcome' %}",
    YOU_ARE_THE_WINNER: "{% translate language, 'common', 'loyalty-lottery-winner' %}",
    coupon: '{% translate language, "common", "coupon", "_duplicate_backslashes=true" %}',
    coupon_redeemed: '{% translate language, "common", "coupon_redeemed", "_duplicate_backslashes=true" %}',
    loading_coupon: '{% translate language, "common", "loading_coupon", "_duplicate_backslashes=true" %}',
    redeem_coupon_for_user: '{% translate language, "common", "redeem_coupon_for_user", "_duplicate_backslashes=true" %}',
    redeem_coupon: '{% translate language, "common", "redeem_coupon", "_duplicate_backslashes=true" %}',
    redeeming_coupon: '{% translate language, "common", "redeeming_coupon", "_duplicate_backslashes=true" %}',
    Confirm: '{% translate language, "common", "Confirm", "_duplicate_backslashes=true" %}'
};

BootstrapDialog.DEFAULT_TEXTS[BootstrapDialog.TYPE_DEFAULT] = '{% translate language, "common", "info", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS[BootstrapDialog.TYPE_INFO] = '{% translate language, "common", "info", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS[BootstrapDialog.TYPE_PRIMARY] = '{% translate language, "common", "info", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS[BootstrapDialog.TYPE_SUCCESS] = '{% translate language, "common", "Success", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS[BootstrapDialog.TYPE_WARNING] = '{% translate language, "common", "warning", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS[BootstrapDialog.TYPE_DANGER] = '{% translate language, "common", "Error", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS['OK'] = '{% translate language, "common", "Done", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS['CANCEL'] = '{% translate language, "common", "Cancel", "_duplicate_backslashes=true" %}';
BootstrapDialog.DEFAULT_TEXTS['CONFIRM'] = '{% translate language, "common", "Confirm", "_duplicate_backslashes=true" %}';

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
