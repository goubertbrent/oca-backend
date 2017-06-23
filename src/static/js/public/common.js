/*
 * Copyright 2017 Mobicage NV
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


function getBrowserLanguage() {
    var language = navigator.language;

    if(!language) {
        if(navigator.languages) {
            language = navigator.languages[0];
        } else {
            language = 'en';
        }
    }

    return language.split('-')[0];
}

function validateInput(e) {
    var valid = true;

    if(e.target) {
        e = e.target;
    }

    $(e).next('p[class=text-error]').remove();
    if(!e.checkValidity()) {
        $('<p class="text-error">' + e.validationMessage + '</p>').insertAfter($(e));
        valid = false;
    }

    return valid;
}


function validateInputs(parent) {
    var allValid = true;

    parent.find('input, select').each(function(i, e) {
        if(!allValid) {
            return;
        }

        if($(this).is(':visible')) {
            if(!validateInput(e)) {
                $(this).focus();
                allValid = false;
            }
        }
    });

    return allValid;
}
