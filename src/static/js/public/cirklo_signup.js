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

$(function () {
    'use strict';

    function RequestsService() {
        this._requestCache = {};
    }

    RequestsService.prototype = {
        request: function (url, method, data, options) {
            if (!options) {
                options = {};
            }
            if (options.showError === undefined) {
                options.showError = true;
            }
            return new Promise(function (resolve, reject) {
                sln.call({
                    url: url,
                    type: method,
                    data: data,
                    success: function (data) {
                        resolve(data);
                    },
                    error: function (data, textStatus, XMLHttpRequest) {
                        if (options.showError) {
                            sln.showAjaxError();
                        }
                        reject({data: data, textStatus: textStatus, XMLHttpRequest: XMLHttpRequest});
                    }
                });
            });
        },
        /**
         * Do a request and cache the result.
         * If the function is called again with the same url, the previous result will be returned.
         * @param url{string}
         * @param options{{cached: boolean, showError: boolean, updatesCache: boolean}}
         * @return {Promise}
         */
        get: function (url, options) {
            if (!options) {
                options = {};
            }
            if (options.cached === undefined) {
                options.cached = true;
            }
            if (!this._requestCache[url] || !options.cached) {
                this._requestCache[url] = this.request(url, 'get', null, options);
            }
            return this._requestCache[url];
        },
        post: function (url, data, options) {
            var request = this.request(url, 'post', data, options);
            // Update cache if updatesCache option is set, get and post must use the same url.
            if (options && options.updatesCache) {
                this._requestCache[url] = request;
            }
            return request;
        },
        signup: function (data) {
            return this.post('/vouchers/cirklo/signup', data, {showError: false});
        }
    };
    var requests = new RequestsService();

    var formElem = $('#signup_form')[0];
    var tabs = [];
    var currentStep = 0;
    var recaptchaLoader = new RecaptchaLoader({
        container: 'recaptcha_container',
    });

    $('form').submit(function (event) {
        event.preventDefault();
    });

    init();

    function init() {
        $('#signup').click(signup);
        $('#next').click(nextStep);
        $('#back').click(previousStep);

        $('#language').change(languageChanged);
        $('#app').change(appSelected);
        $('select').change(validateInput);
        $('input[type!=checkbox][type!=radio]').each(function () {
            var input = this;
            sln.configureDelayedInput($(input), function () {
                validateInput(input);
            }, null, false, 1000);
        });
        setTabs();
    }

    function setTabs() {
        tabs = [];
        for (var i = 0; i <= 2; i++) {
            tabs.push($('#tab' + i));
        }
    }

    function getSelectedApp() {
        var appElem = $('#app option:selected');
        if (!appElem || !appElem.val()) {
            return null;
        }
        return {
            city_id: appElem.val().trim(),
            name: appElem.text().trim(),
            logo_url: appElem.attr('logo_url')
        };
    }

    function appSelected() {
        var app = getSelectedApp();
        if (!app) {
            return;
        }

        var logoElem = $('#tab1_city_logo');
        if (app.logo_url === undefined) {
        	logoElem.hide();
        } else {
	        logoElem.attr('src', app.logo_url);
        	logoElem.show();
        }
    }

    function gatherFromInputs(divName) {
        var result = {};

        $('#' + divName + ' input').each(function (i, el) {
            var fieldName = $(el).attr('id').replace(divName + '_', '');
            result[fieldName] = $(el).val().trim();
        });

        return result;
    }

    function getSignupDetails(recaptchaToken) {
        return new Promise(function (resolve, reject) {
            var app = getSelectedApp();
            var language = getSelectedLanguage();
            var args = {
            	city_id: app.city_id,
                company: gatherFromInputs('enterprise'),
                recaptcha_token: recaptchaToken,
                language: language
            };
            resolve(args);
        });
    }

    function doSignup() {
        sln.hideProcessing();
        recaptchaLoader.execute();
    }

    recaptchaLoader.onLoadCallback = doSignup;

    function signup() {
        // validate first
        nextStep();
        if (!formElem.checkValidity()) {
            return;
        }
        // load captcha challenge if not loaded
        if (recaptchaLoader.isLoaded()) {
            doSignup();
        } else {
            sln.showProcessing(SignupTranslations.LOADING_CAPTCHA_CHALLENGE);
            recaptchaLoader.load();
        }
    }

    window.signupCallback = function (recaptchaToken) {
        sln.showProcessing(CommonTranslations.SUBMITTING_DOT_DOT_DOT);
        getSignupDetails(recaptchaToken).then(function (signupDetails) {
            requests.signup(signupDetails).then(function (result) {
           		sln.hideProcessing();
            	if (result.success) {
            		$('#signup_note').hide();
                	$('#signup_box').hide();
                	$('#signup_success').show();
            	} else {
            		sln.alert(result.errormsg, null, CommonTranslations.ERROR);
            	}
            }).catch(function (error) {            	
                sln.hideProcessing();
                var err = error.data.responseJSON;
                var msg = err.error;
                if(err.data && err.data.url){
                    msg += '<br>' + `<a href="` + err.data.url + '">' + err.data.label + '</a>';
                }
                sln.alert(msg, null, CommonTranslations.ERROR);
            });
        });

        recaptchaLoader.reset();
    };

    function getCurrentTab() {
        return tabs[currentStep];
    }

    function isLastStep() {
        return currentStep >= tabs.length - 1;
    }

    function isFirstStep() {
        return currentStep <= 0;
    }

    function nextStep() {
        if (!validateInputs(getCurrentTab()) || isLastStep()) {
            return;
        }
        stepChanged(currentStep + 1);
    }

    function previousStep() {
        if (isFirstStep()) {
            return;
        }
        stepChanged(currentStep - 1);
    }

    function stepChanged(step) {
        getCurrentTab().hide();
        currentStep = step;
        getCurrentTab().show();
        getCurrentTab().find('input').first().focus();
        showHideButtons();
    }

    function languageChanged() {
        window.location.href = window.location.pathname + '?language=' + getSelectedLanguage();
    }

    function getSelectedLanguage() {
        return $('#language').val() || getBrowserLanguage();
    }

    function showHideButtons() {
        if (isLastStep()) {
            $('#signup').show();
            $('#next').hide();
        } else {
            $('#signup').hide();
            $('#next').show();
        }

        if (isFirstStep()) {
            $('#back').hide();
        } else {
            $('#back').show();
        }
    }

    $(window).keydown(function (event) {
        // if enter is pressed and is not the last step
        // then go the next step
        if (event.keyCode === 13) {
            if (isLastStep()) {
                signup();
            } else {
                event.preventDefault();
                nextStep();
            }
        }
    });
});
