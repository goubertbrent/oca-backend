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

var TMPL_ADDRESS = "${customer.address1}{{if customer.address2}}\n${customer.address2}{{/if}}\n${customer.zip_code} ${customer.city}";

var TAB_IDS = $('#create_service_form_tmpl section').map(function() {
    return this.id;
}).get();
var newService, currentTabId;

var showTab = function(tabId) {
    // Hide errors
    showServiceError(null);
    $('#create_service_form .modal-body').scrollTop(0);

    // Hide other tab content and disable next tabs
    var tabIndex = TAB_IDS.indexOf(tabId);
    $('#create_service_form section').each(function(i, element) {
        var section = $('#create_service_form #' + element.id);
        var a = $('#create_service_form li[section="' + TAB_IDS[i] + '"] a');

        if (tabId == element.id) {
            section.show();
            a.parent().addClass('active');
        } else {
            section.hide();
            a.parent().removeClass('active');
        }

        if (i <= tabIndex) {
            a.parent().removeClass('disabled');
        } else {
            a.parent().addClass('disabled');
        }
    });
    currentTabId = tabId;

    var prevBtn = $('#create_service_form #button_create_service_prev');
    if (tabIndex == 0) {
        prevBtn.addClass('disabled');
    } else {
        prevBtn.removeClass('disabled');
    }

    var nextBtn = $('#create_service_form #button_create_service_next');
    if (tabIndex == TAB_IDS.length - 1) {
        nextBtn.text('Save').addClass('btn-primary');
    } else {
        nextBtn.text('Next').removeClass('btn-primary');
    }
};

var showNextTab = function() {
    var currentTabIndex = TAB_IDS.indexOf(currentTabId);
    if (currentTabIndex < TAB_IDS.length - 1)
        showTab(TAB_IDS[currentTabIndex + 1]);
};

var showPrevTab = function() {
    var currentTabIndex = TAB_IDS.indexOf(currentTabId);
    if (currentTabIndex > 0)
        showTab(TAB_IDS[currentTabIndex - 1]);
};

var showServiceError = function(msg) {
    if (msg) {
        $('#create_service_form #create_service_error').show();
        $('#create_service_form #create_service_error span').empty().text(msg);
        $('#create_service_form .modal-body').scrollTop(0);
    } else {
        $('#create_service_form #create_service_error').hide();
        $('#create_service_form #create_service_error span').empty();
        $('#create_service_form .error').removeClass('error');
    }
};

var validateRequiredFieldsInCurrentTab = function() {
    var allOk = true;
    var currentSection = $('#create_service_form #' + currentTabId);

    $('input[required]', currentSection).each(function(i, element) {
        var input = $('#create_service_form #' + element.id);
        if (input.val() == "") {
            allOk = false;
            input.parents('.control-group').addClass('error');
        } else {
            input.parents('.control-group').removeClass('error');
        }
    });

    $('textarea[required]', currentSection).each(function(i, element) {
        var textarea = $('#create_service_form #' + element.id);
        if (textarea.text() == "") {
            allOk = false;
            textarea.parents('.control-group').addClass('error');
        } else {
            textarea.parents('.control-group').removeClass('error');
        }
    });

    return allOk;
};

var submitMetadata = function() {
    newService.name = $("#create_service_form #service_name").val().trim();
    newService.email = $("#create_service_form #service_email").val().trim();
    newService.address = $("#create_service_form #service_address").val().trim();
    newService.phone_number = $("#create_service_form #service_phone_number").val().trim();
    newService.language = $("#create_service_form #service_language").val();
    newService.currency = $("#create_service_form #service_currency").val();
    newService.organization_type = parseInt($('#create_service_form #service_organization_type').val());

    showNextTab();
};

var submitModules = function() {
    newService.modules = $('#create_service_form #form_modules input[type="checkbox"]:checked').map(function () {
        return $(this).val();
    }).get();

    if (newService.modules.indexOf('broadcast') == -1) {
        newService.broadcast_types = [];
    } else {
        newService.broadcast_types = $('#create_service_form #form_broadcast_types input[type="checkbox"]:checked')
                .map(function() {
                    return this.value;
                }).get();

        $.each($('#create_service_form #service_other_broadcast_types').val().split('\n'), function(i,
                broadcastType) {
            broadcastType = broadcastType.trim();
            if (broadcastType) {
                newService.broadcast_types.push(broadcastType);
            }
        });

        if (!newService.broadcast_types.length) {
            showServiceError('Please supply at least 1 broadcast type');
            return;
        }
    }

    if (newService.modules.indexOf('city_app') == -1) {
    	newService.managed_organization_types = [];
    } else {
    	newService.managed_organization_types = $('#create_service_form #form_managed_organization_types input[type="checkbox"]:checked')
        .map(function() {
            return parseInt(this.value);
        }).get();
    }

    showNextTab();
};

var submitApps = function() {
    var oldUnknowApps = newService.apps || [];

    var defaultAppId = $('#create_service_form #form_apps #service_default_app').val();
    newService.apps = [ defaultAppId ];

    $('#create_service_form #form_apps input[type="checkbox"]').map(function() {
        if (this.value != defaultAppId && $(this).is(':checked')) {
            newService.apps.push(this.value);
        }

        var i = oldUnknowApps.indexOf(this.value);
        if (i >= 0) {
            oldUnknowApps.splice(i, 1);
        }
    });

    if (oldUnknowApps.length) {
        // Its possible that the current user does not have any access to some apps.
        // Previously there were non-city-apps supported.
        // Lets add them again
        $.each(oldUnknowApps, function(i, appId) {
            if (newService.apps.indexOf(appId) == -1) {
                newService.apps.push(appId);
            }
        });
    }
    createService();
};

var createService = function() {
    var btnCreateServiceNextElem = $('#button_create_service_next').attr('disabled', true);
    showProcessing((currentCustomer.service_email ? "Updating" : "Creating") + " service...");
    sln.call({
        url : '/internal/shop/rest/service/put',
        type : 'POST',
        data : {
            data : JSON.stringify({
                service : newService,
                customer_id: currentCustomer.id
            })
        },
        success : function(data) {
            btnCreateServiceNextElem.attr('disabled', false);
            if (data.success) {
                currentCustomer.user_email = newService.email;
                currentCustomer.service_email = newService.login; // Causes the service tab content to be reloaded
                currentCustomer.auto_login_url = data.service.auto_login_url;
                showServiceError(null);
            } else {
                hideProcessing();
                showServiceError(data.errormsg);
            }
        },
        error : function() {
            btnCreateServiceNextElem.attr('disabled', false);
            hideProcessing();
            showServiceError('An unknown error occurred!');
        }
    });
};

var showServiceTab = function() {
    newService = {};
    $('#tab-service').find('.loading').html(TMPL_LOADING_SPINNER);
    $('#tab-service').find('.content').addClass('hide');
    // Check default module checkboxes
    $.each($('#tab-service').find('#form_modules').find(':checkbox'), function () {
        var $this = $(this);
        if (currentCustomer.default_modules.indexOf($this.val()) !== -1) {
            $this.prop('checked', true).parent().show();
        } else {
            if (currentCustomer.isStatic) {
                $this.parent().hide();
            } else {
                $this.parent().show();
            }
            $this.prop('checked', false);
        }
    });

    if (currentCustomer.isStatic) {
        $('#form_broadcast_types').hide();
        $('#form_managed_organization_types').hide();
        $('#static_service_info').show();
    }


    // bind elements
    var form = $('#create_service_form');
    form.find('#service_customer_name').typeahead(type_ahead_options);

    customerSelected(currentCustomer);

    form.find('#button_create_service_prev').unbind('click').click(function() {
        showPrevTab();
    });

    form.find('#button_create_service_next').unbind('click').click(function() {
        if($(this).attr('disabled')){
            return;
        }
        // validate form
        var allOk = validateRequiredFieldsInCurrentTab();
        if (!allOk) {
            showServiceError('Please provide all required fields.');
            return;
        }

        // submit form
        var currentTabIndex = TAB_IDS.indexOf(currentTabId);
        switch (currentTabIndex) {
        case 0:
            submitMetadata();
            break;
        case 1:
            submitModules();
            break;
        case 2:
            submitApps();
            break;
        default:
            break;
        }
    });

    form.find('.nav li').click(function() {
        var elem = $(this);
        if (!elem.hasClass('disabled')) {
            showTab(elem.attr('section'));
        }
    });

    form.find('#form_modules input[type="checkbox"][value="broadcast"]').change(function() {
        var broadcastTypes = form.find('#form_broadcast_types');
        if ($(this).is(':checked')) {
            broadcastTypes.slideDown();
        } else {
            broadcastTypes.slideUp();
        }
    }).change();

    form.find('#form_modules input[type="checkbox"][value="city_app"]').change(function() {
        var managedOrganizationTypes = form.find('#form_managed_organization_types');
        if ($(this).is(':checked')) {
        	managedOrganizationTypes.slideDown();
        } else {
        	managedOrganizationTypes.slideUp();
        }
    }).change();

    form.find('#form_apps #service_default_app').change(function() {
        var appId = $(this).val();
        form.find('#form_apps input[type="checkbox"]').each(function() {
            var checkbox = $(this);
            var isDefault = checkbox.val() === appId;
            checkbox.prop('checked', isDefault || checkbox.is(':checked')).attr('disabled', isDefault)
                .parents('label').toggleClass('default-app', isDefault);
        });
    }).change();

    if (currentCustomer.app_ids.length) {
        // customer already has a service, preselect the current active apps
        form.find('#other-apps').find('[type=checkbox]').each(function () {
            // Preselect the currently enabled apps.
            var $this = $(this);
            $this.prop('checked', currentCustomer.app_ids.indexOf($this.val()) !== -1);
        });
    }
    var customerForm = $('#customer_form');
    customerForm.find("#button_change_service_email").unbind('click').click(function () {
        if (!$(this).attr('disabled'))
            showChangeServiceEmail(currentCustomer);
    });

    customerForm.find("#button_add_location").toggle(!!(currentCustomer.is_admin && currentCustomer.service_email)).unbind('click').click(function () {
        if (!$(this).attr('disabled'))
            showAddLocation(currentCustomer);
    });

    currentTabId = 0;
    showTab(TAB_IDS[0]);
};
var showCreateService = function() {
    $('#tab-service').find('.loading').html(TMPL_LOADING_SPINNER);
    $('#tab-service').find('.content').addClass('hide');
    $('#customer_form').find('[data-target=#tab-service]').tab('show');
    if (currentCustomer.migration_job) {
        $('.service-only').hide();
    }else {
        showRelevantButtons(TABTYPES.SERVICE);
        if (!currentCustomer.service_email) {
            // No service exists yet for this customer. Show a button to create one.
            $('.existing-service-only').hide();
        }
    }
    if(! TEMPLATES['service_tab']) {
        TEMPLATES['service_tab'] = $('#create_service_form_tmpl').html();
    }

    // if the customer his subscription is static, do not make the second tab editable and prefill the appropriate values.
    if(!currentCustomer.default_modules){
        sln.call({
            url: '/internal/shop/rest/customer/get_default_modules',
            data: {
                'customer_id': currentCustomer.id
            },
            success: function (response) {
                $('#create_service_form_tmpl').empty();
                if (response.errormsg) {
                    $('#create_service_form_tmpl').html('<h4>Customer service</h4><p>' + response.errormsg + '</p>');
                    $('#tab-service').find('.loading').html('');
                    $('#tab-service').find('.content').removeClass('hide');
                } else {
                    currentCustomer.default_modules = response.modules;
                    currentCustomer.isStatic = response.success; // if success == true, customer is static.
                    $('#create_service_form_tmpl').html(TEMPLATES['service_tab']);
                    showServiceTab();
                }
            }
        });
    }else{
        showServiceTab();
    }

};

$('button.create-service, a.create-service').click(function() {
    var customerId = parseInt($(this).attr('customer_id'));
    // Open customer form, and immediately go to the services tab.
    showCustomerForm(CustomerFormType.OPEN_TAB, showCreateService, customerId);
});

var resetCustomerServiceApps = function(current_apps, service_apps, current_user_apps) {
    var otherApps = $("#other-apps").empty();
    var defaultAppFound = false;
    $.each(current_user_apps, function(i , user_app) {
        var _label = $('<label class="checkbox"></label>');
        var _input = $('<input type="checkbox">').val(user_app.id);

        _label.append(_input);
        _label.append(" " + user_app.name + " (" + user_app.id + ")");

        otherApps.append(_label);

        if (current_apps[0] == user_app.id) {
            defaultAppFound = true;
        }
    });

    var defaultApps = $("#service_default_app").empty();
    if (!defaultAppFound) {
        $.each(service_apps, function(i , service_app) {
            if (current_apps[0] == service_app.id) {
                var _option = $('<option></option>').val(service_app.id).text(service_app.name + " (" + service_app.id + ")");
                defaultApps.append(_option);
                return false;
            }
        });
    }

    $.each(current_user_apps, function(i , user_app) {
        var _option = $('<option></option>').val(user_app.id).text(user_app.name + " (" + user_app.id + ")");
        defaultApps.append(_option);
    });
};

var customerSelected = function(customer) {
    newService.app_infos = [];
    newService.current_user_app_infos = [];

    if (customer.service_email) {
        sln.call({
            url : '/internal/shop/rest/customer/service/get',
            data : {
                customer_id : customer.id
            },
            success : function(service) {
                showServiceError(null);

                resetCustomerServiceApps(service.apps, service.app_infos, service.current_user_app_infos);

                var createServiceForm = $('#create_service_form');
                // set values
                $.each([ 'name', 'email', 'address', 'phone_number', 'language', 'currency', 'organization_type' ],
                        function(i, attr) {
                            $('#service_' + attr, createServiceForm).val(service[attr]);
                        });
                // set checkBoxes
                $.each([ 'modules', 'broadcast_types', 'apps', 'managed_organization_types'], function(i, attr) {
                    $('#form_' + attr + ' input[type="checkbox"]', createServiceForm).each(function() {
                    	var v = this.value;
                    	if (attr === 'managed_organization_types') {
                    		v = parseInt(v);
                    	}
                        $(this).prop('checked', service[attr].indexOf(v) != -1).change();
                    });
                });
                newService.apps = service.apps;
                currentCustomer.service = service;

                if (service.modules.indexOf('broadcast') == -1) {
                    $('#form_broadcast_types', createServiceForm).hide();
                } else {
                    var otherBroadcastTypes = "";
                    $.each(service.broadcast_types, function(i, broadcastType) {
                        // if there is no checkbox with <broadcastType> as
                        // value, then add it to the 'Other' textarea.
                        if (!$('#form_broadcast_types input[type="checkbox"][value="' + broadcastType + '"]',
                                createServiceForm).val()) {
                            if (otherBroadcastTypes != "") {
                                otherBroadcastTypes += "\n";
                            }
                            otherBroadcastTypes += broadcastType;
                        }
                    });
                    $('#service_other_broadcast_types', createServiceForm).val(otherBroadcastTypes);
                }

                if (service.modules.indexOf('city_app') == -1) {
                    $('#form_managed_organization_types', createServiceForm).hide();
                }
                selectDefaultApps();
                $('#tab-service').find('.loading').html('');
                $('#tab-service').find('.content').removeClass('hide');
            },
            error : function() {
                $('#customer_form').modal('hide');
                showAlert("An unexpected error occurred while getting the service details. Please try again.");
            }
        });
    } else {
        if (currentCustomer.contacts) {
            prefillServiceData(customer, currentCustomer.contacts[0]);
        } else {

            sln.call({
                url: '/internal/shop/rest/contact/find',
                data: {
                    customer_id: customer.id
                },
                success: function (contacts) {
                    prefillServiceData(customer, contacts[0])
                }
            });
        }

        sln.call({
            url : '/internal/shop/rest/regio_manager/apps',
            success : function(data) {
                resetCustomerServiceApps([], [], data);
                selectDefaultApps();
            }
        });

        //set default apps
        if(currentCustomer.prospect_id){
            // get prospect
            if(!currentCustomer.prospect){
                sln.call({
                    url: '/internal/shop/rest/prospect/findbycustomer',
                    type: 'GET',
                    data: {
                        customer_id: currentCustomer.id
                    },
                    success: function (data) {
                        if (data) {
                            currentCustomer.prospect = data.prospect;
                            selectDefaultApps();
                        }
                    }
                });
            }else{
                selectDefaultApps();
            }
        }else{
            selectDefaultApps();
        }
    }
};

function prefillServiceData(customer, contact) {
    showServiceError(null);
    if (customer) {
        $('#service_organization_type').val(customer.organization_type);
        $('#service_name').val(customer.name);
        $('#service_address').val($.tmpl(TMPL_ADDRESS, {
            customer: customer
        }).text());
        $('#service_language').val(customer.language);
    }

    if (contact) {
        $('#create_service_form #service_email').val(contact.email);
        $('#create_service_form #service_phone_number').val(contact.phone_number);
    }
    $('#tab-service').find('.loading').html('');
    $('#tab-service').find('.content').removeClass('hide');

}


function selectDefaultApps(){
    var elemServiceDefaultApp = $('#service_default_app');
    if(currentCustomer.service){
        $.each(currentCustomer.service.apps, function(i, app){
            var elem = $('#other-apps').find('[value=' + app + ']').prop('checked', true);
            if(i === 0){
                $('#service_default_app').val(currentCustomer.service.apps[0]).change();
            }
        });
    } else if (currentCustomer.prospect) {
        var exists = false;
        var default_app = currentCustomer.prospect.app_id;
        elemServiceDefaultApp.find('option').each(function () {
            if (this.value === default_app) {
                exists = true;
            }
            if (this.value === 'rogerthat') {
                $(this).prop('checked', true);
            }
        });
        if (!exists) {
            default_app = "rogerthat";
        }
        elemServiceDefaultApp.val(default_app).change();
    } else{
    	var defaultAppId = "rogerthat";

    	var form = $('#create_service_form');
    	form.find('#form_apps input[type="checkbox"]').each(function() {
            var checkbox = $(this);
            var value = checkbox.val();
            var text = checkbox.parents("label").text();
        	if (text.indexOf(currentCustomer.city) >= 0) {
        		defaultAppId = value;
        	}
        });
        elemServiceDefaultApp.val(defaultAppId).change();
    }
}


$(document).ready(function () {
    customer_selected.push(function (sender, customer) {
        if (sender.attr('id') == 'service_customer_name') {
            customerSelected(customer);
        }
    });

    sln.registerMsgCallback(function (data) {
        switch (data.type) {
            case 'shop.provision.success':
                if(!currentCustomer || currentCustomer.id != data.customer_id) {
                    return;
                }
                loadCustomer(currentCustomer.id, function (updatedCustomer) {
                    for (var prop in updatedCustomer) {
                        if (updatedCustomer.hasOwnProperty(prop)) {
                            currentCustomer[prop] = updatedCustomer[prop];
                        }
                    }
                    hideProcessing();
                    var s = '';
                    if (currentCustomer.creating) {
                        s = 'An e-mail with the account details has been sent to ' + currentCustomer.user_email + '.<br><br>';
                    }
                    showAlert(s + '<a href="' + currentCustomer.auto_login_url + '" target="_blank">LOG IN</a>', function () {
                        // Always redirect to 'orders' tab. Also force that tab to refresh.
                        showOrders(true);
                        currentCustomer.creating = false;
                    }, "Customer service saved");
                });
                break;
            case 'shop.provision.failed':
                hideProcessing();
                showAlert('Failed to save customer service. Please contact mobicage.', null, "Could not save service");
                break;
        }
    });

});
