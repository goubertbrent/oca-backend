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
'use strict';
var TMPL_PROCESSING = '<div class="modal hide fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
    + '    <div class="modal-header">'
    + '        <h3 id="myModalLabel">${header}</h3>'
    + '    </div>'
    + '    <div class="modal-body">'
    + '        <div class="progress progress-striped active"><div class="bar" style="width: 100%;"></div></div>'
    + '    </div>' + '</div>';

var TMPL_ALERT = '<div class="modal hide fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
    + '    <div class="modal-header">'
    + '        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'
    + '        <h3 id="myModalLabel">${header}</h3>'
    + '    </div>'
    + '    <div class="modal-body">'
    + '        <p>{{html body}}</p>'
    + '    </div>'
    + '    <div class="modal-footer">'
    + '        <button class="btn" data-dismiss="modal" aria-hidden="true">${closeBtn}</button>' //
    + '    </div>' //
    + '</div>';

var TMPL_INPUT = '<div class="modal hide fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
    + '    <div class="modal-header">'
    + '        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'
    + '        <h3 id="myModalLabel">${header}</h3>'
    + '    </div>'
    + '    <div class="modal-body">'
    + '        <input id="categoryname" type="text" style="width: 514px" placeholder="${placeholder}" value="${value}" />'
    + '    </div>'
    + '    <div class="modal-footer">'
    + '        <button action="cancel" class="btn" data-dismiss="modal" aria-hidden="true">${cancelBtn}</button>'
    + '        <button action="submit" class="btn btn-primary">${submitBtn}</button>' //
    + '    </div>' //
    + '</div>';

var TMPL_CONFIRM = '<div class="modal hide fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
    + '    <div class="modal-header">'
    + '        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'
    + '        <h3 id="myModalLabel">${header}</h3>'
    + '    </div>'
    + '    <div class="modal-body">'
    + '        <p>{{html body}}</p>'
    + '    </div>'
    + '    <div class="modal-footer">'
    + '        <button action="cancel" class="btn" data-dismiss="modal" aria-hidden="true">${cancelBtn}</button>'
    + '        <button action="submit" class="btn btn-primary">${submitBtn}</button>' //
    + '    </div>' //
    + '</div>';

var TMPL_LOADING_SPINNER = '<svg class="circular" style="margin:0 auto; left: 0;right: 0;">'
    + '<circle class="path" cx="50" cy="50" r="20" fill="none" stroke-width="3" stroke-miterlimit="10" />'
    + '</svg>';

var OrganizationType = {
    ASSOCIATION: 1,
    MERCHANT: 2,
    COMMUNITY_SERVICE: 3,
    CARE: 4
};

var _processingModal = null;
var currentCustomer = {};
var type_ahead_timeout = null;
var customer_selected = [];
var CustomerFormType = {
    NEW: 'new',
    SEARCH: 'search',
    LINK_PROSPECT: 'link-prospect',
    OPEN_TAB: 'open-tab'
};
var TABTYPES = {
    DETAILS: 'details',
    CONTACTS: 'contacts',
    PROSPECT: 'prospect',
    NEW_ORDER: 'new-order',
    ORDERS: 'orders',
    QUOTATIONS: 'quotations',
    SERVICE: 'service',
    HISTORY: 'history'
};

var SUBSCRIPTION_MODULES = {
    city: ['OCAM', 'APLS', 'APPL'],
    gold: ['NWSG'],
    platinum: ['NWSP']
};

var currentMode;

var regioManagerTeams = [];
var logoUrl = '/static/images/shop/osa_white_en_64.jpg';
var regioManagersPerApp = {};
var _processingTimeout,
    LEGAL_ENTITY,
    _legalEntityCallbacks = [],
    currentSubscription;

var EMAIL_REGEX = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;


var openCustomerModalFromUrl = function() {
    function getParameterByName(name) {
        var url = window.top.location.href;
        name = name.replace(/[\[\]]/g, "\\$&");
        var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)", "i"),
            results = regex.exec(url);
        if (!results) return null;
        if (!results[2]) return '';
        return decodeURIComponent(results[2].replace(/\+/g, " "));
    }

    if (window.top == window.self)
        return;

    var customerId = getParameterByName("customer_id");
    if (customerId) {
        customerId = parseInt(customerId);
        if (!customerId || isNaN(customerId)) {
            console.warning('Invalid customer id for node', customerId, $this);
        } else {
            loadCustomer(customerId, function (customer) {
                initCustomerForm(customer);
                showCustomerForm(CustomerFormType.OPEN_TAB, showDetails, customer.id);
            });
        }
    }
};

var loadRegioManagerTeams = function () {
    sln.call({
        url: '/internal/shop/rest/regio_manager_team/list',
        success: function (data) {
            if (data) {
                regioManagerTeams = data;
                openCustomerModalFromUrl();
            }
        }
    });
};

function getRegioManagerTeam (teamId) {
    return regioManagerTeams.filter(function (team) {
        return team.id === teamId;
    })[0];
}

var customerMap = {};
var type_ahead_options = {
    source: function (query, resultHandler) {
        // Only send the ajax request after the user stopped typing
        if (type_ahead_timeout) {
            clearTimeout(type_ahead_timeout);
        }
        type_ahead_timeout = setTimeout(function () {
            var findAll = $("#show_all_customers").is(":visible");
            if (findAll) {
                findAll = $("#show_all_customers").is(':checked');
            }
            sln.call({
                url: '/internal/shop/rest/customer/find',
                data: {
                    search_string: query,
                    find_all: findAll
                },
                success: function (data) {
                    customerMap = {};
                    var customers = [];
                    $.each(data, function (i, o) {
                        customerMap[o.id] =  o
                        // sorting is done by typeahead
                        // keys of customerMap are strings
                        customers.push('' + o.id);
                    });
                    resultHandler(customers);
                }
            });
        }, 333);
    },
    matcher: function (key) {
        return true; // accept everything returned by the source function
    },
    items: 20,
    highlighter: function(key) {
        var customer = customerMap[key];

        var typeahead_wrapper = $('<div class="typeahead_wrapper"></div>');
        var typeahead_labels = $('<div class="typeahead_labels"></div>');

        var nameContainer = customer.service_disabled_at ? $('<b style="color: red;"></b>') : $('<b></b>');
        var typeahead_primary = $('<div class="typeahead_primary"></div>').append(nameContainer.text(customer.name));
        typeahead_labels.append(typeahead_primary);

        var subtitle = [customer.address1, customer.address2, customer.zip_code, customer.city].filter(function(text) {
            return typeof text === 'string' ? text.trim() : text;
        }).join(', ');
        var typeahead_secondary = $('<div class="typeahead_secondary"></div>').text(subtitle);
        typeahead_labels.append(typeahead_secondary);

        typeahead_wrapper.append(typeahead_labels);

        return typeahead_wrapper;
    },
    updater: function (key) {
        var thizz = $(this.$element);
        var customer = customerMap[key];
        thizz.data('customer', customer).addClass('success');
        $.each(customer_selected, function (i, f) {
            f(thizz, customer);
        });
        return customer.name;
    }
};
var createModal = function (html, onShown) {
    var modal = $(html).modal({
        backdrop: true,
        keyboard: true,
        show: false
    }).on('hidden', function () {
        modal.remove(); // remove from DOM
    });

    if (onShown) {
        modal.on('shown', function () {
            onShown(modal);
        });
    }
    modal.modal('show');
    return modal;
};
var showProcessing = function (title) {
    // Only show processing when the it took more than 400 ms between calling this method and the hideProcessing method.
    _processingTimeout = setTimeout(function () {
        if (_processingModal)
            return;
        var html = $.tmpl(TMPL_PROCESSING, {
            header: title
        });
        _processingModal = createModal(html);
    }, 400);
};
var hideProcessing = function () {
    clearTimeout(_processingTimeout);
    if (!_processingModal)
        return;
    _processingModal.modal('hide');
    _processingModal = null;
};
var showAlert = function (message, onClose, title, timeout) {
    var html = $.tmpl(TMPL_ALERT, {
        header: title || "Alert",
        body: message,
        closeBtn: "Close"
    });
    var modal = createModal(html);
    var closed = false;
    var close = function () {
        if (!closed) {
            closed = true;
            onClose();
        }
    };
    if (onClose) {
        modal.on('hidden', close);
    }
    if (timeout) {
        window.setTimeout(function () {
            if (!closed)
                modal.modal('hide');
        }, timeout);
    }
};
var showError = function (errorMessage) {
    return showAlert(errorMessage, null, "Error");
};
var askInput = function (onSubmit, title, submitBtnCaption, placeholder, initialValue) {
    var html = $.tmpl(TMPL_INPUT, {
        header: title || "Input",
        cancelBtn: "Cancel",
        submitBtn: submitBtnCaption || "Submit",
        placeholder: placeholder,
        value: initialValue
    });
    var modal = createModal(html, function (modal) {
        $('input', modal).focus();
    });
    $('button[action="submit"]', modal).unbind('click').click(function () {
        var close = onSubmit($("input", modal).val()) !== false;
        if (close)
            modal.modal('hide');
    });
};
var showConfirmation = function (message, onConfirm, onCancel, positiveCaption, negativeCaption, title) {
    var html = $.tmpl(TMPL_CONFIRM, {
        body: message,
        header: title || "Confirm",
        cancelBtn: negativeCaption || "No",
        submitBtn: positiveCaption || "Yes"
    });
    var modal = createModal(html);
    $('button[action="submit"]', modal).unbind('click').click(function () {
        if (onConfirm)
            onConfirm();
        modal.modal('hide');
    });
    $('button[action="cancel"]', modal).unbind('click').click(function () {
        if (onCancel)
            onCancel();
        modal.modal('hide');
    });
};

var htmlize = function (value) {
    return $("<div></div>").text(value).html().replace(/\n/g, "<br>");
};

var getDateString = function (date) {
    return date.toLocaleTimeString(window.navigator.userLanguage || window.navigator.language, {
        weekday: "long",
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
};

var getLocalDateFormat = function () {
    var date = new Date(2013, 10, 18);
    var format = date.toLocaleDateString();
    return format.replace('2013', 'yyyy').replace('11', 'MM').replace('18', 'dd');
};

var mergeObject = function (object, data) {
    $.each(data, function (k, v) {
        object[k] = v;
    });
};

var startOnSitePayment = function (customerId, customerName, customerUserEmail, orderNumber, chargeId, chargeAmount,
                                   chargeReference, cancelable) {
    var paymentOptionsModal = $('#payment_options_modal').modal('show');
    $('.modal-header .close').toggle(cancelable);

    $(".pay-on-site", paymentOptionsModal).unbind('click').click(function () {
        paymentOptionsModal.modal('hide');
        getLegalEntity(function (legalEntity) {
            var modal = $("#payment_info_modal").modal('show').data('customerId', customerId).data('customerUserEmail',
                customerUserEmail).data('chargeReference', chargeReference);
            $('#charge-customer', modal).text(customerName);
            $('#charge-amount', modal).text(legalEntity.currency + ' ' + Number(chargeAmount / 100).toFixed(2));
            $('#charge-reference', modal).text(chargeReference);
        });
    });
};

var prepareNewCustomer = function () {
    currentCustomer = {
        creating : true,
        country : 'BE'
    };
    $('#customer_number-parent').hide();
    // Show all forms without .search-customer-only which were possibly hidden by 'Search customer' step 1
    $('#customer_form form').each(function () {
        var form = $(this);
        if (!form.hasClass('search-customer-only')) {
            form.show();
        }
    });
    // Show the buttons (they are hidden after searching for a customer)
    $('#customer_form .modal-footer').show();
};

var prepareSearchCustomer = function () {
    currentCustomer = {};
    // Hide other forms until search completed
    $('#customer_number-parent').show();
    $('#customer_form form').each(function () {
        var form = $(this);
        if (!form.hasClass('search-customer-only')) {
            form.hide();
        }
    });
    // Hide save button until search completed
    $('#customer_form .modal-footer').hide();
    setTimeout(function () {
        $('#customer_form #search_customer_name').focus();
    }, 500);
    $('#tab-nav-container').find('a').parent().hide();
    // hide 'save' button
    $('#button_save_customer').hide();
};

var prepareShowTab = function (tabFunction, customerId) {
    // Get the user, show the desired tab
    if (!currentCustomer.id) {
        loadCustomer(customerId, function (customer) {
            currentCustomer = customer;
            tabFunction();
        });
    } else {
        tabFunction();
    }
};

var loadCustomer = function (customerId, callback) {
    sln.call({
        url: '/internal/shop/rest/customer',
        data: {
            customer_id: customerId
        },
        success: function (data) {
            if (data.errormsg) {
                showAlert(data.errormsg, null, 'Error');
            } else {
                callback(data.customer);
            }
        },
        error: function () {
            showAlert("An unknown error occurred, please report this to the administrators.");
        }
    });
};

var setCountryByVat = function(vat) {
    // Auto-select country and language based on the entered VAT #278
    vat = vat.toUpperCase();
    var detailsTab = $('#tab-details');
    if (vat.indexOf('BE') == 0) {
        detailsTab.find('#country').val('BE');
        detailsTab.find('#language').val('nl');
    } else if (vat.indexOf('ES') == 0) {
        detailsTab.find('#country').val('ES');
        detailsTab.find('#language').val('es');
    }
};

var showCustomerForm = function (mode, tabFunction, customerId) {
    currentMode = mode;
    currentCustomer = {};
    var found = [false];
    $.each(CustomerFormType, function (k, v) {
        if (v == mode) {
            found[0] = true;
            $('#customer_form .' + v + '-customer-only').show();
        } else {
            $('#customer_form .' + v + '-customer-only').not('.' + mode + '-customer-only').hide();
        }
    });

    if (!found[0]) {
        alert('Developer, you forgot to add ' + mode + ' to CustomerFormType');
        return;
    }

    var readonly = false;
    if (mode == CustomerFormType.NEW) {
        prepareNewCustomer();
    } else if (mode == CustomerFormType.SEARCH) {
        prepareSearchCustomer();
    } else if (mode == CustomerFormType.LINK_PROSPECT) {
        prepareSearchCustomer();
        $('#tab-nav-container').find('a').each(function () {
            var $this = $(this);
            var tab = $this.attr('data-target');
            if (tab == '#tab-prospect' || tab == '#tab-orders') {
                $this.hide();
            } else {
                $this.show();
            }
        });
        readonly = true;
    } else if (mode == CustomerFormType.OPEN_TAB) {
        prepareShowTab(tabFunction, customerId);
    }

    var detailsTab = $('#tab-details');
    detailsTab.find('#vat').unbind('keyup').bind('keyup', function() {
        setCountryByVat($(this).val().toUpperCase());
    });

    detailsTab.find('input, textarea, select').not('.customer_select').prop('disabled', readonly);

    detailsTab.find('input').val('');
    var modal = $('#customer_form').data('mode', mode).modal('show');

    // Show the tabs when clicking on them
    $('#tab-nav-container').find('a').unbind('click').click(function (e) {
        e.preventDefault();
        var tab = $(this);
        tab.tab('show');
        switch (tab.attr('data-target')) {
            case '#tab-details':
                // the rest of the logic is done when picking a result from the autocomplete box
                showDetails();
                break;
            case '#tab-contacts':
                showContacts(currentCustomer.id);
                break;
            case '#tab-prospect':
                showProspect();
                break;
            case '#tab-new-order':
                showNewOrder();
                break;
            case '#tab-orders':
                showOrders();
                break;
            case '#tab-quotations':
                showQuotations();
                break;
            case '#tab-service':
                showCreateService();
                break;
            case '#tab-history':
                showHistory();
                break;
        }
    });
    showDetails();
    return modal;
};

var showDetails = function () {
    // hide non-relevant buttons

    $('#tab-nav-container').find('a').show().first().tab('show');
    showRelevantButtons(TABTYPES.DETAILS);
    if (currentCustomer.id) {
        var teamNameElem = $('#team-name');
        teamNameElem.text(currentCustomer.team_id ? getRegioManagerTeam(currentCustomer.team_id).name : '')
            .attr("team-id", currentCustomer.team_id || '')
            .toggle(!currentCustomer.is_admin);
        var select = $("#team-select").toggle(currentCustomer.is_admin);
        if (currentCustomer.is_admin) {
            select.html($('<option></option>').attr('value', "").text("Select team"));
            $.each(regioManagerTeams, function (i, team) {
                select.append($('<option></option>').attr('value', team.id).text(team.name));
            });
            if (currentCustomer.team_id) {
                select.val(currentCustomer.team_id);
            }
            $('#show_all_customers').parent().hide();
        }
        $('#managed-by').text(currentCustomer.manager ? currentCustomer.manager : '');
        $('#user-email').text(currentCustomer.user_email ? currentCustomer.user_email : 'none');
        $('#service-email').text(currentCustomer.service_email)
            .parent().toggle(!!currentCustomer.service_email);
        $('#customer-website').text(currentCustomer.website || '-');
        $('#customer-facebook').text(currentCustomer.facebook_page || '-');
        $('#subscription-type').text(currentCustomer.subscription_str);
        $('#customer-creation-time').text(sln.format(new Date(currentCustomer.creation_time * 1000)));
        $('#has-loyalty-status').find('i').css('color', currentCustomer.has_loyalty ? '#51a351' : '#ff0000');
        $('#loyalty-status').text(currentCustomer.has_loyalty ? 'Yes' : 'No');
        $('#service-status').toggle(currentCustomer.service_disabled_at !== 0);
        $('#service-disabled-at').text(sln.format(new Date(currentCustomer.service_disabled_at * 1000)));
        $('#service-disabled-reason').text(currentCustomer.service_disabled_reason);
        $('#service-disable-pending').toggle(currentCustomer.subscription_cancel_pending_date !== 0);
        $('#service-disable-pending-time').text(sln.format(new Date(currentCustomer.subscription_cancel_pending_date * 1000)));
        $('#service-disable-pending-reason').text(currentCustomer.service_disabled_reason);
        $('#service-cancelling-on-date').text(sln.format(new Date(currentCustomer.cancelling_on_date * 1000)));

        $('#other-customer-info').removeClass('hide');
    } else {
        $('#other-customer-info').addClass('hide');
    }
    if (currentMode == CustomerFormType.LINK_PROSPECT) {
        $('#button_save_customer').hide();
    } else if (currentMode == CustomerFormType.NEW) {
        $('#tab-nav-container').find('a').parent().hide();
        currentCustomer.creating = true;
    } else if (currentMode == CustomerFormType.SEARCH || currentMode == CustomerFormType.OPEN_TAB) {
        $('#button_save_customer').show();
    }
    if (currentCustomer.id) {
        $(".can_edit_only").each(function (i, elem) {
            if (!currentCustomer.can_edit) {
                $(elem).hide();
            }
        });
    }
    setCustomerDetails();
};

var showContacts = function (customerId, reload) {
    //show all the buttons in the footer of the popup that are relevant for contacts
    $('#tab-nav-container').find('a').show();
    $('#tab-nav-container').find('a[data-target="#tab-contacts"]').tab('show');
    showRelevantButtons(TABTYPES.CONTACTS);
    if (!customerId) {
        renderContacts();
        return;
    }
    ShopRequests.getContacts(customerId, {cached: !reload}).then(contacts => renderContacts(contacts));
};

var showProspect = function (reload) {
    $('a[data-target="#tab-prospect"]').tab('show');
    var customerId = currentCustomer.id;
    showRelevantButtons(TABTYPES.PROSPECT);
    // Load the prospect from remote, if necessary.
    if (currentCustomer.prospect && !reload) {
        renderProspect(currentCustomer.prospect);
    } else {
        sln.call({
            url: '/internal/shop/rest/prospect/findbycustomer',
            type: 'GET',
            data: {
                customer_id: customerId
            },
            success: function (data) {
                if (data) {
                    currentCustomer.prospect = data.prospect;
                    $('#button_link_prospect').hide();
                }
                renderProspect(currentCustomer.prospect);
            },
            error: sln.showAjaxError
        });
    }
};

var showNewOrder = function () {
    showRelevantButtons(TABTYPES.NEW_ORDER);
    var form = $('#customer_form');
    form.find('#tab-nav-container').find('a').parent().show();
    // TODO chain requests getLegalEntity
    ShopRequests.getContacts(currentCustomer.id).then(contacts => {
        var html = $.tmpl(JS_TEMPLATES['customer_popup/new_order'], {
            contacts: contacts
        });
        form.find('#tab-new-order').html(html);
        ShopRequests.getProducts(currentCustomer.language).then(products => {
            var productsMapping = products.reduce((acc, product) => {
                acc[product.code] = product;
                return acc;
            }, {});
            getLegalEntity(legalEntity => {
                var orderList = new OrderItemList(form.find('#order-item-list'), legalEntity, products, currentCustomer.organization_type);
                // Show product combination buttons for mobicage entity
                $('#subscription-buttons').toggle(legalEntity.is_mobicage);
                orderList.render();
                if (!legalEntity.is_mobicage) {
                    return;
                }
                $('button[data-sub]').unbind('click').click(function () {
                    orderList.selectedItems = [];
                    var $this = $(this);
                    var sub = $this.attr('data-sub');
                    currentSubscription = sub;
                    for (const productKey of SUBSCRIPTION_MODULES[sub]) {
                        const product = productsMapping[productKey];
                        orderList.addOrderItem(product.code, product.default_count, product.default_comment, product.price, 'new');
                    }
                    orderList.render();
                    $this.parent().find('button').css('opacity', 0.5);
                    $this.css('opacity', 1);
                });
                form.find("#button_create_new_order").unbind('click').click(function () {
                    if ($(this).attr('disabled')) {
                        return;
                    }
                    var customer = currentCustomer;
                    var contact = parseInt(form.find('#new_order_contact').val());
                    if (!orderList.selectedItems.length) {
                        $('#new_order_error').show().find('span').text('You need to select at least 1 product');
                        return;
                    }
                    if (!(customer && contact)) {
                        $('#new_order_error').show().find('span').text('Not all required fields are filled!');
                        return;
                    }

                    $("#button_create_new_order").attr('disabled', true);
                    var chargeInterval = parseInt($('#new_order_charge_interval').val());
                    sln.call({
                        url: '/internal/shop/rest/order/new',
                        type: 'POST',
                        data: {
                            data: JSON.stringify({
                                customer_id: customer.id,
                                contact_id: contact,
                                items: orderList.selectedItems,
                                replace: false,
                                charge_interval: chargeInterval,
                            })
                        },
                        success: function (data) {
                            if (data.success) {
                                orderList.selectedItems = [];
                                orderList.render();
                                $('#new_order_error').hide();
                                showCreateService();
                            } else {
                                if (data.can_replace) {
                                    showConfirmation(data.errormsg, function () {
                                        $("#button_create_new_order").attr('disabled', true);
                                        sln.call({
                                            url: '/internal/shop/rest/order/new',
                                            type: 'POST',
                                            data: {
                                                data: JSON.stringify({
                                                    customer_id: customer.id,
                                                    contact_id: contact,
                                                    items: orderList.selectedItems,
                                                    replace: true,
                                                    charge_interval: chargeInterval,
                                                })
                                            },
                                            success: function (data) {
                                                if (!data.success) {
                                                    $('#new_order_error span').text(data.errormsg);
                                                    $('#new_order_error').show();
                                                    return;
                                                }
                                                $('#new_order table tbody').empty();
                                                $('#new_order_total_excl_vat').empty();
                                                $('#new_order_vat_percentage').empty();
                                                $('#new_order_vat').empty();
                                                $('#new_order_total_incl_vat').empty();
                                                $('#new_order_error').hide();
                                                // Always go to create service, regardless if this is a new customer or not.
                                                showCreateService();
                                            },
                                            error: function () {
                                                $('#new_order_error span').text('Unknown error occurred!');
                                                $('#new_order_error').show();
                                            }, complete: function () {
                                                // Force the service and orders tabs to be reloaded
                                                currentCustomer.ordersLoaded = false;
                                                currentCustomer.default_modules = false;
                                                loadCustomer(currentCustomer.id, function (customer) {
                                                    for (var k in customer) {
                                                        if (customer.hasOwnProperty(k)) {
                                                            currentCustomer[k] = customer[k];
                                                        }
                                                    }
                                                });
                                                $("#button_create_new_order").attr('disabled', false);
                                            }
                                        });
                                    }, null, "Replace current order with new order", "Cancel");
                                } else {
                                    $('#new_order_error span').text(data.errormsg);
                                    $('#new_order_error').show();
                                }
                            }
                        },
                        error: function () {
                            $('#new_order_error span').text('Unknown error occurred!');
                            $('#new_order_error').show();
                        }, complete: function () {
                            currentCustomer.ordersLoaded = false;
                            currentCustomer.default_modules = false;
                            $("#button_create_new_order").attr('disabled', false);
                        }
                    });
                });

                $('#button_add_order_item').unbind('click').click(function () {
                    orderList.showAddItemDialog();
                });
            });
            $('#possible_order_item_count').change(function () {
                $('#order_item_count').val($(this).val());
            });
        });
    });
};

var renderProspect = function (prospect) {
    if (!prospect) {
        prospect = {};
        prospect.unassigned = true;
    } else {
        for (var i = 0; i < prospect.comments.length; i++) {
            prospect.comments[i].datetime = sln.format(new Date(prospect.comments[i].timestamp * 1000));
        }
    }
    if (prospect.subscription) {
        prospect.probableSubscription = (SUBSCRIPTION_TYPES[prospect.subscription]) + ', ';
    }
    var html = $.tmpl(JS_TEMPLATES['customer_popup/prospects_tab'], {
        prospect: prospect ? prospect : {}
    });
    var tab = $('#tab-prospect');
    tab.html(html);
    tab.find('.edit-prospect-type-btn').unbind('click').click(function () {
        $('#prospect-types-modal').modal('show');
    });
    tab.find('.edit-prospect-categories-btn').unbind('click').click(function () {
        $('#prospect-categories-modal').modal('show');
    });
    $('#prospect-categories-modal').find('input[type="checkbox"]').each(function () {
        var $this = $(this);
        $this.prop('checked', prospect.categories ? prospect.categories.indexOf($this.val()) !== -1 : false);
    });

    if (!prospect.unassigned) {
        $('#save-prospect-button, #button_save_prospect').hide();
        $('#edit-prospect-button').show().unbind('click').click(function () {
            tab.find('.edit').show().siblings().hide();
            $('#edit-prospect-button').hide();

            $('#prospect-types-modal').find('input[type="checkbox"]').each(function () {
                var $this = $(this);
                $this.prop('checked', prospect.types.indexOf($this.val()) != -1);
            });
            // show 'save' button
            $('#button_save_prospect').show().unbind('click').click(function () {
                putProspect(prospect.id);
                $('#button_save_prospect').hide();
                $('#edit-prospect-button').show();
                tab.find('.edit').hide().siblings().show();
            });
        });
        var historyContainer = $('#customer-prospect-history-container');
        historyContainer.html('');

        $('#customer-prospect-task-history').show().unbind('click').click(function () {
            $(this).hide();
            historyContainer.html(TMPL_LOADING_SPINNER)
                .css('min-height', '105px');
            sln.call({
                url: '/internal/shop/rest/prospect/task_history',
                data: {
                    id: currentCustomer.prospect.id
                },
                success: function (data) {
                    $.each(data, function (i, task) {
                        task.created = sln.format(new Date(task.creation_time * 1000));
                        task.closed = task.closed_time ? sln.format(new Date(task.closed_time * 1000)) : '';
                        var manager = currentRegioManagers[task.assignee]; //  currentRegioManagers is only filled in on the prospects page
                        if (manager) {
                            task.manager = manager.name;
                        } else {
                            task.manager = task.assignee;
                        }
                        task.type_icon = ShopTaskIcons[task.type];

                    });
                    var html = $.tmpl(JS_TEMPLATES.prospect_task_history, {
                        history: data
                    });
                    historyContainer.show().html(html);
                }
            });
        });
    } else {
        $('#edit-prospect-button, #button_save_prospect').hide();
        tab.find('.edit').show().siblings().hide();
    }
};

var putProspect = function (prospectId) {
    var tab = $('#tab-prospect');
    var data = {
        prospect_id: prospectId === undefined ? null : prospectId,
        name: tab.find('.edit-prospect-name').val(),
        phone: tab.find('.edit-prospect-phone').val(),
        address: tab.find('.edit-prospect-address').val(),
        email: tab.find('.edit-prospect-email').val() || null,
        website: tab.find('.edit-prospect-website').val() || null,
        comment: tab.find('.edit-prospect-comment').val() || null,
        types: $('#prospect-types-modal').find('input[type="checkbox"]:checked').map(function () {
            return this.value;
        }).get(),
        categories: $('#prospect-categories-modal').find('input[type="checkbox"]:checked').map(function () {
            return this.value;
        }).get()
    };

    if (!data.name) {
        showError('Name is required');
        return;
    }
    if (!data.address) {
        showError('Address is required');
        return;
    }
    if (!data.types.length) {
        showError('Type is required');
        return;
    }

    if (!prospectId) {
        // new prospect
        data.prospect_id = null;
        data.status = StatusType.TODO;
        data.app_id = tab.find('.edit-prospect-app-id').val();

        if (!data.app_id) {
            showError('App is required');
            return;
        }
    } else {
        if (!data.phone) {
            showError('Phone is required');
            return;
        }
    }

    showProcessing('Saving prospect');
    sln.call({
        url: '/internal/shop/rest/prospect/put',
        type: 'post',
        data: {
            data: JSON.stringify(data)
        },
        success: function (data) {
            hideProcessing();
            if (!data.success) {
                showError(data.errormsg);
                return;
            }
            // show the newly created / updated prospect in this tab.
            currentCustomer.prospect = data.prospect;
            showProspect();
        },
        error: function () {
            hideProcessing();
            showError('An unknown error occurred. Check with the administrators.');
        }
    });
};

function renderContacts(data) {
    var html = $.tmpl(JS_TEMPLATES['customer_popup/contacts_tab'], {
        contacts: data
    });
    $('#tab-contacts').html(html);
    // `Add contact` button
    $('#add-contact-button').unbind('click').click(function () {
        showAddContact();
    });
    $('.contact-card').unbind('click').click(function () {
        var contactId = parseInt($(this).attr('data-contact-id'));
        var contact = data.find(c => c.id === contactId);
        showEditContact(contact);
    });
    //Prevent popup from showing up when clicking the email or phone links.
    $('.contact-card').find('a').unbind('click').click(function (e) {
        e.stopPropagation();
    });
}

var showEditContact = function (contact) {
    //Recycle the 'add contact' form, but hide the customer field.
    var err = $('#new_contact_error').hide();
    var form = $('#contact_form');
    form.find('input').val('');
    form.modal('show');
    form.find('.update_contact').show();
    form.find('.add_contact').hide();

    // fill in the form values
    $.each(contact, function (prop, val) {
        form.find('#' + prop).val(val);
    });

    form.find('#button_update_contact').unbind('click').click(function () {
        // save changes
        var updatedContact = {
            first_name: form.find('#first_name').val().trim(),
            last_name: form.find('#last_name').val().trim(),
            email: form.find('#email').val().trim(),
            phone_number: form.find('#phone_number').val().trim()
        }
        if (!(updatedContact.first_name && updatedContact.last_name && updatedContact.email && updatedContact.phone_number)) {
            err.show().find('span').text('Not all required fields are filled!');
            return;
        }
        ShopRequests.updateContact(currentCustomer.id, contact.id, updatedContact).then(() => {
            $('#contact_form').modal('hide');
            showContacts(currentCustomer.id, true);
        });
    });

    form.find('#button_remove_contact').unbind('click').click(function () {
        ShopRequests.deleteContact(currentCustomer.id, contact.id).then(() => {
            $('#contact_form').modal('hide');
            return ShopRequests.getContacts(currentCustomer.id, {cached: false}).then(contacts => renderContacts(contacts));
        });
    });
};

var showAddContact = function () {
    // show the 'add contact' tab
    $('#new_contact_error').hide();
    var form = $('#contact_form');
    // Hide things from the 'update contact' form
    form.find('.update_contact').hide();
    form.find('.add_contact').show();
    form.find('input').val('');
    form.modal('show');

    // Try to pre-fill by prospect
    var prospect = $('#customer_form').data('prospect');
    if (prospect) {
        var splittedName = prospect.name.split('/');
        if (splittedName.length == 2) {
            form.find('#first_name').val(splittedName[1]);
            form.find('#last_name').val(splittedName[0]);
        }
        form.find('#email').val(prospect.email);
        form.find('#phone_number').val(prospect.phone);
    }
};

var showChangeServiceEmail = function (customer) {
    // remove any existing popups
    $('#change_service_email_form').remove();

    // clone popup tmpl
    var tmpl = $('#change_service_email_tmpl');
    var modal = $(tmpl.clone().attr('id', 'change_service_email_form'));
    tmpl.parent().append(modal);
    modal.modal('show');
    $('#service-email-container', modal).text(customer.name);
    $('#new_service_email').val(customer.service_email);

    var showErrorMessage = function (msg) {
        if (msg) {
            $('#change_service_email_form #change_service_email_error').show();
            $('#change_service_email_form #change_service_email_error span').empty().text(msg);
            $('#change_service_email_form .modal-body').scrollTop(0);
        } else {
            $('#change_service_email_form #change_service_email_error').hide();
            $('#change_service_email_form #change_service_email_error span').empty();
            $('#change_service_email_form .error').removeClass('error');
        }
    };

    $('#new_service_email', modal).val(customer.user_email);

    $('#button_start_change_service_email', modal).unbind('click').click(function () {
        var newServiceEmail = $('#new_service_email', modal).val();

        if (!newServiceEmail || !newServiceEmail.trim()) {
            showErrorMessage("New service e-mail is required");
            return;
        }

        // hide error
        showErrorMessage(null);

        showProcessing("Starting job...");
        sln.call({
            url: '/internal/shop/rest/service/change_email',
            type: 'POST',
            data: {
                data: JSON.stringify({
                    email: newServiceEmail,
                    customer_id: customer.id
                })
            },
            success: function (data) {
                hideProcessing();
                if (data.success) {
                    modal.modal('hide');
                    if (data.job_key) {
                        followJob(data.job_key);
                    }
                } else {
                    showErrorMessage(data.errormsg);
                }
            },
            error: function () {
                hideProcessing();
                showErrorMessage('An unknown error occurred!');
            }
        });
    });
};

var showAddLocation = function(customer) {
    askInput(function(val) {
        showProcessing("Adding location...");
        sln.call({
            url: '/internal/shop/rest/location/add',
            type: 'POST',
            data: {
                data: JSON.stringify({
                    customer_id: customer.id,
                    name: val
                })
            },
            success: function (data) {
                if (!data.success) {
                    hideProcessing();
                    alert(data.errormsg);
                    return;
                }
            },
            error: function () {
                hideProcessing();
                alert('An unknown error occurred. Check with the administrators.');
            }
        });

        return true;
    }, 'Name of the new location');
};

var followJob = function (job) {
    // remove any existing popups
    $('#follow_job_popup').remove();

    // clone popup tmpl
    var tmpl = $('#follow_job_tmpl');
    var modal = $(tmpl.clone().attr('id', 'follow_job_popup'));
    tmpl.parent().append(modal);
    modal.modal('show');

    var showErrorMessage = function (msg) {
        if (msg) {
            $('#follow_job_popup #follow_job_error').show();
            $('#follow_job_popup #follow_job_error span').empty().text(msg);
            $('#follow_job_popup .modal-body').scrollTop(0);
        } else {
            $('#follow_job_popup #follow_job_error').hide();
            $('#follow_job_popup #follow_job_error span').empty();
            $('#follow_job_popup .error').removeClass('error');
        }
    };

    var stop = [false];

    $('#button_close', modal).unbind('click').click(function () {
        stop[0] = true;
        modal.modal('hide');
        showCreateService();
    });

    var poll = function () {
        if (stop[0]) {
            return;
        }

        sln.call({
            url: '/internal/shop/rest/job/get_status',
            type: 'GET',
            data: {
                job: job
            },
            success: function (data) {
                if (!data) {
                    showErrorMessage("Job not found");
                    $('.bar', modal).addClass('bar-error');
                    return;
                }

                $('.bar', modal).css('width', data.progress + '%');
                if (data.phase == -1) {
                    $('.progress', modal).removeClass('active');
                    $('.bar', modal).addClass('bar-success');
                    $('#follow_job_completed', modal).show();
                } else {
                    // job is not finished yet
                    setTimeout(poll, 2000);
                }
            },
            error: function () {
                setTimeout(poll, 2000);
                console.error('An unknown error ocurred while getting status for job ' + job);
            }
        });
    };

    poll();
};

var setCustomerDetails = function () {
    var customerForm = $('#customer_form');
    if (currentCustomer.id) {
        $('form', customerForm).each(function () {
            var form = $(this);
            if (!form.hasClass('new-customer-only')) {
                form.fadeIn();
            }
        });
        $('#search_customer_name', customerForm).data('customer', currentCustomer).val(currentCustomer.name);
        $('#customer_number', customerForm).val(currentCustomer.id.toString().replace(/(\d)(?=(\d\d\d\d)+(?!\d))/g, "$1."))
            .unbind('click').click(function () {
            this.select();
        }).parent().show();

    } else {
        $('#customer_number', customerForm).val(null).parent().hide();
    }
    $("#customer_organization_type", customerForm).val('' + currentCustomer.organization_type).change();
    $("#vat", customerForm).val(currentCustomer.vat);
    $("#customer_name", customerForm).val(currentCustomer.name);
    $("#address1", customerForm).val(currentCustomer.address1);
    $("#address2", customerForm).val(currentCustomer.address2);
    $("#zipcode", customerForm).val(currentCustomer.zip_code);
    $("#city", customerForm).val(currentCustomer.city);
    $("#country", customerForm).val(currentCustomer.country);
    if (currentCustomer.creating) {
        // prefill with the most used language in that country
        $("#language", customerForm).val(DEFAULT_LANGUAGES[currentCustomer.country]);
    } else {
        // do not pre-fill when the customer has no language assigned
        $("#language", customerForm).val(currentCustomer.language ? currentCustomer.language : '');
    }
};

var initCustomerForm = function (customer) {
    currentCustomer = customer;
    var customerForm = $('#customer_form');
    $('.modal-footer', customerForm).show();
    $('#new_customer_error', customerForm).hide();

    if (customerForm.data('mode') == CustomerFormType.LINK_PROSPECT) {
        $('.migrating-only', customerForm).hide();
    } else if (customer.migration_job) {
        $('.migrating-only', customerForm).show();
    } else if (customer.service_email || !customer.id) {
        $('.migrating-only', customerForm).hide();
    } else {
        $('.migrating-only', customerForm).hide();
    }

    $("#button_new_contact", customerForm).unbind('click').click(function () {
        if ($(this).attr('disabled'))
            return;

        showAddContact();
    });

    $("#button_follow_job", customerForm).unbind('click').click(function () {
        if ($(this).attr('disabled'))
            return;

        followJob(currentCustomer.migration_job);
    });

    $('#button_cancel_subscription', customerForm).unbind('click').click(cancelSubscriptionClicked);

    //show all tab links, and select 'Details' tab by default
    $('#tab-nav-container').find('a').parent().show();
    $('#tab-nav-container').find('a:first').click();

    if (customer.id || currentMode == CustomerFormType.NEW) {
        showDetails();
    }
};

var showRelevantButtons = function (tabType) {
    var form = $('#customer_form');
    // show the tab
    form.find('a[data-target=#tab-' + tabType + ']').tab('show');
    $.each(TABTYPES, function (i, t) {
        if (t == tabType) {
            form.find('.' + t + '-only').show();
        } else {
            form.find('.' + t + '-only').hide();
        }
    });
    if (currentCustomer.name) {
        $('#button_discover').hide();
    }
    if (currentCustomer.id) {
        $('#button_add_customer').hide();
    }

    if (currentCustomer.auto_login_url) {
        form.find("#button_login_as_service")
            .show()
            .attr('href', currentCustomer.auto_login_url);
    } else {
        form.find("#button_login_as_service").hide();
    }
};

var showOrders = function (refresh) {
    if (currentCustomer.id === undefined) {
        console.error('Trying to show orders while there is no current customer');
        return;
    }

    $('#customer_form').find('a[data-target="#tab-orders"]').tab('show');
    showRelevantButtons(TABTYPES.ORDERS);
    $('#button_cancel_subscription').toggle(currentCustomer.subscription !== -1 && (currentCustomer.is_admin || currentCustomer.can_edit) && currentCustomer.service_disabled_at === 0);
    if (!refresh && currentCustomer.ordersLoaded) {
        renderBilling();
    } else {
        loadOrdersAndInvoices();
    }
    $('#button_set_next_charge_date').toggle(currentCustomer.is_admin || currentCustomer.can_edit).unbind('click').click(showSetNextChargeDate);
};

function showQuotations(refresh) {
    var tab = $('#tab-quotations');
    tab.html(TMPL_LOADING_SPINNER);
    showRelevantButtons(TABTYPES.QUOTATIONS);
    var contactsPromise = ShopRequests.getContacts(currentCustomer.id);
    var productsPromise = ShopRequests.getProducts(currentCustomer.language);
    var quotationsPromise = ShopRequests.getQuotations(currentCustomer.id, {cached: !refresh});
    Promise.all([contactsPromise, productsPromise, quotationsPromise]).then(([contacts, products, quotations]) => {
        getLegalEntity(legalEntity => {
            var html = $.tmpl(JS_TEMPLATES['customer_popup/quotations_tab'], {
                contacts: contacts
            });
            tab.html(html);
            renderQuotations(legalEntity, quotations);
            var itemList = new OrderItemList($('#quotation-item-list'), legalEntity, products, currentCustomer.organization_type);
            itemList.render();
            $('#add-quotation-item').click(() => itemList.showAddItemDialog());
            var createButton = $('#create-quotation');
            createButton.click(() => {
                if (createButton.prop('disbaled')) {
                    return;
                }
                createButton.prop('disabled', true);
                var quotation = {
                    contact_id: parseInt($('#new_quotation_contact').val(), 10),
                    order_items: itemList.selectedItems,
                };
                ShopRequests.createQuotation(currentCustomer.id, quotation).then(() => {
                    createButton.prop('disabled', false);
                    itemList.selectedItems = [];
                    itemList.render();
                    ShopRequests.getQuotations(currentCustomer.id, {cached: false}).then(quotations => {
                        renderQuotations(legalEntity, quotations);
                    });
                }).catch(() => createButton.prop('disabled', false));
            });
        });
    });
}

function renderQuotations(legalEntity, quotations) {
    var html = $.tmpl(JS_TEMPLATES['customer_popup/quotations_list'], {
        quotations: quotations.map(q => Object.assign({}, q, {
            date: sln.format(new Date(q.date * 1000)),
            total_amount: `${legalEntity.currency} ${(q.total_amount / 100).toFixed(2)}`,
        }))
    });
    $('#quotations-list').html(html);
}

var renderBilling = function () {
    var html = $.tmpl(JS_TEMPLATES['customer_popup/billing_tab'], {
        unsigned_orders: currentCustomer.unsigned_orders,
        invoices: currentCustomer.invoices,
        orders: currentCustomer.signed_orders,
        canceledOrders: currentCustomer.canceled_orders
    });
    $("#tab-orders").html(html).find('a.sign-order').unbind('click').click(function () {
        var $this = $(this);
        sln.call({
            url: '/internal/shop/stat/view-order.part.html',
            success: function (page) {
                $("#extra-content").append(page);
                if (!currentCustomer.service_email) {
                    showAlert('This customer does not have a service yet. First create a service for this customer.'
                        , null, "Error");
                    return;
                }
                var order_number = $this.attr('order_number');
                $('#pdf-viewer').attr('src', '/static/pdfdotjs/web/viewer.html?file=' + encodeURIComponent('/internal/shop/order/pdf?customer_id=' + currentCustomer.id +
                    '&order_number=' + order_number + '&download=false'));
                $('#button_sign_order').show();
                $('#view_order_form').modal('show').data('order', {
                    customer_id: currentCustomer.id,
                    order_number: order_number
                });
            }
        });
    });
    $('button.cancel-order').unbind('click').click(function () {
        var $this = $(this);
        var orderNumber = $this.attr('order_number');
        sln.confirm('Are you sure you want to cancel order ' + orderNumber + '?', onConfirm);

        function onConfirm() {
            sln.call({
                url: '/internal/shop/rest/order/cancel',
                method: 'POST',
                data: {
                    customer_id: parseInt($this.attr('customer_id')),
                    order_number: orderNumber,
                },
                success: function () {
                    loadOrdersAndInvoices();
                }
            });
        }
    });
};

var loadOrdersAndInvoices = function () {
    sln.call({
        url: '/internal/shop/orders/load_all',
        type: 'GET',
        data: {
            customer_id: currentCustomer.id
        },
        success: function (data) {
            currentCustomer.unsigned_orders = data.unsigned_orders;
            currentCustomer.signed_orders = data.signed_orders;
            currentCustomer.canceled_orders = data.canceled_orders;
            currentCustomer.invoices = data.invoices;
            currentCustomer.ordersLoaded = true;
            renderBilling();
        },
        error: sln.showAjaxError
    });
};


function showHistory () {
    $('#customer_form').find('[data-target=#tab-history]').tab('show');
    showRelevantButtons(TABTYPES.HISTORY);
    if (currentCustomer.prospect_id) {
        sln.call({
            url: '/internal/shop/prospect/history',
            type: 'GET',
            data: {
                prospect_id: currentCustomer.prospect_id
            },
            success: function (data) {
                renderProspectHistory(data);
            },
            error: sln.showAjaxError
        });
    } else {
        renderProspectHistory(null);
    }
}

function renderProspectHistory (data) {
    if (data != null) {
        // sort by date (newest first)
        data.sort(function (a, b) {
            return a.created_time < b.created_time;
        });
        for (var i = 0; i < data.length; i++) {
            data[i].status = StatusTypeStrings[data[i].status];
            data[i].datetime = sln.format(new Date(data[i].created_time * 1000));
        }
    }
    var html = $.tmpl(JS_TEMPLATES['customer_popup/history_tab'], {
        history: data
    });
    $("#tab-history").html(html);
}

$(function () {
    loadRegioManagerTeams();

    customer_selected.push(function (sender, customer) {
        if (sender.attr('id') != 'search_customer_name')
            return;
        initCustomerForm(customer);
    });

    $('#customer_form').find('#search_customer_name').change(function () {
        if ($(this).val() == "") {
            prepareSearchCustomer();
        }
    });

    $("a.set-manager").click(
        function () {
            $("#set_manager").attr("customer_id", $(this).attr("customer_id")).attr("order_number",
                $(this).attr("order_number")).modal('show');
        });

    $("#button_set_manager").unbind('click').click(function () {
        var customer_id = parseInt($("#set_manager").attr("customer_id"));
        var order_number = $("#set_manager").attr("order_number");
        var manager = $("#order_manager").val();
        showProcessing("Setting manager");
        sln.call({
            url: '/internal/shop/rest/order/set_manager',
            type: 'POST',
            data: {
                data: JSON.stringify({
                    customer_id: customer_id,
                    order_number: order_number,
                    manager: manager
                })
            },
            success: function (data) {
                window.location.reload();
            },
            error: function () {
                hideProcessing();
                showErrorMessage('An unknown error occurred!');
            }
        });
    });

    $('#menu_new_customer, #menu_search_customer').unbind('click').click(function () {
        $('#new_customer_error').hide();
        var isNew = (this.id == 'menu_new_customer');
        showCustomerForm(isNew ? CustomerFormType.NEW : CustomerFormType.SEARCH);
    });

    $('#form_search_customer_name').submit(function (e) {
        e.preventDefault();
    });
    $('#customer_form #search_customer_name').typeahead(type_ahead_options);

    var putCustomer = function (customerId, force) {
        var name = $('#customer_form #customer_name').val();
        var address1 = $('#customer_form #address1').val();
        var address2 = $('#customer_form #address2').val();
        var zipcode = $('#customer_form #zipcode').val();
        var city = $('#customer_form #city').val();
        var country = $('#customer_form #country').val();
        var language = $('#customer_form').find('#language').val();
        var prospect = $('#customer_form').data('prospect');
        var type = parseInt($('#customer_form #customer_organization_type').val());
        if (!(name && address1 && zipcode && city && country && type)) {
            $('#new_customer_error').show()
                .find('span').text('Not all required fields are filled');
            return;
        } else {
            $('#new_customer_error').hide();
        }

        var vat = $('#customer_form #vat').val() || null;

        var teamId = currentCustomer.team_id;
        if (currentCustomer.is_admin) {
            teamId = $('#team-select').val();
        }
        if (currentCustomer.country != country) {
            delete currentCustomer.vat_percent;
        }

        sln.call({
            url: '/internal/shop/rest/customer/put',
            type: 'POST',
            data: {
                data: JSON.stringify({
                    force: force,
                    organization_type: type,
                    name: name,
                    address1: address1,
                    address2: address2,
                    zip_code: zipcode,
                    city: city,
                    country: country,
                    language: language,
                    vat: vat,
                    prospect_id: prospect ? prospect.id : null,
                    customer_id: customerId,
                    team_id: parseInt(teamId)
                })
            },
            success: function (data) {
                if (data.success) {
                    $('#new_contact_error, #new_customer_error').hide();
                    if (customerId == null) {
                        var creating = currentCustomer.creating;
                        currentCustomer = data.customer;
                        currentCustomer.creating = creating;
                        showAddContact();
                    } else {
                        // Updated existing customer
                        currentCustomer = data.customer;
                        showDetails();
                        showAlert('Customer saved', null, 'Saved', 3000);
                    }
                } else if (data.warning) {
                    // warnings like duplicated customer name
                    showConfirmation(data.warning + "<br><br>Are you sure you wish to continue?", function () {
                        putCustomer(customerId, true);
                    });
                } else {
                    // other warnings, e.g. field x not filled in
                    $('#new_customer_error').show().find('span').text(data.errormsg);
                }
            },
            error: function () {
                $('#new_customer_error').show().find('span').text('Unknown error occurred!');
            }
        });
    };

    $('#customer_form').on('hidden', function (e) {
        if (e.target.id !== 'customer_form') {
            return;
        }
        currentCustomer = {};
        newService = {};
        currentMode = null;
        currentSubscription = null;
        $('#search_customer_name').val('');
        $(this).data('prospect', null).data('mode', null);
    });

    $('#customer_form #customer_organization_type').change(function () {
        var type = parseInt($('#customer_form #customer_organization_type').val());
        var vatControls = $('#customer_form #vat').parents('div.controls');
        if (type == OrganizationType.MERCHANT || type == OrganizationType.CARE) {
            $("label", vatControls).text('VAT');
        } else {
            $("label", vatControls).text('VAT (optional)');
        }
    });

    $('#button_add_customer, #button_save_customer').unbind('click').click(function () {
        if ($(this).attr('disabled')) {
            return;
        }

        var customerId = null;
        if (this.id == 'button_save_customer')
            customerId = currentCustomer.id;

        putCustomer(customerId, false);
    });

    $('#customer_form #button_link_prospect').unbind('click').click(function () {
        var customer = $('#customer_form #search_customer_name').data('customer');
        var prospectId = $('#customer_form').data('prospect');
        // linkProspectToCustomer is defined in prospects.js
        linkProspectToCustomer(customer.id, prospectId, function (data) {
            // show tab 'prospects'
            showProspect(true);
        });
    });

    $('#button_add_contact').click(
        function () {
            var first = $('#contact_form #first_name').val();
            var last = $('#contact_form #last_name').val();
            var email = $('#contact_form #email').val();
            var phone = $('#contact_form #phone_number').val();

            if (!(currentCustomer.id && first && last && email && phone)) {
                $('#new_contact_error').show().find('span').text('Not all required fields are filled!');
                return;
            }
            if (!EMAIL_REGEX.test(email)) {
                $('#new_contact_error').show().find('span').text('Invalid email address');
                return;
            }
            var contact = {
                first_name: first,
                last_name: last,
                email: email,
                phone_number: phone
            };
            ShopRequests.addContact(currentCustomer.id, contact).then(() => {
                currentMode = CustomerFormType.SEARCH;
                $('#contact_form').modal('hide');
                if (currentCustomer.creating) {
                    showNewOrder();
                } else {
                    showContacts(currentCustomer.id, true);
                }
            });
        });

    $('#country').change(function () {
        if (!currentCustomer.id) {
            // set default language to the main language of this country
            var countryCode = $(this).val();
            $('#language').val(DEFAULT_LANGUAGES[countryCode]);
        }
    });

    $('#button_discover').click(
        function () {
            $('#select_company_info').text('Discovering companies in the neighbourhood ...').show();
            $('#select_company_error').hide();
            $('#select_company').modal('show');
            var tbody = $('#select_company table tbody').empty();
            navigator.geolocation.getCurrentPosition(function (location) {
                sln.call({
                    url: '/internal/shop/rest/company/discover',
                    data: {
                        lat: location.coords.latitude,
                        lon: location.coords.longitude
                    },
                    success: function (data) {
                        if (!data) {
                            $('#select_company_error span').text(
                                'Failed to discover comapnies in the neighbourhood!');
                            $('#select_company_error').show();
                            $('#select_company_info').hide();
                            return;
                        }

                        data.sort(function (a, b) {
                            var lowerCaseA = a.name.toLowerCase();
                            var lowerCaseB = b.name.toLowerCase();
                            if (lowerCaseA < lowerCaseB)
                                return -1;
                            if (lowerCaseA > lowerCaseB)
                                return 1;
                            return 0;
                        });

                        $('#select_company_info').text('Found ' + data.length + ' companies!');
                        $.each(data, function (i, company) {
                            var tr = $('<tr></tr>').append(
                                $('<td></td>').text(
                                    company.name + ', ' + company.address1
                                    + (company.address2 ? ', ' + company.address2 : '') + ', '
                                    + company.zip_code + ', ' + company.city));
                            tr.unbind('click').click(function () {
                                $('#customer_form #vat').val(company.vat);
                                $('#customer_form #customer_name').val(company.name);
                                $('#customer_form #address1').val(company.address1);
                                $('#customer_form #address2').val(company.address2);
                                $('#customer_form #zipcode').val(company.zip_code);
                                $('#customer_form #city').val(company.city);
                                $('#customer_form #country').val(company.country).change();
                                $('#customer_form #customer_organization_type').val('' + OrganizationType.MERCHANT)
                                    .change();
                                $('#new_customer_error').hide();
                                $('#select_company').modal('hide');
                            });
                            tbody.append(tr);
                        });
                    },
                    error: function () {
                        $('#select_company_error span').text('Unknown error occurred!');
                        $('#select_company_error').show();
                        $('#select_company_info').hide();
                    }
                });
            });
        });

    $('#button_cancel_customer').unbind('click').click(function () {
        $('#customer_form').modal('hide');
    });

    $('#payment_info_modal .btn').unbind('click').click(function () {
        var modal = $('#payment_info_modal');
        var finished = $(this).attr('success') == "true";
        if (!finished) {
            modal.modal('hide');
            $('#payment_options_modal').modal('show');
            return;
        }

        var chargeReference = modal.data('chargeReference');
        var customerId = modal.data('customerId');
        var customerUserEmail = modal.data('customerUserEmail');

        showProcessing("Processing ...");
        sln.call({
            url: '/internal/shop/rest/charge/finish_on_site_payment',
            type: 'POST',
            data: {
                data: JSON.stringify({
                    charge_reference: chargeReference,
                    customer_id: customerId
                })
            },
            success: function (data) {
                hideProcessing();
                if (!data.success) {
                    alert(data.errormsg);
                    return;
                }

                modal.modal('hide');

                var paymentCompletedModal = $('#payment_completed_modal').modal('show');
                if (customerUserEmail) {
                    $('.invoice-not-sent-yet', paymentCompletedModal).hide();
                    $('.invoice-sent', paymentCompletedModal).show();
                    $('.create-service', paymentCompletedModal).removeAttr('customer_id');
                } else {
                    $('.invoice-not-sent-yet', paymentCompletedModal).show();
                    $('.invoice-sent', paymentCompletedModal).hide();
                    $('.create-service', paymentCompletedModal).attr('customer_id', customerId);
                }

                paymentCompletedModal.unbind('hide').on('hide', function () {
                    if (customerUserEmail) {
                        if ($('#customer_form').css('display') == 'block') {
                            showOrders(true);
                        } else {
                            window.location.reload();
                        }
                    }
                });
            },
            error: function () {
                hideProcessing();
                showAlert("An unknown error occurred, please report this to the administrators.");
            }
        });
    });

    $('#export-customers').click(function () {
        sln.call({
            url: '/internal/shop/rest/customers/export',
            success: function (data) {
                if (data.success) {
                    sln.alert('You will receive an email with the exported customers within a few minutes.');
                }
            }
        });
    });

    $('#export-cirklo-customers').click(function () {
    	 sln.call({
    		 url: '/internal/shop/rest/apps/all',
             success: function (data) {
                 var html = $.tmpl(JS_TEMPLATES.app_select_modal, {
                	 apps: data,
                	 selectedApp: 'osa-demo2'
                 });

                 var modal = sln.createModal(html);
                 $('button[action=submit]', modal).click(function() {
                	 modal.modal('hide');
                	 var appId = $('#app_select').val();
                	 sln.call({
                         url: '/internal/shop/rest/customers/cirklo/export',
                         data: {
                             app_id: appId
                         },
                         success: function (data) {
                             if (data.success) {
                                 sln.alert('You will receive an email with the exported customers within a few minutes.');
                             }
                         }
                     });
                 });
             }
    	 });
    });

    $(document).click(function (e) {
        "use strict";
        var $this = $(e.target);
        if ($this.attr('open-customer-popup')) {
            var customerId = parseInt($this.attr('open-customer-popup'));
            if (!customerId || isNaN(customerId)) {
                console.warning('Invalid customer id for node', customerId, $this);
            } else {
                loadCustomer(customerId, function (customer) {
                    initCustomerForm(customer);
                    showCustomerForm(CustomerFormType.OPEN_TAB, showDetails, customer.id);
                });
            }
        }
    });
});

/*
 Returns RegioManagers for specified app id. Caches results to limit server requests.
 */
function getManagersForApp (appId, callback) {
    if (regioManagersPerApp[appId]) {
        setCurrentRegioManagers(regioManagersPerApp[appId]);
        callback(regioManagersPerApp[appId]);
    }
    else {
        sln.call({
            url: '/internal/shop/rest/regio_manager/get_all_by_app',
            data: {app_id: appId},
            showProcessing: true,
            success: function (data) {
                regioManagersPerApp[appId] = data;
                setCurrentRegioManagers(data);
                callback(data);
            },
            error: function () {
                sln.alert('Could not load regiomanagers');
            }
        });
    }
}

function cancelSubscriptionClicked () {
    var cancelSubscriptionButton = $(this);
    var valid = true;
    if (!cancelSubscriptionButton.attr('disabled')) {
        cancelSubscriptionButton.attr('disabled', true);
        var html = $.tmpl(JS_TEMPLATES['customer_popup/cancel_order_modal_content'], {
            customer: currentCustomer
        });
        var title = 'Cancel subscription';
        var positiveCaption = 'Cancel subscription';
        var negativeCaption = 'Abort';
        sln.confirm(html.html(), doCancelSubscription, abortCancelSubscription, positiveCaption, negativeCaption, title, closeCheck);
    }

    function doCancelSubscription () {
        var cancelReasonElem = $('#cancelSubscriptionReason');
        var cancelReason = cancelReasonElem.val();
        valid = true;
        if (!cancelReason) {
            cancelReasonElem.parent().addClass('error');
            valid = false;
        } else {
            cancelReasonElem.parent().removeClass('error');
        }
        if (valid) {
            cancelSubscriptionRest(cancelReason, subscriptionCanceledResponse);
        }
    }

    function closeCheck () {
        return valid;
    }

    function subscriptionCanceledResponse (data) {
        if (data.success && typeof(data.success) !== 'function') {
            sln.alert('The subscription has been canceled.');
            cancelSubscriptionButton.hide();
            var customerId = currentCustomer.id;
            currentCustomer = {};
            loadCustomer(customerId, function (customer) {
                currentCustomer = customer;
                showDetails();
            });
        } else {
            sln.alert(data.errormsg || 'An unexpected error occured.');
        }
        cancelSubscriptionButton.attr('disabled', false);
    }

    function abortCancelSubscription () {
        cancelSubscriptionButton.attr('disabled', false);
    }
}

function cancelSubscriptionRest (cancelReason, callback) {
    sln.call({
        url: '/internal/shop/rest/order/cancel_subscription',
        method: 'post',
        showProcessing: 'Canceling subscription...',
        data: {customer_id: currentCustomer.id, cancel_reason: cancelReason},
        success: callback,
        error: callback
    });
}

function showSetNextChargeDate () {
    'use strict';
    sln.call({
        url: '/internal/shop/rest/order/get_subscription_order',
        data: {
            customer_id: currentCustomer.id
        },
        success: function (data) {
            if (data.success === true) {
                var modal = $('#adjust_next_charge_date_modal').modal('show');
                var datePicker = $('#adjust-next-charge-date').datepicker().data('datepicker');
                datePicker.setValue(new Date(data.order.next_charge_date*1000));
                $('#btn-set-next-charge-date').unbind('click').click(function () {
                    sln.call({
                        url: '/internal/shop/rest/customer/set_next_charge_date',
                        method: 'post',
                        data: {
                            customer_id: currentCustomer.id,
                            next_charge_date: datePicker.date.getTime() / 1000
                        },
                        success: function (data) {
                            if (data.success !== true) {
                                sln.alert(data.errormsg);
                            } else {
                                modal.modal('hide');
                            }
                        }
                    })
                    ;
                });
            } else {
                sln.alert(data.errormsg);
            }
        }
    });
}

function getLegalEntity(callback) {
    // Prevent firing multiple ajax requests to get the legal identity in case this method is called before the request
    // to get the legal identity is finished
    _legalEntityCallbacks.push(callback);
    if (LEGAL_ENTITY) {
        doCallbacks();
    } else if (_legalEntityCallbacks.length === 1) {
        sln.call({
            url: '/internal/shop/rest/legal_entity',
            success: function (data) {
                LEGAL_ENTITY = data;
                LEGAL_ENTITY.getVatPercent = function () {
                    return !currentCustomer.vat || LEGAL_ENTITY.country_code === currentCustomer.country ? LEGAL_ENTITY.vat_percent : 0;
                };
                doCallbacks();
            }
        });
    }
    function doCallbacks() {
        for (var i = 0; i < _legalEntityCallbacks.length; i++) {
            _legalEntityCallbacks[i](LEGAL_ENTITY);
        }
        _legalEntityCallbacks = [];
    }
}
