/*
 * Copyright 2017 GIG Technology NV
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

$(function() {
    "use strict";

    var customer = null;
    var lastUsedTester = '';
    var checkboxTmpl = '{{each(i, val) values}}<label class="checkbox"><input type="checkbox" value="${val.value}"> ${val.text}</label>{{/each}}';
    var elemAppsContainer = $('#sb_apps_container'),
        elemInputMessage = $('#sb_text'),
        elemInputCustomer = $('#sb_search_customer_name');
    initUI();

    function createCheckboxes(values) {
        return $.tmpl(checkboxTmpl, {values: values});
    }

    function initUI() {
        customer = null;
        elemAppsContainer.html('Search for a customer first');
        $('#sb_send, #sb_test').prop('disabled', true);
    }


    function loadService() {
        if (customer.service_email) {
            sln.call({
                url : '/internal/shop/rest/customer/service/get',
                data : {
                    customer_id : customer.id
                },
                success : function(service) {
                    console.log('Service retrieved', service);
                    customer.service = service;
                    if (!service.app_infos || !service.app_infos.length) {
                        return sln.alert('This customer has no apps');
                    }

                    // First add the default app
                    var defaultAppName = service.app_infos[0].name + " (" + service.app_infos[0].id + ", default)";
                    elemAppsContainer.html(createCheckboxes([{value: service.app_infos[0].id, text: defaultAppName}]));

                    // Next add the other apps
                    var otherApps = service.app_infos.slice(1).sort(function(x, y) {
                        return x.name > y.name ? 1 : -1;
                    }).map(function (app) {
                        return {
                            value: app.id,
                            text: app.name + ' (' + app.id + ')'
                        };
                    });
                    elemAppsContainer.append(createCheckboxes(otherApps));
                    $('#sb_send, #sb_test').prop('disabled', false);
                }
            });
        } else {
            sln.alert('This customer has no service');
        }
    }

    function reEnableButtons() {
        $('#sb_send, #sb_test').prop('disabled', !elemAppsContainer.find(':checked').val());
    }

    $('#sb_apps').change(reEnableButtons);
    elemInputMessage.keyup(reEnableButtons);

    var options = {
        source : type_ahead_options.source,
        matcher : type_ahead_options.matcher,
        items : type_ahead_options.items,
        updater : function(item) {
            var $this = $(this.$element);
            customer = $this.data('customerMap')[item];
            loadService();
            return customer.name;
        }
    };

    elemInputCustomer.typeahead(options).keyup(function () {
        if (customer && customer.name != $(this).val()) {
            initUI();
        }
    });

    $('#sb_send, #sb_test').click(function() {
        var $this = $(this);
        if ($this.is(':disabled')) {
            return;
        }
        var text = elemInputMessage.val().trim();
        var appIds = [];
        elemAppsContainer.find(':checked').each(function () {
            appIds.push($(this).val());
        });

        if (!text) {
            sln.alert('Please provide the message');
            return;
        }
        if (!appIds.length) {
            sln.alert('Please select one or more apps');
            return;
        }

        function postSystemBroadcast(tester) {
            $this.prop('disabled', true);
            var data = {
                service: customer.service_email,
                app_ids: appIds,
                message: text,
                tester: tester
            };
            sln.call({
                url : $this.data('url'),
                type : 'POST',
                showProcessing : true,
                data: data,
                success : function(data) {
                    if (!tester) {
                        elemAppsContainer.find(':checked').prop('checked', false);
                        elemInputMessage.val('');
                        elemInputCustomer.val('');
                    }
                    if (!data.success) {
                        sln.alert(data.errormsg);
                        $this.prop('disabled', false);
                        return;
                    }
                    // In case of success, disable the send button to prevent accidental double sending
                    sln.alert('Successfully started the app-wide broadcast', function() {
                        $this.prop('disabled', $this.attr('id') == 'sb_send');
                    }, 'Success');
                },
                error : function(XMLHttpRequest, textStatus, errorThrown) {
                    sln.hideProcessing();
                    sln.showAjaxError(XMLHttpRequest, textStatus, errorThrown);
                    $this.prop('disabled', false);
                }
            });
        }

        if ($this.attr('id') == 'sb_test') {
            sln.input(function(tester) {
                lastUsedTester = tester;
                postSystemBroadcast(tester);
            }, 'E-mail address of the test account', null, null, lastUsedTester);
        } else {
            postSystemBroadcast();
        }
    });

});
