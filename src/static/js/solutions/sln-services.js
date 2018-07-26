/*
 * Copyright 2018 Mobicage NV
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
 * @@license_version:1.3@@
 */
(function () {
    'use strict';
    var isWaitingForProvisionUpdate = false;
    var servicesLists = {};
    var searchDict = {};

    LocalCache.services = {
        services: {}
    };

    init();

    function init() {
        initServicesList();
        $('.search-services').click(searchServices);
        ROUTES.services = router;
    }

    function router(urlHash) {
        var page = urlHash[1];
        if (['add', 'edit', 'overview'].indexOf(page) === -1) {
            page = 'overview';
            window.location.hash = '#/' + urlHash[0] + '/' + page;
            return;
        }
        switch (page) {
            case 'add':
                renderServicesForm(urlHash[1]);
                break;
            case 'edit':
                renderServicesForm(urlHash[1], urlHash[2]);
                break;
            default:
                loadServices();
        }
    }

    // only one service can be created/updated at a time
    var currentService = {};
    var supportedLanguages = [
        {code: 'nl', name: 'Dutch', default: true},
        {code: 'en', name: 'English'},
        {code: 'fr', name: 'French'},
        {code: 'de', name: 'German'},
        {code: 'ro', name: 'Romanian'},
        {code: 'es', name: 'Spanish'},
        {code: 'ru', name: 'Russian'}
    ];

    function initServicesList() {
        $('.services-list').each(function(i, container) {
            var organizationType = parseInt($(this).attr('organization_type'));
            servicesLists[organizationType] = new ServicesList(organizationType, $(container));
        });
    }

    function getSelectedOrganizationType() {
        var activeCategory = $('#services_tab li[class=active]');
        return parseInt(activeCategory.attr('organization_type'));
    }

    function getCurrentServicesList() {
        var organizationType = getSelectedOrganizationType();
        var currentServicesList = servicesLists[organizationType];
        return currentServicesList;
    }

    function getCurrentServicesContainer() {
        return getCurrentServicesList().servicesContainer;
    }

    function loadServices() {
        $('#service-form-container').hide();
        $('#services-list-container').show();
        var servicesList = getCurrentServicesList();
        if(servicesList) {
            servicesList.servicesContainer.show();
            servicesList.reloadServices();
        }
    }

    function reloadAllServices() {
        $.each(servicesLists, function(organizationType, servicesList) {
            servicesList.reset(); // to reload later
        });
        // reload
        window.location.hash = '#/services';
    }


    $('#services_tab a[data-toggle="tab"]').on('shown', function() {
        // load the services of the selected tab when clicked
        // via the router
        window.location.hash = '#/services';
    });

    function addBroadcastType() {
        var $this = $('#service-extra-broadcast-type');
        if ($this.val().length > 0) {
            $('#service-extra-broadcast-type').before(
                    ' <label class="checkbox"><input type="checkbox" name="service-broadcast-types" value="'
                    + $this.val() + '" checked>' + $this.val() + '</label>'
                );
            $this.val('');
        }
    }

    function renderServicesFormInternal(mode) {
        $('#services-list-container').hide();
        $('#service-form-container').show();

        var organizationType;
        if(currentService && currentService.organization_type) {
            // pre-selected organization type
            organizationType = currentService.organization_type;
        } else {
            organizationType = getSelectedOrganizationType();
        }

        getServiceConfiguration(function (config) {
            var broadcastTypes = config.broadcast_types;
            if (mode === 'edit') {
                broadcastTypes = currentService.broadcast_types;
            }
            var html = $.tmpl(templates['services/service_form'], {
                service: currentService,
                edit: mode === 'edit',
                modules: config.modules,
                organizationType: organizationType,
                organizationTypes: ORGANIZATION_TYPES,
                broadcastTypes: broadcastTypes,
                languages: supportedLanguages,
                t: CommonTranslations
            });
            $('#service-form-container').html(html);

            $('#service-form').find('input').not('[type=checkbox], [type=select]').first().focus();
            $('#service-extra-broadcast-type-add').click(addBroadcastType);
            $('#service-extra-broadcast-type').keypress(function (e) {
                if (e.keyCode === 13) {
                    addBroadcastType();
                }
            });

            var checkNoWebsite = $('#check-no-website'),
                checkNoFacebookPage = $('#check-no-facebook-page');

            checkNoWebsite.change(function() {
                if(checkNoWebsite.is(':checked')) {
                    $('#service-website').attr('disabled', true);
                } else {
                    $('#service-website').attr('disabled', false);
                }
            });
            checkNoFacebookPage.change(function() {
                if(checkNoFacebookPage.is(':checked')) {
                    $('#service-facebook-page').attr('disabled', true);
                } else {
                    $('#service-facebook-page').attr('disabled', false);
                }
            });
            $('#service-submit').click(function() {
                putService(false);
            });
        });
    }

    function renderServicesForm(mode, serviceEmail) {
        currentService = {mode: mode};
        if (mode === 'edit') {
            getService(serviceEmail, renderServicesFormInternal);
        } else {
            renderServicesFormInternal('new');
        }
    }

    function getServiceFormValues() {
        var serviceModules = [], serviceBroadcastTypes = [];
        $('#service-modules-container').find('input[type=checkbox]:checked').each(function () {
            serviceModules.push($(this).val());
        });
        $('#service-broadcast-types-container').find('input[type=checkbox]:checked').each(function () {
            serviceBroadcastTypes.push($(this).val());
        });
        return {
            customer_id: currentService.customer_id,
            name: $('#service-name').val(),
            address1: $('#service-address1').val(),
            address2: $('#service-address2').val(),
            zip_code: $('#service-zip').val(),
            city: $('#service-city').val(),
            user_email: $('#service-email').val(),
            telephone: $('#service-phone').val(),
            language: $('#service-language').val(),
            modules: serviceModules,
            broadcast_types: serviceBroadcastTypes,
            organization_type: parseInt($('#organization_type').val()),
            vat: $('#service-vat').val(),
            website: $('#service-website').val(),
            facebook_page: $('#service-facebook-page').val()
        };
    }

    /*
     Ajax calls
     */

    function getServiceConfiguration(callback) {
        if (LocalCache.services.config) {
            callback(LocalCache.services.config);
        } else {
            sln.call({
                url: '/common/services/get_defaults',
                success: function (data) {
                    LocalCache.services.config = data;
                    callback(LocalCache.services.config);
                }
            });
        }
    }


    function getService(serviceEmail, callback) {
        getCurrentServicesContainer().html(TMPL_LOADING_SPINNER);
        sln.call({
            url: '/common/services/get',
            data: {service_email: serviceEmail},
            success: function (data) {
                if(data.hasOwnProperty('success') && !data.success) {
                    sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    return;
                }
                currentService = data;
                currentService.service_email = serviceEmail;
                callback('edit');
            },
        });
    }


    function putService(force) {
        var formValues = getServiceFormValues();
        currentService = formValues;
        if(currentService.modules.indexOf('broadcast') !== -1 && !currentService.broadcast_types.length) {
            sln.alert(T('broadcast-type-required'), null, CommonTranslations.ERROR);
            return;
        }
        if (currentService.mode === 'edit') {
            formValues.service_email = currentService.service_email;
        }

        var requireWebsite, requireFacebook;
        requireWebsite = !($('#check-no-website').is(':checked'));
        requireFacebook  = !($('#check-no-facebook-page').is(':checked'));
        if(!requireWebsite) {
            currentService.website = null;
        } else if(requireWebsite && currentService.website.trim() === '') {
            sln.alert(T('website-required'), null, CommonTranslations.ERROR);
            return;
        }
        if(!requireFacebook) {
            currentService.facebook_page = null;
        } else if(requireFacebook && currentService.facebook_page.trim() === '') {
            sln.alert(T('Facebook-page-required'), null, CommonTranslations.ERROR);
            return;
        }

        sln.showProcessing(CommonTranslations.SAVING_DOT_DOT_DOT);
        // Not registered on page load to prevent updates when multiple people are logged in on the same dashboard
        isWaitingForProvisionUpdate = true;
        currentService['force'] = force;
        sln.call({
            url: '/common/services/put',
            method: 'post',
            data: {data: JSON.stringify(formValues)},
            success: function (data) {
                if(!data.success) {
                    isWaitingForProvisionUpdate = false;
                    sln.hideProcessing();

                    if (data.errormsg) {
                        sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    } else if(data.warningmsg) {
                        // just show the warning with the confirmation
                        sln.confirm(data.warningmsg, function() {
                            putService(true);
                        });
                    }
                }
                // else: successfully created service, but still provisioning. Channel update will tell us when it's done.
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                isWaitingForProvisionUpdate = false;
                sln.hideProcessing();
                sln.showAjaxError(XMLHttpRequest, textStatus, errorThrown);
            }
        });
    }

    function searchServices() {
        var html = $.tmpl(templates['services/service_search'], {
            title: CommonTranslations.Search,
            placeholder: CommonTranslations.ENTER_DOT_DOT_DOT
        });
        var modal = sln.createModal(html, function(modal) {
            $('#service_name_input', modal).focus();
        });
        var input = $('#service_name_input', modal);

        function serviceSelected(service_email) {
            input.val('');
            modal.modal('hide');
            window.location.hash = '#/services/edit/' + service_email;
        }

        sln.serviceSearch(input, ORGANIZATION_TYPES, null, serviceSelected);
    }

    function servicesChannelUpdates(data) {
        if (!isWaitingForProvisionUpdate && data.type !== 'solutions.common.services.deleted') {
            return;
        }
        switch (data.type) {
            case 'common.provision.success':
                isWaitingForProvisionUpdate = false;
                sln.hideProcessing();
                var msg = T(currentService.customer_id ? 'service_updated' : 'service_created');
                sln.alert(msg, reloadAllServices, CommonTranslations.SUCCESS);
                break;
            case 'common.provision.failed':
                isWaitingForProvisionUpdate = false;
                sln.hideProcessing();
                sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                break;
            case 'solutions.common.services.deleted':
                var organizationType = data.service_organization_type;
                if(servicesLists[organizationType]) {
                    servicesLists[organizationType].serviceDeleted(data.service_email);
                }
                break;
        }
    }

    $(document).ready(function () {
        sln.registerMsgCallback(servicesChannelUpdates);
    });
})();
