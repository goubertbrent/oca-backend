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
                    error: function () {
                        if (options.showError) {
                            sln.showAjaxError();
                        }
                        reject();
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
        getAppInfo: function (appId, language, options) {
            return this.get('/unauthenticated/osa/signup/app-info/' + appId + '?language=' + language, options);
        }
    }
    var requests = new RequestsService();

    var TMPL_ORG_TYPE = '<div class="radio">'
        + '<label><input type="radio" name="organization_type" value="${value}" {{if checked}}checked{{/if}}>${label}</label>'
        + '</div>';

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
        var vatInput = $('#enterprise_vat');
        sln.configureDelayedInput(vatInput, function () {
            validateVat(vatInput);
        }, null, false, 3000, true);

        for (var i = 0; i <= 4; i++) {
            tabs.push($('#tab' + i));
        }
        if (typeof SIGNUP_APP_ID !== 'undefined' && SIGNUP_APP_ID) {
            appSelected();
        }
    }

    function setEditableOrganizationTypes(types) {
        $('#organization_types div[class=radio]').remove();
        $('#organization_types').show();

        var selectFirstType = true;
        var controlsContainer = $('#organization_types > div[class=controls]');
        $.each(types, function (type, label) {
            controlsContainer.append(
                $.tmpl(TMPL_ORG_TYPE, {
                    value: type,
                    label: label,
                    checked: selectFirstType
                })
            );
            selectFirstType = false;
        });
    }

    function getSelectedApp() {
        var appElem = $('#app option:selected');
        if (!appElem || !appElem.val()) {
            return null;
        }
        return {
            app_id: appElem.val().trim(),
            name: appElem.text().trim(),
        };
    }

    function appSelected() {
        var app = getSelectedApp();
        if (!app) {
            return;
        }
        $('#next').attr('disabled', true);

        requests.getAppInfo(app.app_id, getSelectedLanguage()).then(function (appInfo) {
            setEditableOrganizationTypes(appInfo.organization_types);
            $('#next').attr('disabled', false);
        });
    }

    function fillInput(inputId, value) {
        var input = $('#' + inputId);
        if (!input.val().trim()) {
            input.val(value);
        }
    }

    function copyInput(inputIdFrom, inputIdTo) {
        var value = $('#' + inputIdFrom).val();
        fillInput(inputIdTo, value);
    }

    function clearErrors(input) {
        input.next('p[class=text-error], [class=text-warning]').remove();
    }

    function validateVat(input) {
        var vat = input.val().replace(/\s/g, '');
        if (!vat) {
            // clear any prev errors/warnings
            clearErrors(input);
            return;
        }
        requests.getAppInfo(getSelectedApp().app_id, getSelectedLanguage()).then(function (appInfo) {
            var country = appInfo.customer.country;
            if (isDigit(vat[0])) {
                vat = country + vat;
            }

            $('#next').attr('disabled', true);
            sln.call({
                url: '/unauthenticated/osa/company/info',
                type: 'get',
                data: {
                    vat: vat,
                    country: country
                },
                success: function (data) {
                    var errorMessage, warningMessage;
                    if (data.errormsg && !data.vat) {
                        errorMessage = SignupTranslations.VAT_INVALID;
                    } else if (data.errormsg && data.vat) {
                        // vat format is valid, but it's unknown
                        warningMessage = SignupTranslations.VAT_UNKNOWN;
                    } else if (data.country.toUpperCase() !== country) {
                        errorMessage = SignupTranslations.VAT_INCORRECT_COUNTRY;
                    } else {
                        fillInput('enterprise_name', data.name);
                        fillInput('enterprise_address1', data.address1 + (data.address2 ? ', ' + data.address2 : ''));
                        fillInput('enterprise_zip_code', data.zip_code);
                        fillInput('enterprise_city', data.city);
                    }

                    if (data.vat) {
                        $('#enterprise_vat').val(data.vat);
                    }

                    $('#next').attr('disabled', false);
                    clearErrors(input);
                    if (errorMessage) {
                        $('<p class="text-error">' + errorMessage + '</p>').insertAfter(input);
                    } else if (warningMessage) {
                        $('<p class="text-warning">' + warningMessage + '</p>').insertAfter(input);
                    }
                },
                error: function () {
                    $('#next').attr('disabled', false);
                    sln.showAjaxError();
                }
            });
        });
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
            requests.getAppInfo(app.app_id, language).then(function (appInfo) {
                var args = {
                    city_customer_id: appInfo.customer.id,
                    company: gatherFromInputs('enterprise'),
                    customer: gatherFromInputs('contact'),
                    recaptcha_token: recaptchaToken,
                    email_consents: {
                        email_marketing: $('#email_consents_email_marketing').prop('checked'),
                        newsletter: $('#email_consents_newsletter').prop('checked'),
                    }
                };
                args.customer.language = language;
                args.company.organization_type = parseInt($('input[name=organization_type]:checked').val());
                resolve(args);
            });
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
        if (isLastStep()) {
            var elem = $('#agree-to-toc');
            if (elem.prop('disabled') || !elem[0].checkValidity()) {
                $('<p class="text-error">' + SignupTranslations.PLEASE_AGREE_TO_TOC + '</p>').insertAfter(elem);
                return;
            }
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
            sln.call({
                url: '/unauthenticated/osa/customer/signup',
                type: 'POST',
                data: signupDetails,
                success: function (result) {
                    sln.hideProcessing();
                    if (!result.success) {
                        var message = SignupTranslations[result.errormsg.toUpperCase()] || result.errormsg;
                        sln.alert(message, null, CommonTranslations.ERROR);
                    } else {
                        $('#signup_note').parent().addClass('white-box');
                        $('#signup_note').html(SignupTranslations.SIGNUP_SUCCCESS);
                        $('#signup_box').hide();
                        $('#go_back').show();
                    }
                },
                error: sln.showAjaxError
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
        if (currentStep === 2) {
            var vatError = $('#enterprise_vat').next('p[class=text-error]');
            if (vatError.length) {
                return;
            }
        }

        if (!validateInputs(getCurrentTab()) || isLastStep()) {
            return;
        }

        if (isFirstStep()) {
            // redirect to the signup page if the user already in/have an app
            if ($('input[name=already_in_app]:checked').val() === 'yes') {
                // Preserve app id in url
                window.location.pathname = window.location.pathname.replace('signup', 'signin');
                return;
            }
        }

        var selectedApp = getSelectedApp();
        if (currentStep === 0 && selectedApp) {
            requests.getAppInfo(selectedApp.app_id, getSelectedLanguage()).then(function (appInfo) {
                if (Object.keys(appInfo.organization_types).length === 1) {
                    stepChanged(currentStep + 2);
                } else {
                    stepChanged(currentStep + 1);
                }
            });
        } else {
            stepChanged(currentStep + 1);
        }
    }

    function previousStep() {
        if (isFirstStep()) {
            return;
        }
        if (currentStep === 2) {
            requests.getAppInfo(getSelectedApp().app_id, getSelectedLanguage()).then(function (appInfo) {
                if (Object.keys(appInfo.organization_types).length === 1) {
                    stepChanged(currentStep - 2);
                } else {
                    stepChanged(currentStep - 1);
                }
            });
        } else {
            stepChanged(currentStep - 1);
        }
    }

    function stepChanged(step) {
        getCurrentTab().hide();
        currentStep = step;
        getCurrentTab().show();
        getCurrentTab().find('input').first().focus();
        showHideButtons();

        /* refill some info from the previous one */
        if (currentStep === 2) {
            var city = getSelectedApp().name;
            fillInput('enterprise_city', city);
            fillInput('contact_city', city);
        }

        if (currentStep === 3) {
            copyInput('enterprise_user_email', 'contact_user_email');
            copyInput('enterprise_telephone', 'contact_telephone');
        }
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
        if (event.keyCode == 13) {
            if (!isLastStep()) {
                event.preventDefault();
                nextStep();
            } else {
                signup();
            }
        }
    });

    $('.legal-all-versions').click(function (event) {
        // open all versions page in a new window
        event.preventDefault();
        window.open($(this).attr('href'), '_blank');
    });

});
