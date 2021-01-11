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
    OPEN_TAB: 'open-tab'
};
var TABTYPES = {
    DETAILS: 'details',
    CONTACTS: 'contacts',
    SERVICE: 'service'
};

var currentMode;

var logoUrl = '/static/images/shop/osa_white_en_64.jpg';
var _processingTimeout;

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

var customerMap = {};
var type_ahead_options = {
    source: function (query, resultHandler) {
        // Only send the ajax request after the user stopped typing
        if (type_ahead_timeout) {
            clearTimeout(type_ahead_timeout);
        }
        type_ahead_timeout = setTimeout(function () {
            sln.call({
                url: '/internal/shop/rest/customer/find',
                data: {
                    search_string: query,
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

function prepareNewCustomer() {
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
    $('#customer_form #country').off('change').on('change', function(){
        var country = $(this).val();
        getCustomerCommunities(country);
    });
    getCustomerCommunities(currentCustomer.country);
}

async function getCustomerCommunities(country){
    const communities = await (await fetch('/console-api/communities?country=' + country)).json();
    const communitySelect = $('#customer_form #customer-community-id');
    communitySelect.empty();
    communitySelect.append('<option></option>');
    for (const community of communities){
        communitySelect.append(`<option value="${community.id}">${community.name}</option>`);
    }
}

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
            case '#tab-service':
                showCreateService();
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
        $('#user-email').text(currentCustomer.user_email ? currentCustomer.user_email : 'none');
        $('#service-email').text(currentCustomer.service_email)
            .parent().toggle(!!currentCustomer.service_email);
        $('#customer-website').text(currentCustomer.website || '-');
        $('#customer-facebook').text(currentCustomer.facebook_page || '-');
        $('#customer-creation-time').text(sln.format(new Date(currentCustomer.creation_time * 1000)));
        $('#service-status').toggle(currentCustomer.service_disabled_at !== 0);
        $('#service-disabled-at').text(sln.format(new Date(currentCustomer.service_disabled_at * 1000)));
        $('#service-disabled-reason').text(currentCustomer.service_disabled_reason);

        $('#other-customer-info').removeClass('hide');
    } else {
        $('#other-customer-info').addClass('hide');
    }
    if (currentMode == CustomerFormType.NEW) {
        $('#tab-nav-container').find('a').parent().hide();
        currentCustomer.creating = true;
    } else if (currentMode == CustomerFormType.SEARCH || currentMode == CustomerFormType.OPEN_TAB) {
        $('#button_save_customer').show();
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

    if (customer.migration_job) {
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
    if (currentCustomer.id) {
        $('#button_add_customer').hide();
    } else {
    	$('#button_save_customer').hide();
    }

    if (currentCustomer.auto_login_url) {
        form.find("#button_login_as_service")
            .show()
            .attr('href', currentCustomer.auto_login_url);
    } else {
        form.find("#button_login_as_service").hide();
    }
};

$(function () {
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
        var communityId = $('#customer_form #customer-community-id').val();
        var language = $('#customer_form').find('#language').val();
        var type = parseInt($('#customer_form #customer_organization_type').val());
        if (!(name && address1 && zipcode && city && country && type) || (!customerId && !communityId)) {
            $('#new_customer_error').show()
                .find('span').text('Not all required fields are filled');
            return;
        } else {
            $('#new_customer_error').hide();
        }

        var vat = $('#customer_form #vat').val() || null;
        if (currentCustomer.country != country) {
            delete currentCustomer.vat_percent;
        }

        sln.call({
            url: '/internal/shop/rest/customer/put',
            type: 'POST',
            data: {
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
                customer_id: customerId,
                community_id: communityId ? parseInt(communityId) : undefined,
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
        $('#search_customer_name').val('');
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
                    showCreateService();
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

    $('#button_cancel_customer').unbind('click').click(function () {
        $('#customer_form').modal('hide');
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
});
