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

    var mainForm = $('#reset_password_form')[0];
    var form = $('form[class=white-box]');

    $('form').submit(function(event){
      event.preventDefault();
    });

    init();

    function init() {
        $('#reset_password_button').click(submit);
    }

    function submit() {
        if(validateInputs(form) && checkPasswordMatching()) {
            $('#password').val($('#password1').val());
            mainForm.submit();
        }
    }

    function checkPasswordMatching() {
        var password1, password2;
        password1 = $('#password1').val();
        password2 = $('#password2').val();

        $('#errors').text('');
        if(password1 && password2) {
            if(password1 === password2) {
                return true;
            }
        }

        $('#errors').text(SetPasswordTranslations.MISMATCH);
        return false;
    }

    $(document).ready(function() {
        $('#password1').focus();
    });

    $('#password1').keydown(function(event) {
        if(event.keyCode == 13) {
            if(validateInput(event.target)) {
                $('#password2').focus();
            }
        }
    });


    $(window).keydown(function(event) {
        if(event.keyCode == 13) {
            submit();
        }
    });

})();
