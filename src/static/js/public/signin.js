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


(function() {
    'use strict';

    var LOGIN_SUCCESS = 1;
    var LOGIN_FAIL_NO_PASSWORD = 2; // not possible here?
    var LOGIN_FAIL = 3;
    var LOGIN_TOO_MANY_ATTEMPTS = 4;
    var LOGIN_ACCOUNT_DEACTIVATED = 5;
    var LOGIN_FAILED_SERVICE_DISABLED = 6;

    $('form').submit(function (event) {
        event.preventDefault();
    });

    init();

    function getQueryVariable(name) {
        var query = window.location.search.substring(1);
        var vars = query.split('&');
        for (var i = 0; i < vars.length; i++) {
            var pair = vars[i].split('=');
            if (decodeURIComponent(pair[0]) === name) {
                return decodeURIComponent(pair[1]);
            }
        }
    }

    function init() {
        $('#signin_button').click(signin);
        $('input').keydown(function (event) {
            $('#errors').hide();
        });
        $('#email').val(getQueryVariable('email'));
    }

    function showError(message) {
        $('#errors').show();
        $('#errors').text(message);
    }

    function resetForm() {
        $('#password').val('');
        $('#email').focus();
    }

    function signin() {
        var formElem = $('#signin_form');
        if(!validateInputs(formElem)) {
            return;
        }
        var email = $('#email').val();
        var password = $('#password').val();

        sln.call({
            url: '/mobi/rest/user/login',
            type: 'POST',
            data: {
                email: email,
                password: password,
                remember: true,
            },
            success: function(result) {
                if(result === LOGIN_SUCCESS) {
                    window.location = '/';
                } else {
                    if(result === LOGIN_FAIL){
                        showError(SigninTranslations.LOGIN_FAIL);
                    } else if(result === LOGIN_TOO_MANY_ATTEMPTS) {
                        showError(SigninTranslations.TOO_MANY_ATTEMPTS);
                    } else if(result === LOGIN_ACCOUNT_DEACTIVATED) {
                        showError(SigninTranslations.DEACTIVATED_ACCOUNT);
                    } else if(result === LOGIN_FAILED_SERVICE_DISABLED) {
                        showError(SigninTranslations.DEACTIVATED_SERVICE);
                    }
                    resetForm();
                }
            },
            error: sln.showAjaxError
        });
    }

    $(document).ready(function() {
        $('#email').focus();
    });

    $('#email').keydown(function(event) {
        if(event.keyCode == 13) {
            if(validateInput(event)) {
                $('#password').focus();
            }
        }
    });

    $(window).keydown(function(event) {
        if(event.keyCode == 13) {
            signin();
        }
    });

})();
