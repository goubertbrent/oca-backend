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
    var associations = [], generatedOn, isWaitingForProvisionUpdate = false;
    LocalCache.associations = {};

    init();

    function init() {
        ROUTES['associations'] = router;
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
                renderAssociationsForm(urlHash[1]);
                break;
            case 'edit':
                renderAssociationsForm(urlHash[1], urlHash[2]);
                break;
            default:
                renderAssociationsList();
        }
    }

    var currentAssociation = {};
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

    function renderAssociationsList() {
        getAssociationConfiguration(function (config) {
            getAssociations(function (associations) {
                var html = $.tmpl(templates['associations/association'], {
                    associations: associations,
                    t: CommonTranslations,
                    modules: config.modules,
                    generatedOn: generatedOn ? sln.format(new Date(generatedOn * 1000)) : false
                });
                $('#associations-content').html(html);
                $('button.delete-association').click(function () {
                    var $this = $(this);
                    var serviceEmail = $this.attr('service_email');
                    var serviceName = $this.attr('service_name');
                    var message = CommonTranslations.confirm_delete_association.replace('%(association_name)s', serviceName);
                    sln.confirm(message, function () {
                        deleteAssociation(serviceEmail);
                    });
                });
                $('.association-icons>div').each(function () {
                    var $this = $(this);
                    if ($this.attr('disabled')) {
                        $this.attr('data-original-title', '(' + CommonTranslations.module_disabled + ') ' + $this.attr('data-original-title'));
                    }
                }).tooltip();
            });
        });
    }

    function deleteAssociation(serviceEmail) {
        sln.call({
            url: '/common/associations/delete',
            method: 'post',
            data: {
                service_email: serviceEmail
            },
            success: function (data) {
                if (data.success) {
                    associationDeleted(serviceEmail);
                }
            }
        });
    }

    function associationDeleted(serviceEmail) {
        associations = associations.filter(function (a) {
            return a.service_email !== serviceEmail;
        });
        renderAssociationsList();
    }

    function addBroadcastType() {
        var $this = $('#association-extra-broadcast-type');
        if ($this.val().length > 0) {
            $('#association-broadcast-types-container')
                .find('input[type=checkbox]:last')
                .parent()
                .after(
                    ' <label class="checkbox"><input type="checkbox" name="association-broadcast-types" value="'
                    + $this.val() + '" checked>' + $this.val() + '</label>'
                );
            $this.val('');
        }
    }

    function renderAssociationsFormInternal(mode) {
        getAssociationConfiguration(function (config) {
            var broadcastTypes = config.broadcast_types;
            if (mode === 'edit') {
                broadcastTypes = currentAssociation.broadcast_types;
            }
            var html = $.tmpl(templates['associations/association_form'], {
                association: currentAssociation,
                edit: mode === 'edit',
                modules: config.modules,
                broadcastTypes: broadcastTypes,
                languages: supportedLanguages,
                t: CommonTranslations
            });
            $('#associations-content').html(html);
            $('#association-form').find('input').not('[type=checkbox], [type=select]').first().focus();
            $('#association-extra-broadcast-type-add').click(addBroadcastType);
            $('#association-extra-broadcast-type').keypress(function (e) {
                if (e.keyCode === 13) {
                    addBroadcastType();
                }
            });
            $('#association-submit').click(putAssociation);
        });
    }

    function renderAssociationsForm(mode, serviceEmail) {
        currentAssociation = {mode: mode};
        if (mode === 'edit') {
            getAssociation(serviceEmail, renderAssociationsFormInternal);
        } else {
            renderAssociationsFormInternal('new');
        }
    }

    function getAssociationFormValues() {
        var associationModules = [], associationBroadcastTypes = [];
        $('#association-modules-container').find('input[type=checkbox]:checked').each(function () {
            associationModules.push($(this).val());
        });
        $('#association-broadcast-types-container').find('input[type=checkbox]:checked').each(function () {
            associationBroadcastTypes.push($(this).val());
        });
        return {
            customer_id: currentAssociation.customer_id,
            name: $('#association-name').val(),
            address1: $('#association-address1').val(),
            address2: $('#association-address2').val(),
            zip_code: $('#association-zip').val(),
            city: $('#association-city').val(),
            user_email: $('#association-email').val(),
            telephone: $('#association-phone').val(),
            language: $('#association-language').val(),
            modules: associationModules,
            broadcast_types: associationBroadcastTypes
        };
    }

    /*
     Ajax calls
     */

    function getAssociationConfiguration(callback) {
        if (LocalCache.associations.config) {
            callback(LocalCache.associations.config);
        } else {
            sln.call({
                url: '/common/associations/get_defaults',
                success: function (data) {
                    LocalCache.associations.config = data
                    callback(LocalCache.associations.config);
                }
            });
        }
    }

    function getAssociations(callback) {
        if (associations.length) {
            callback(associations);
            return;
        }
        $('#associations-content').html(TMPL_LOADING_SPINNER);
        sln.call({
            url: '/common/associations/get_all',
            success: function (data) {
                associations = data.associations;
                generatedOn = data.generated_on;
                for (var i = 0; i < associations.length; i++) {
                    associations[i].statistics.lastQuestionAnsweredDate = sln.format(new Date(associations[i].statistics.last_unanswered_question_timestamp * 1000));
                    associations[i].hasAgenda = associations[i].modules.indexOf('agenda') !== -1;
                    associations[i].hasQA = associations[i].modules.indexOf('ask_question') !== -1;
                    associations[i].hasBroadcast = associations[i].modules.indexOf('broadcast') !== -1;
                    associations[i].hasStaticContent = associations[i].modules.indexOf('static_content') !== -1;
                }
                callback(associations);
            }
        });
    }

    function getAssociation(serviceEmail, callback) {
        $('#associations-content').html(TMPL_LOADING_SPINNER);
        sln.call({
            url: '/common/associations/get',
            data: {service_email: serviceEmail},
            success: function (data) {
                currentAssociation = data;
                currentAssociation.service_email = serviceEmail;
                callback('edit');
            }
        });
    }


    function putAssociation() {
        var formValues = getAssociationFormValues();
        currentAssociation = formValues;
        if (currentAssociation.mode === 'edit') {
            formValues.service_email = currentAssociation.service_email;
        }
        sln.showProcessing(CommonTranslations.SAVING_DOT_DOT_DOT);
        // Not registered on page load to prevent updates when multiple people are logged in on the same dashboard
        isWaitingForProvisionUpdate = true;
        sln.call({
            url: '/common/associations/put',
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

    function reloadAssociationList() {
        associations = [];
        window.location.hash = '#/associations';
    }

    function associationsChannelUpdates(data) {
        if (!isWaitingForProvisionUpdate && data.type !== 'solutions.common.associations.deleted') {
            return;
        }
        switch (data.type) {
            case 'common.provision.success':
                isWaitingForProvisionUpdate = false;
                sln.hideProcessing();
                var msg = currentAssociation.customer_id ? CommonTranslations.association_updated : CommonTranslations.association_created;
                sln.alert(msg, reloadAssociationList, CommonTranslations.SUCCESS);
                break;
            case 'common.provision.failed':
                isWaitingForProvisionUpdate = false;
                sln.hideProcessing();
                sln.alert(CommonTranslations.ERROR, null, data.errormsg);
                break;
            case 'solutions.common.associations.deleted':
                associationDeleted(data.service_email);
                break;
        }
    }

    $(document).ready(function () {
        sln.registerMsgCallback(associationsChannelUpdates);
    });
})();
