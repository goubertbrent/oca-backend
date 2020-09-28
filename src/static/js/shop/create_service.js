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

var TMPL_ADDRESS = "${customer.address1}{{if customer.address2}}\n${customer.address2}{{/if}}\n${customer.zip_code} ${customer.city}";

var TAB_IDS = $('#create_service_form_tmpl section').map(function() {
    return this.id;
}).get();
var newService, currentTabId;
var CREATE_SERVICE_TEMPLATE = $('#create_service_form_tmpl').html();

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
    newService.email = $("#create_service_form #service_email").val().trim();
    newService.language = $("#create_service_form #service_language").val();
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

var submitCommunity = function() {
    const communityId = $('#service_community').val();
    if (communityId) {
        newService.community_id = parseInt(communityId);
    } else {
        showAlert('Please select a community');
        return;
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
            submitCommunity();
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

async function getServiceCommunities(country, communityId){
    const communities = await (await fetch('/console-api/communities?country=' + country)).json();
    const communitySelect = $('#service_community');
    communitySelect.empty();
    communitySelect.append('<option></option>');
    for (const community of communities){
        communitySelect.append(`<option value="${community.id}">${community.name}</option>`);
    }
    if (communityId) {
        communitySelect.val(communityId);
    }
}

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
                    $('#create_service_form_tmpl').html(CREATE_SERVICE_TEMPLATE);
                    showServiceTab();
                }
            }
        });
    } else{
        showServiceTab();
    }

};

$('button.create-service, a.create-service').click(function() {
    var customerId = parseInt($(this).attr('customer_id'));
    // Open customer form, and immediately go to the services tab.
    showCustomerForm(CustomerFormType.OPEN_TAB, showCreateService, customerId);
});

var customerSelected = function(customer) {

    if (customer.service_email) {
        sln.call({
            url : '/internal/shop/rest/customer/service/get',
            data : {
                customer_id : customer.id
            },
            success : function(service) {
                showServiceError(null);

                var createServiceForm = $('#create_service_form');
                // set values
                $.each(['email', 'language', 'organization_type'],
                    function (i, attr) {
                        $('#service_' + attr, createServiceForm).val(service[attr]);
                    });
                // set checkBoxes
                $.each([ 'modules', 'broadcast_types', 'managed_organization_types'], function(i, attr) {
                    $('#form_' + attr + ' input[type="checkbox"]', createServiceForm).each(function() {
                    	var v = this.value;
                    	if (attr === 'managed_organization_types') {
                    		v = parseInt(v);
                    	}
                        $(this).prop('checked', service[attr].indexOf(v) != -1).change();
                    });
                });
                currentCustomer.service = service;
                getServiceCommunities(currentCustomer.country, service.community_id);

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
                $('#tab-service').find('.loading').html('');
                $('#tab-service').find('.content').removeClass('hide');
            },
            error : function() {
                $('#customer_form').modal('hide');
                showAlert("An unexpected error occurred while getting the service details. Please try again.");
            }
        });
    } else {
        ShopRequests.getContacts(customer.id).then(contacts => prefillServiceData(customer, contacts[0]));

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
                        }
                    }
                });
            }
        }
    }
};

function prefillServiceData(customer, contact) {
    showServiceError(null);
    if (customer) {
        $('#service_organization_type').val(customer.organization_type);
        $('#service_language').val(customer.language);
    }

    if (contact) {
        $('#create_service_form #service_email').val(contact.email);
        $('#create_service_form #service_phone_number').val(contact.phone_number);
    }
    $('#tab-service').find('.loading').html('');
    $('#tab-service').find('.content').removeClass('hide');

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
