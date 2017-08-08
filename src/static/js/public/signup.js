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

$(function() {
    'use strict';

    var TMPL_ORG_TYPE = '<div class="radio">'
        + '<label><input type="radio" name="organization_type" value="${value}" {{if checked}}checked{{/if}}>${label}</label>'
        + '</div>';

    var TMPL_SERVICE_SECTOR = '<div class="radio">'
        + '<label><input type="radio" name="service_sector" value="${value}" {{if checked}}checked{{/if}}>${label}</label>'
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

        $('#app').change(customerSelected);
        $('select').change(validateInput);
        $('input[type!=checkbox][type!=radio]').each(function() {
            var input = this;
            sln.configureDelayedInput($(input), function() {
                validateInput(input);
            }, null, false, 1000);
        });
        var vatInput = $('#enterprise_vat');
        sln.configureDelayedInput(vatInput, function() {
            validateVat(vatInput);
        }, null, false, 500, true);

        for(var i = 0; i <= 3; i++) {
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

    function setServiceSectors(sectors) {
        if(!Object.keys(sectors).length) {
            $('#service_sectors').hide();
            return;
        }
        $('#service_sectors div[class=radio').remove();
        $('#service_sectors').show();

        var selectFirstType = true;
        $.each(sectors, function(name, title) {
            $('#service_sectors > div[class=controls]').append(
                $.tmpl(TMPL_SERVICE_SECTOR, {
                    value: name,
                    label: title,
                    checked: selectFirstType
                })
            );
            selectFirstType = false;
        });
    }

    function customerSelected() {
        var customerId = $('#app option:selected').attr('customer_id');
        if(customerId) {
            $('#signup_form').attr('customer', customerId);

            // get editable organization types
            if(orgTypesCache[customerId]) {
                setEditableOrganizationTypes(orgTypesCache[customerId].organization_types);
                setServiceSectors(orgTypesCache[customerId].sectors)
            } else {
                $('#next').attr('disabled', true);
                sln.call({
                    url: '/unauthenticated/osa/customer/org/types',
                    type: 'GET',
                    data: {
                        customer_id: parseInt(customerId)
                    },
                    success: function(data) {
                        setEditableOrganizationTypes(data.organization_types);
                        setServiceSectors(data.sectors);
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
            $('#service_sector').hide();
        }
    }

    function validateVat(input) {
        var vat = input.val().replace(/\s/g,'');

        input.next('p[class=text-error]').remove();
        if(!vat) {
            $('#next').attr('disabled', false);
            return;
        } else {
            $('#next').attr('disabled', true);
        }

        sln.call({
            url: '/unauthenticated/osa/company/info',
            type: 'get',
            data: {
                vat: vat
            },
            success: function(data) {
                var country, errorMessage;
                var country = $('#app option:selected').attr('country').toLowerCase();
                if(data.errormsg) {
                    // vat is invalid
                    errorMessage = SignupTranslations.VAT_INVALID;
                } else if(data.country.toLowerCase() !== country) {
                    errorMessage = SignupTranslations.VAT_INCORRECT_COUNTRY;
                } else {
                    var enterpriseDetails = gatherFromInputs('enterprise');
                    if(!enterpriseDetails.name) {
                        $('#enterprise_name').val(data.name);
                    }
                    if(!enterpriseDetails.address1) {
                        var address = data.address1;
                        if(data.address2) {
                            address += ', ' + data.address2;
                        }
                        $('#enterprise_address1').val(address);
                    }
                    if(!enterpriseDetails.zip_code) {
                        $('#enterprise_zip_code').val(data.zip_code);
                    }
                    if(!enterpriseDetails.city) {
                        $('#enterprise_city').val(data.city);
                    }
                    $('#next').attr('disabled', false);
                }

                if(errorMessage) {
                    $('<p class="text-error">' + errorMessage + '</p>').insertAfter(input);
                }
            },
            error: sln.showAjaxError
        });
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
        args.company.sector = $('input[name=service_sector]:checked').val();
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
                    var email = gatherFromInputs('entrepreneur').user_email;
                    $('#signup_note').text(SignupTranslations.SIGNUP_SUCCCESS.replace('%(email)s', email));
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

        if(isFirstStep()) {
            // redirect to the signup page if the user already in/have an app
            if($('input[name=already_in_app]:checked').val() === 'yes') {
                window.location = '/customers/signin';
                return;
            }
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
        if(currentStep === 2) {
            var city = $('#app option:selected').attr('city');
            if(!$('#enterprise_city').val()) {
                $('#enterprise_city').val(city);
            }
        }
        if(currentStep === 3) {
            var city = $('#enterprise_city').val();
            if(!$('#entrepreneur_city').val()) {
                $('#entrepreneur_city').val(city);
            }
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

});
