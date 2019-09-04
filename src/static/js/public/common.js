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
    if(e.target) {
        e = e.target;
    }

    var valid = e.checkValidity();
    var msg = e.validationMessage;
    var elem = $(e);
    elem.next('p[class=text-error]').remove();
    if (!valid) {
        $('<p class="text-error">' + msg + '</p>').insertAfter(elem);
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


function isDigit(str) {
    return !isNaN(parseInt(str));
}

// A helper to load/reload google recaptcha when needed
function RecaptchaLoader(options) {
    this.container = options.container;
    this.renderParams = options.renderParams || 'inherit';
    this.loaded = false;

    this.scriptUrl = 'https://www.google.com/recaptcha/api.js?render=explicit&onload=grecaptchaLoaded';
    this.onLoadCallback = options.onLoadCallback;

    window.grecaptchaLoaded = this.onLoad.bind(this);
}

RecaptchaLoader.prototype = {
    onLoad: function() {
        grecaptcha.render(this.container, this.renderParams);
        this.loaded = true;

        if (typeof this.onLoadCallback === 'function') {
            this.onLoadCallback();
        }
    },

    isLoaded: function() {
        return this.loaded;
    },

    load: function() {
        var scriptElem = document.createElement('script');
        scriptElem.src = this.scriptUrl;
        scriptElem.async = true;
        scriptElem.defer = true;
        document.head.appendChild(scriptElem);
    },

    reload: function() {
        // cleanup
        if (this.isLoaded()) {
            $('script[src="' + this.scriptUrl + '"]').remove();
            if (typeof this.container === 'string') {
                $('#' + this.container).empty();
            } else {
                $(this.container).empty();
            }
            this.loaded = false;
        }
        // then load again
        this.load();
    },

    call: function(name) {
        if (this.isLoaded()) {
            return grecaptcha[name]();
        }
        throw new ReferenceError('Error calling grecaptcha.' + name + ', Grecaptcha is not loaded yet')
    },

    execute: function() {
        this.call('execute');
    },

    reset: function() {
        this.call('reset');
    }

};
