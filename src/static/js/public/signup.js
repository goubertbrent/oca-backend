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

var signupCallback;

(function() {
    'use strict';

    var TMPL_ORG_TYPE = '<div class="radio">'
        + '<label><input type="radio" name="organization_type" value="${value}" {{if checked}}checked{{/if}}>${label}</label>'
        + '</div>';

    var formElem = $('#signup_form')[0];
    var tabs = [];
    var currentStep = 0;
    var orgTypesCache = {};

    $('form').submit(function(event){
      event.preventDefault();
    });

    init();

    function init() {
        $('#signup').click(signup);
        $('#next').click(nextStep);
        $('#back').click(previousStep);

        $('#city').change(customerSelected);
        $('select').change(validateInput);
        $('input[type!=checkbox][type!=radio]').keyup(function() {
            var input = this;
            sln.configureDelayedInput($(input), function() {
                validateInput(input);
            }, null, false, 1000);
        });

        for(var i = 0; i <= 2; i++) {
            tabs.push($('#tab' + i));
        }
    }

    function setEditableOrganizationTypes(types) {
        $('#organization_types div[class=radio').remove();
        $('#organization_types').show();

        var selectFirstType = true;
        $.each(types, function(type, label) {
            $('#organization_types > div[class=controls]').append(
                $.tmpl(TMPL_ORG_TYPE, {
                    value: type,
                    label: label,
                    checked: selectFirstType
                })
            );
            selectFirstType = false;
        });
    }

    function customerSelected() {
        var customerId = $('#city').val().trim();
        if(customerId) {
            $('#signup_form').attr('customer', customerId);

            // get editable organization types
            if(orgTypesCache[customerId]) {
                setEditableOrganizationTypes(orgTypesCache[customerId]);
            } else {
                $('#next').attr('disabled', true);
                sln.call({
                    url: '/unauthenticated/osa/customer/org/types',
                    type: 'GET',
                    data: {
                        customer_id: parseInt(customerId),
                        language: getBrowserLanguage()
                    },
                    success: function(data) {
                        setEditableOrganizationTypes(data);
                        orgTypesCache[customerId] = data;
                        $('#next').attr('disabled', false);
                    },
                    error: function() {
                        $('#next').attr('disabled', false);
                        sln.showAjaxError();
                    }
                });
            }
        } else {
            $('#organization_types').hide();
        }
    }

    function gatherFromInputs(divName) {
        var result = {};

        $('#' + divName + ' input').each(function(i, el) {
            var fieldName = $(el).attr('id').replace(divName + '_', '');
            result[fieldName] = $(el).val();
        });

        return result;
    }

    function getSignupDetails(recaptchaToken) {
        var args = {};

        args.city_customer_id = parseInt($('#signup_form').attr('customer'));
        args.company = gatherFromInputs('enterprise');
        args.company.organization_type = parseInt($('input[name=organization_type]:checked').val());
        args.customer = gatherFromInputs('entrepreneur');
        args.customer.language = getBrowserLanguage();
        args.recaptcha_token = recaptchaToken;

        return args;
    }

    function signup() {
        // validate first
        nextStep();
        if(formElem.checkValidity()) {
            grecaptcha.execute();
        }
    }

    signupCallback = function(recaptchaToken) {
        sln.showProcessing(CommonTranslations.SUBMITTING_DOT_DOT_DOT);
        sln.call({
            url: '/unauthenticated/osa/customer/signup',
            type: 'POST',
            data: getSignupDetails(recaptchaToken),
            success: function(result) {
                sln.hideProcessing();
                if(!result.success) {
                    sln.alert(result.errormsg, null, CommonTranslations.ERROR);
                } else {
                    $('#signup_note').text(SignupTranslations.SIGNUP_SUCCCESS);
                    $('#signup_box').hide();
                }
            },
            error: function() {
                sln.hideProcessing();
                sln.showAjaxError();
            }
        });

        grecaptcha.reset();
    };

    function getCurrentTab() {
        return  tabs[currentStep];
    }

    function isLastStep() {
        return currentStep >= tabs.length - 1;
    }

    function isFirstStep() {
        return currentStep <= 0;
    }

    function nextStep() {
        if(!validateInputs(getCurrentTab()) || isLastStep()) {
            return;
        }

        stepChanged(currentStep + 1);
    }

    function previousStep() {
        if(isFirstStep()) {
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

        /* refill some info from the previous one */
        if(currentStep == 1) {
            var city = $('#city option:selected').attr('city');
            $('#enterprise_city').val(city);
        }
        if(currentStep == 2) {
            var enterprise_details = gatherFromInputs('enterprise');
            $.each(enterprise_details, function(field_name, value) {
                $('#entrepreneur input[id=entrepreneur_' + field_name + ']').val(value);
            });
        }
    }

    function showHideButtons() {
        if(isLastStep()) {
            $('#signup').show();
            $('#next').hide();
        } else {
            $('#signup').hide();
            $('#next').show();
        }

        if(isFirstStep()) {
            $('#back').hide();
        } else {
            $('#back').show();
        }
    }

    $(window).keydown(function(event) {
        // if enter is pressed and is not the last step
        // then go the next step
        if(event.keyCode == 13) {
            if(!isLastStep()) {
                event.preventDefault();
                nextStep();
            } else {
                signup();
            }
        }
    });

})();
