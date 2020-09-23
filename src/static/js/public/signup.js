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
        getCommunityInfo: function (appId, language, options) {
            return this.get('/unauthenticated/osa/signup/community-info/' + appId + '?language=' + language, options);
        },
        getCommunities: function (country, options) {
            return this.get('/unauthenticated/osa/signup/communities/' + country, options);
        },
        getPrivacySettings: function (communityId, language) {
            return this.get('/unauthenticated/osa/signup/privacy-settings/' + communityId + '?language=' + language);
        },
        signup: function (data) {
            return this.post('/unauthenticated/osa/customer/signup', data, {showError: false});
        }
    };
    var requests = new RequestsService();

    var TMPL_ORG_TYPE = '<div class="radio">'
        + '<label><input type="radio" name="organization_type" value="${value}" {{if checked}}checked{{/if}}>${label}</label>'
        + '</div>';

    var TMPL_PRIVACY_CHECKBOX = '<label class="checkbox" for="privacy_${setting.type}">' +
        '<input type="checkbox" id="privacy_${setting.type}" name="${setting.type}" ' +
        '{{if setting.enabled}}checked{{/if}}>${setting.label}</label>';

    var formElem = $('#signup_form')[0];
    var tabs = [];
    var privacySettings = [];
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
        $('#community').change(communitySelected);
        $('#country').change(countrySelected);
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

        setTabs();
        if (typeof SIGNUP_APP_ID !== 'undefined' && SIGNUP_APP_ID) {
            communitySelected();
        }
    }

    function setTabs() {
        tabs = [];
        for (var i = 0; i <= 5; i++) {
            tabs.push($('#tab' + i));
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

    function getSelectedCommunity() {
        var communityElem = $('#community option:selected');
        if (!communityElem || !communityElem.val()) {
            return null;
        }
        return {
            id: communityElem.val().trim(),
            name: communityElem.text().trim(),
        };
    }

    function communitySelected() {
        var community = getSelectedCommunity();
        if (!community) {
            return;
        }
        $('#next').attr('disabled', true);

        requests.getCommunityInfo(community.id, getSelectedLanguage()).then(function (communityInfo) {
            setEditableOrganizationTypes(communityInfo.organization_types);
            $('#next').attr('disabled', false);
        });
    }

    function getSelectedCountry(){
        return $('#country').val();
    }

    function countrySelected(){
        var country = getSelectedCountry();
        if (!country) {
            return;
        }
        $('#community-select-parent').show();
        var communitySelect = $('#community');
        requests.getCommunities(country).then(function (communities) {
            communitySelect.empty();
            var emptyOption = document.createElement('option');
            emptyOption.innerText = '';
            communitySelect.append(emptyOption);
            for (var i = 0; i < communities.length; i++) {
                var community = communities[i];
                var option = document.createElement('option');
                option.value = community.id;
                option.innerText = community.name;
                communitySelect.append(option);
            }
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
        var country = getSelectedCountry();
        if (isDigit(vat[0])) {
            vat = country + vat;
        }
        $('#enterprise_vat').val(vat);
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
            var community = getSelectedCommunity();
            var language = getSelectedLanguage();
            requests.getCommunityInfo(community.id, language).then(function (communityInfo) {
                var consents = {};
                for (var i = 0; i < privacySettings.length; i++) {
                    var group = privacySettings[i];
                    for(var j =0;j<group.items.length;j++){
                        var s = group.items[j];
                        consents[s.type] = $('#privacy_' + s.type).prop('checked');
                    }
                }
                var args = {
                    city_customer_id: communityInfo.customer.id,
                    company: gatherFromInputs('enterprise'),
                    customer: gatherFromInputs('contact'),
                    recaptcha_token: recaptchaToken,
                    email_consents: consents,
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
            requests.signup(signupDetails).then(function () {
                sln.hideProcessing();
                $('#signup_note').parent().addClass('white-box');
                $('#signup_note').html(SignupTranslations.SIGNUP_SUCCCESS);
                $('#signup_box').hide();
                $('#go_back').show();
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

        var selectedCommunity = getSelectedCommunity();
        if (currentStep === 0 && selectedCommunity) {
            requests.getCommunityInfo(selectedCommunity.id, getSelectedLanguage()).then(function (communityInfo) {
                if (Object.keys(communityInfo.organization_types).length === 1) {
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
            requests.getCommunityInfo(getSelectedCommunity().id, getSelectedLanguage()).then(function (communityInfo) {
                if (Object.keys(communityInfo.organization_types).length === 1) {
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
            var selectedCommunity = getSelectedCommunity();
            var city = selectedCommunity.name;
            fillInput('enterprise_city', city);
            fillInput('contact_city', city);
            getPrivacySettings(selectedCommunity.id);
        }

        if (currentStep === 3) {
            copyInput('enterprise_user_email', 'contact_user_email');
            copyInput('enterprise_telephone', 'contact_telephone');
        }
    }

    function getPrivacySettings(communityId) {
        return requests.getPrivacySettings(communityId, getSelectedLanguage()).then(function (settings) {
            privacySettings = settings;
            var container1 = $('#privacy-settings-1');
            var container2 = $('#privacy-settings-2');
            container1.empty();
            container2.empty();
            for (var i = 0; i < settings.length; i++) {
                var group = settings[i];
                var container;
                if(group.page ===1){
                    container = container1;
                }else if(group.page===2){
                    container = container2;
                }else{
                    continue;
                }
                container.append(group.description);
                for (var j = 0; j < group.items.length; j++) {
                    var setting = group.items[j];
                    container.append($.tmpl(TMPL_PRIVACY_CHECKBOX, {setting: setting}));
                }
            }
            setTabs();
            var hasCirklo = settings.some(function (group) {
                return group.items.some(function(item){
                    return item.type === 'cirklo_share';
                });
            });
            if(!hasCirklo) {
                // Remove last tab
                tabs.pop();
            }
        });
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
