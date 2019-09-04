/*
 * Copyright 2019 Green Valley Belgium NV
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
 * @@license_version:1.5@@
 */


(function() {
    'use strict';

    var form = $('form[class=white-box]');

    $('form').submit(function(event){
        event.preventDefault();
    });

    init();

    function init() {
        $('#send_instructions').click(submit);
    }

    function submit() {
        if(validateInputs(form)) {
            sendInstructions();
        }
    }

    $(window).keydown(function(event) {
        if(event.keyCode == 13) {
            submit();
        }
    });

    function sendInstructions() {
        var value = $('#email').val();
        if(!value.trim()) {
            return;
        }
        var setPasswordRoute = '/customers/setpassword';
        if (SIGNUP_APP_ID) {
            setPasswordRoute += '/' + SIGNUP_APP_ID;
        }
        sln.call({
            url: '/mobi/rest/user/reset_password',
            type: 'post',
            data: {
                email: value,
                sender_name: 'OCA',
                set_password_route: setPasswordRoute
            },
            success: function(result) {
                if(result) {
                    form.hide();
                    $('#reset_password_note').text(ResetPasswordTranslations.RESET_INSTRUCTIONS_SENT);
                    $('#go_back').show();
                } else {
                    $('#errors').text(ResetPasswordTranslations.RESET_PASSWORD_FAILED);
                }
            },
            error: sln.showAjaxError
        });
    }

})();
