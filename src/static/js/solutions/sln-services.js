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
(function () {
    'use strict';
    var generatedOn, isWaitingForProvisionUpdate = false;
    LocalCache.services = {
        services: []
    };

    init();

    function init() {
        ROUTES['services'] = router;
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
                renderServicesList();
        }
    }

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

    /*
     Render methods
     */

    function renderServicesList() {
        getServiceConfiguration(function (config) {
            getServices(function (services) {
                var html = $.tmpl(templates['services/services'], {
                    services: services,
                    t: CommonTranslations,
                    modules: config.modules,
                    generatedOn: generatedOn ? sln.format(new Date(generatedOn * 1000)) : false
                });
                $('#services-content').html(html);
                $('button.delete-service').click(function () {
                    var $this = $(this);
                    var serviceEmail = $this.attr('service_email');
                    var serviceName = $this.attr('service_name');
                    var message = T('confirm_delete_service', {service_name: serviceName});
                    sln.confirm(message, function () {
                        deleteService(serviceEmail);
                    });
                });
                $('.service-icons>div').each(function () {
                    var $this = $(this);
                    if ($this.attr('disabled')) {
                        $this.attr('data-original-title', '(' + CommonTranslations.module_disabled + ') ' + $this.attr('data-original-title'));
                    }
                }).tooltip();
            });
        });
    }

    function deleteService(serviceEmail) {
        sln.call({
            url: '/common/services/delete',
            method: 'post',
            data: {
                service_email: serviceEmail
            },
            success: function (data) {
                if (data.success) {
                    serviceDeleted(serviceEmail);
                }
            }
        });
    }

    function serviceDeleted(serviceEmail) {
        LocalCache.services.services = LocalCache.services.services.filter(function (a) {
            return a.service_email !== serviceEmail;
        });
        renderServicesList();
    }

    function addBroadcastType() {
        var $this = $('#service-extra-broadcast-type');
        if ($this.val().length > 0) {
            $('#service-broadcast-types-container')
                .find('input[type=checkbox]:last')
                .parent()
                .after(
                    ' <label class="checkbox"><input type="checkbox" name="service-broadcast-types" value="'
                    + $this.val() + '" checked>' + $this.val() + '</label>'
                );
            $this.val('');
        }
    }

    function renderServicesFormInternal(mode) {
        getServiceConfiguration(function (config) {
            var broadcastTypes = config.broadcast_types,
                organizationTypes = config.organization_types;
            if (mode === 'edit') {
                broadcastTypes = currentService.broadcast_types;
            }
            var html = $.tmpl(templates['services/service_form'], {
                service: currentService,
                edit: mode === 'edit',
                modules: config.modules,
                organizationTypes: organizationTypes,
                broadcastTypes: broadcastTypes,
                languages: supportedLanguages,
                t: CommonTranslations
            });
            $('#services-content').html(html);
            $('#service-form').find('input').not('[type=checkbox], [type=select]').first().focus();
            $('#service-extra-broadcast-type-add').click(addBroadcastType);
            $('#service-extra-broadcast-type').keypress(function (e) {
                if (e.keyCode === 13) {
                    addBroadcastType();
                }
            });
            $('#service-submit').click(putService);
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
            vat: $('#service-vat').val()
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

    function getServices(callback) {
        if (LocalCache.services.services.length) {
            callback(LocalCache.services.services);
            return;
        }
        $('#services-content').html(TMPL_LOADING_SPINNER);
        sln.call({
            url: '/common/services/get_all',
            success: function (data) {
                LocalCache.services.services = data.services;
                generatedOn = data.generated_on;
                for (var i = 0; i < LocalCache.services.services.length; i++) {
                    var service = LocalCache.services.services[i];
                    service.statistics.lastQuestionAnsweredDate = sln.format(new Date(service.statistics.last_unanswered_question_timestamp * 1000));
                    service.hasAgenda = service.modules.indexOf('agenda') !== -1;
                    service.hasQA = service.modules.indexOf('ask_question') !== -1;
                    service.hasBroadcast = service.modules.indexOf('broadcast') !== -1;
                    service.hasStaticContent = service.modules.indexOf('static_content') !== -1;
                }
                callback(LocalCache.services.services);
            }
        });
    }

    function getService(serviceEmail, callback) {
        $('#services-content').html(TMPL_LOADING_SPINNER);
        sln.call({
            url: '/common/services/get',
            data: {service_email: serviceEmail},
            success: function (data) {
                currentService = data;
                currentService.service_email = serviceEmail;
                callback('edit');
            }
        });
    }


    function putService() {
        var formValues = getServiceFormValues();
        currentService = formValues;
        if(currentService.modules.indexOf('broadcast') !== -1 && !currentService.broadcast_types.length) {
            sln.alert(T('broadcast-type-required'), null, CommonTranslations.ERROR);
            return;
        }
        if (currentService.mode === 'edit') {
            formValues.service_email = currentService.service_email;
        }
        sln.showProcessing(CommonTranslations.SAVING_DOT_DOT_DOT);
        // Not registered on page load to prevent updates when multiple people are logged in on the same dashboard
        isWaitingForProvisionUpdate = true;
        sln.call({
            url: '/common/services/put',
            method: 'post',
            data: {data: JSON.stringify(formValues)},
            success: function (data) {
                if (data.errormsg) {
                    isWaitingForProvisionUpdate = false;
                    sln.hideProcessing();
                    sln.alert(data.errormsg, null, CommonTranslations.ERROR);
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

    function reloadServiceList() {
        LocalCache.services.services = [];
        window.location.hash = '#/services';
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
                sln.alert(msg, reloadServiceList, CommonTranslations.SUCCESS);
                break;
            case 'common.provision.failed':
                isWaitingForProvisionUpdate = false;
                sln.hideProcessing();
                sln.alert(CommonTranslations.ERROR, null, data.errormsg);
                break;
            case 'solutions.common.services.deleted':
                serviceDeleted(data.service_email);
                break;
        }
    }

    $(document).ready(function () {
        sln.registerMsgCallback(servicesChannelUpdates);
    });
})();
