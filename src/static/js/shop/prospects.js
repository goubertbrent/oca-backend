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

var StatusType = {
    TODO : 0,
    APPOINTMENT_MADE : 1,
    CALL_BACK : 2,
    NOT_INTERESTED : 3,
    IRRELEVANT : 4,
    CUSTOMER : 5,
    NOT_ANSWERED : 6,
    NOT_EXISTING : 7,
    CONTACT_LATER : 8,
    NOT_INTERESTED_AFTER_APPOINTMENT : 9,
    INVITED_TO_INTRODUCTION: 10,
    ADDED_BY_DISCOVERY: 11
};
var ShopTaskIcons = {
    1: 'fa-map-marker',
    2: 'fa-phone',
    3: 'fa-question'
};

// Show no reason in prospect info for these statuses
var STATUSES_WITHOUT_REASON = [StatusType.TODO, StatusType.APPOINTMENT_MADE, StatusType.CUSTOMER,
    StatusType.NOT_EXISTING, StatusType.CONTACT_LATER, StatusType.INVITED_TO_INTRODUCTION,
    StatusType.ADDED_BY_DISCOVERY];

// Define the order in which the statuses appear in the filter popup
var ORDERED_STATUSES = [StatusType.CUSTOMER, StatusType.APPOINTMENT_MADE, StatusType.CALL_BACK,
    StatusType.NOT_ANSWERED, StatusType.CONTACT_LATER, StatusType.NOT_INTERESTED_AFTER_APPOINTMENT,
    StatusType.NOT_INTERESTED, StatusType.IRRELEVANT, StatusType.NOT_EXISTING, StatusType.ADDED_BY_DISCOVERY,
    StatusType.INVITED_TO_INTRODUCTION, StatusType.TODO];

var SUBSCRIPTION_TYPES = {
    1: 'Silver',
    2: 'Gold',
    3: 'Platinum'
};

// Check to be sure that ORDERED_STATUSES contains every status
for ( var k in StatusType) {
    if (ORDERED_STATUSES.indexOf(StatusType[k]) == -1) {
        alert('Developer, you forgot to add StatusType.' + k + ' to ORDERED_STATUSES');
    }
}

var MarkerStatusMapping = {};
MarkerStatusMapping[StatusType.TODO] = 'gray-dot';
MarkerStatusMapping[StatusType.APPOINTMENT_MADE] = 'yellow-fa-location-arrow';
MarkerStatusMapping[StatusType.CALL_BACK] = 'yellow-fa-phone';
MarkerStatusMapping[StatusType.NOT_INTERESTED] = 'white-fa-times';
MarkerStatusMapping[StatusType.IRRELEVANT] = 'white-fa-minus';
MarkerStatusMapping[StatusType.CUSTOMER] = 'green-fa-check';
MarkerStatusMapping[StatusType.NOT_ANSWERED] = 'gray';
MarkerStatusMapping[StatusType.NOT_EXISTING] = 'white';
MarkerStatusMapping[StatusType.CONTACT_LATER] = 'gray-fa-ellipsis-h';
MarkerStatusMapping[StatusType.NOT_INTERESTED_AFTER_APPOINTMENT] = 'white-fa-times';
MarkerStatusMapping[StatusType.INVITED_TO_INTRODUCTION] = 'blue-dot';
MarkerStatusMapping[StatusType.ADDED_BY_DISCOVERY] = 'orange-dot';

// https://developers.google.com/places/supported_types
var GOOGLE_PLACE_TYPES = [ 'accounting', 'airport', 'amusement_park', 'aquarium', 'art_gallery', 'atm', 'bakery',
        'bank', 'bar', 'beauty_salon', 'bicycle_store', 'book_store', 'bowling_alley', 'bus_station', 'cafe',
        'campground', 'car_dealer', 'car_rental', 'car_repair', 'car_wash', 'casino', 'cemetery', 'church',
        'city_hall', 'clothing_store', 'convenience_store', 'courthouse', 'dentist', 'department_store', 'doctor',
        'electrician', 'electronics_store', 'embassy', 'establishment', 'finance', 'fire_station', 'florist', 'food',
        'funeral_home', 'furniture_store', 'gas_station', 'general_contractor', 'grocery_or_supermarket', 'gym',
        'hair_care', 'hardware_store', 'health', 'hindu_temple', 'home_goods_store', 'hospital', 'insurance_agency',
        'jewelry_store', 'laundry', 'lawyer', 'library', 'liquor_store', 'local_government_office', 'locksmith',
        'lodging', 'meal_delivery', 'meal_takeaway', 'mosque', 'movie_rental', 'movie_theater', 'moving_company',
        'museum', 'night_club', 'painter', 'park', 'parking', 'pet_store', 'pharmacy', 'physiotherapist',
        'place_of_worship', 'plumber', 'police', 'post_office', 'real_estate_agency', 'restaurant',
        'roofing_contractor', 'rv_park', 'school', 'shoe_store', 'shopping_mall', 'spa', 'stadium', 'storage', 'store',
        'subway_station', 'synagogue', 'taxi_stand', 'train_station', 'travel_agency', 'university', 'veterinary_care',
        'zoo' ];

var COUNTRY_CODES = {
    'Belgium' : 'BE',
    'Netherlands' : 'NL'
};

var currentRegioManagers = {};

var setCurrentRegioManagers = function(regioManagers) {
    currentRegioManagers = {};
    $.each(regioManagers, function(i, regioManager) {
        currentRegioManagers[regioManager.email] = regioManager;
    });
};

var getMarkerIcon = function(prospectStatus) {
    var markerColor = MarkerStatusMapping[prospectStatus];
    if (markerColor) {
        return '/static/images/google-maps-marker-' + markerColor + '.png';
    }
    return undefined;
};

var showProspectComment = function(commentsTBody, comment) {
    if (!commentsTBody) {
        commentsTBody = $('#prospect-info').find('.prospect-comments').find('tbody');
    }

    var tr = $.tmpl(JS_TEMPLATES.prospect_comment, {
        comment : comment
    });
    $('.comment', tr).html(sln.htmlize(comment.text));
    commentsTBody.append(tr);

    var creatorName = currentRegioManagers[comment.creator] ? currentRegioManagers[comment.creator].name
            : comment.creator;
    var dateStr = getDateString(new Date(comment.timestamp * 1000));

    $('a[data-toggle="tooltip"]', tr).tooltip({
        title : dateStr + "\n\n" + creatorName
    });

    tr.click(function() {
        var index = $(this).attr('data-comment-index');
        $('#prospect-info').find('a[data-toggle="tooltip"]').each(function (i, a) {
            var tooltip = $(a);
            tooltip.tooltip(index == tooltip.attr('data-comment-index') ? 'toggle' : 'hide');
        });
    });
};

function showProspectInfo(prospect, hideStatus, callback) {
    if (prospect.app_id) { // existing prospect
        getManagersForApp(prospect.app_id, function () {
            if (callback) {
                callback(_showProspectInfo(prospect, hideStatus));
            } else {
                _showProspectInfo(prospect, hideStatus);
            }
        });
    } else { // New prospect
        if (callback) {
            callback(_showProspectInfo(prospect, hideStatus));
        } else {
            _showProspectInfo(prospect, hideStatus);
        }
    }
}

var _showProspectInfo = function (prospect, hideStatus) {
    if (hideStatus) {
        $('#prospect-set-status').hide();
    } else {
        $('#prospect-set-status').show();
    }
    var modal = $('#prospect-info').modal('show').data('prospect', prospect);

    if (modal.data('editing')) {
        // Hide the stuff that's only visible during editing
        $('.modal-body .edit', modal).hide().siblings().show();
        $('.modal-footer .btn.edit', modal).hide();
        $('.modal-footer .btn', modal).not('.edit').show();

        $('.create', modal).hide();

        modal.data('editing', false).data('creating', false);
    }

    $('.prospect-name', modal).text(prospect.name);
    $('.edit-prospect-name', modal).val(prospect.name);

    $('.prospect-type', modal).text(prospect.types.join(', '));

    $('.prospect-categories', modal).text(prospect.categories.join(', '));

    $('.prospect-phone', modal).text(prospect.phone)
        .attr('href', 'tel:' + (prospect.phone ? prospect.phone.replace('+', '00'): ''));
    $('.edit-prospect-phone', modal).val(prospect.phone);

    $('.prospect-email', modal).text(prospect.email || '');
    $('.edit-prospect-email', modal).val(prospect.email || '');

    $('.prospect-address', modal).text(prospect.address);
    $('.edit-prospect-address', modal).val(prospect.address);

    $('.prospect-website', modal).text(prospect.website || "").attr('href', prospect.website || "#");
    $('.edit-prospect-website', modal).val(prospect.website || "");

    $('.prospect-status', modal).empty();
    if (prospect.status == StatusType.CUSTOMER && prospect.has_customer) {
        // If customer, add a link that opens the customer details
        var customerLink = $('<a></a>').attr('href', '#').text(StatusTypeStrings[prospect.status]).click(function() {
            loadCustomer(prospect.customer_id, function(customer) {
                modal.modal('hide');
                initCustomerForm(customer);
                showCustomerForm(CustomerFormType.OPEN_TAB, showDetails, customer.id);
            });
        });
        $('.prospect-status', modal).html(customerLink);
    } else {
        $('.prospect-status', modal).text(StatusTypeStrings[prospect.status]);
    }

    if (STATUSES_WITHOUT_REASON.indexOf(prospect.status) == -1) {
        $('.prospect-reason', modal).text(prospect.reason || "");
        $('.prospect-reason', modal).parent('div').show();
    } else {
        $('.prospect-reason', modal).parent('div').hide();
    }

    if (prospect.status == StatusType.CALL_BACK || prospect.status == StatusType.APPOINTMENT_MADE) {
        $('.prospect-action-timestamp', modal).text(getDateString(new Date(prospect.action_timestamp * 1000)));
        $('.prospect-action-timestamp', modal).parent('div').show();
    } else {
        $('.prospect-action-timestamp', modal).parent('div').hide();
    }

    if (prospect.assignee) {
        var assignee;
        if (currentRegioManagers[prospect.assignee]) {
            assignee = currentRegioManagers[prospect.assignee].name;
        } else {
            assignee = prospect.assignee;
        }
        $('.prospect-assignee', modal).text(assignee);
        $('.prospect-assignee', modal).parent('div').show();
    } else {
        $('.prospect-assignee', modal).parent('div').hide();
    }

    $('.edit-prospect-comment', modal).val('');
    var commentsTBody = $('.prospect-comments tbody', modal).empty();
    if (prospect.comments.length > 0) {
        $.each(prospect.comments, function(i, comment) {
            showProspectComment(commentsTBody, comment);
        });
        $('.prospect-comments', modal).parent('div').show();
    } else {
        $('.prospect-comments', modal).parent('div').hide();
    }
    if(prospect.lat) {
        var mapsUrl = 'https://www.google.com/maps/?q&layer=c&cbp=';
        mapsUrl += '&cbll=' + prospect.lat + ',' + prospect.lon;
        $('#show-streetview').show().attr('href', mapsUrl);
    }else{
        $('#show-streetview').hide();
    }
    if(prospect.address || prospect.name) {
        var searchUrl = 'https://www.google.com/search?q=' + prospect.name;
        if(prospect.address){
            var address = prospect.address.split(',');
            searchUrl += ' ' + (address[1] ? address[1] : prospect.address);
        }
        $('#google-link').show().attr('href', searchUrl);
    }else{
        $('#google-link').hide();
    }
    var probableSubscription = [];
    if (prospect.subscription) {
        probableSubscription.push(SUBSCRIPTION_TYPES[prospect.subscription]);
    }
    if (prospect.certainty) {
        probableSubscription.push(prospect.certainty + '% certainty');
    }
    if (probableSubscription.length) {
        $('#prospect-subscription').text(probableSubscription.join(', ')).parent().removeClass('hide');
    } else {
        $('#prospect-subscription').text('').parent().addClass('hide');
    }

    var historyContainer = $('#prospect-history-container');
    historyContainer.html('');
    historyContainer.toggle(!prospect.creating);
    $('#prospect-task-history')
        .toggle(!prospect.creating)
        .unbind('click')
        .click(function() {
        $(this).hide();
        historyContainer.html(TMPL_LOADING_SPINNER)
            .css('min-height', '105px');
        sln.call({
            url: '/internal/shop/rest/prospect/task_history',
            data: {
                id: prospect.id
            },
            success: function (data) {
                $.each(data, function (i, task) {
                    task.created = sln.format(new Date(task.creation_time * 1000));
                    task.closed = task.closed_time ? sln.format(new Date(task.closed_time * 1000)) : '';
                    var manager = currentRegioManagers[task.assignee];
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

    return modal;
};

var addReasonToHTML = function(reason) {
    var html = $($('#prospects_reason_tmpl').html());
    $('input', html).attr('value', reason).after(reason);
    $('#prospect_reasons_container').prepend(html);
};

var askReason = function(callback) {
    var modal = $('#ask-reason').modal('show');
    var textarea = $('.modal-body textarea', modal);
    var radios = $('.modal-body input:radio[name=reason]', modal);

    textarea.val('');
    $('input:radio[name=reason][value=other]', modal).prop('checked', true);

    radios.unbind('change').change(function() {
        var reason = $(this).val();
        if (!reason || reason == 'other') {
            $('.modal-body textarea', modal).show();
        } else {
            $('.modal-body textarea', modal).hide();
        }
    }).change();

    $('.submit-button', modal).unbind('click').click(function() {
        var reason = $('input:radio[name=reason]:checked', modal).val();
        if (!reason || reason == 'other') {
            reason = $('.modal-body textarea', modal).val();
            addReasonToHTML(reason);
        }

        if (!reason) {
            showAlert('You must specify a reason');
            return;
        }

        modal.modal('hide');
        callback(reason);
    });
};

var askTime = function (callback, showRegioManagers, prospect, statusType) {
    var modal = $('#ask-time').modal('show');
    var popupTitle = '';
    var cert = $('#certainty');
    var sub = $('#subscription');
    var mail = $('#prospect-contact-email');
    var inviteLang = $('#prospect-invite-language');
    var appointmentTyp = $('#prospect-invite-type');
    var regioManagersDiv = $('#regio_manager', modal);
    var regioManagersSelect = $('select', regioManagersDiv).empty();
    var currentUserAdded = false;
    switch (statusType) {
        case StatusType.APPOINTMENT_MADE:
            popupTitle = 'Select date and time to visit';
            break;
        case StatusType.CALL_BACK:
            popupTitle = 'Select date and time to call back';
            break;
        default:
            popupTitle = 'Select date and time';
    }
    if (popupTitle) {
        modal.find('#header').hide();
        modal.find('#custom-header').show().text(popupTitle);
    } else {
        modal.find('#header').show();
        modal.find('#custom-header').hide();
    }

    $.each(currentRegioManagers, function(regioManagerEmail, regioManager) {
        regioManagersSelect.append($('<option></option>').attr('value', regioManagerEmail).text(regioManager.name));
        if (CURRENT_USER == regioManagerEmail) {
            currentUserAdded = true;
            regioManagersSelect.val(regioManagerEmail);
        }
    });
    if (!currentUserAdded) {
        regioManagersSelect.prepend($('<option></option>').attr('value', CURRENT_USER).text(CURRENT_USER));
    }
    if(prospect.certainty){
        cert.val(prospect.certainty);
    }else{
        cert.val(0);
    }
    if(prospect.subscription){
        sub.val(prospect.subscription);
    }else{
        sub.val(0);
    }

    if (prospect.email) {
        mail.val(prospect.email);
    } else {
        mail.val('');
    }
    if (statusType === StatusType.APPOINTMENT_MADE) {
        var defaultLang = DEFAULT_LANGUAGES[prospect.app_id.split('-')[0].toUpperCase()];
        inviteLang.val(defaultLang);
        $('#prospect-invite-container').show();
    } else {
        $('#prospect-invite-container').hide();
    }

    if (showRegioManagers) {
        regioManagersDiv.show();
        if (prospect && prospect.assignee) {
            regioManagersSelect.val(prospect.assignee);
        }
    } else {
        regioManagersDiv.hide();
    }

    var date;
    var minDate = new Date();
    if (prospect && prospect.action_timestamp) {
        date = new Date(prospect.action_timestamp * 1000);
    } else {
        // Getting next hour
        date = new Date(parseInt(minDate.getTime() / 3600000 + 1) * 3600000);
    }

    $('#datetime', modal).datetimepicker({
        language : 'en_US',
        format : getLocalDateFormat() + ' hh:mm',
        pickSeconds : false,
        startDate : minDate
    });

    var picker = $('#datetime', modal).data('datetimepicker');
    picker.setLocalDate(date);

    var commentsTextArea = $('textarea', modal).val('');

    $('.submit-button', modal).unbind('click').click(function() {
        modal.modal('hide');
        var comment = commentsTextArea.val();
        var regioManager = showRegioManagers ? regioManagersSelect.val() : undefined;
        var timestamp = picker.getLocalDate().getTime() / 1000;
        var certainty = cert.val() ? parseInt(cert.val()): null;
        var subscription = sub.val() ? parseInt(sub.val()): null;
        var email = mail.val();
        var inviteLanguage, appointmentType;
        if (statusType === StatusType.APPOINTMENT_MADE) {
            inviteLanguage = inviteLang.val();
            appointmentType = parseInt(appointmentTyp.val());
        }
        // Removing seconds with parseInt(... / 60) * 60
        callback(parseInt(timestamp / 60) * 60, regioManager, comment, certainty, subscription, email, inviteLanguage,
            appointmentType);
    });
};

var convertToCustomer = function(prospect) {
    var organizationType = OrganizationType.MERCHANT;
    $.each([ 'health', 'veterinary_care' ], function(i, careType) {
        if (prospect.types.indexOf(careType) != -1) {
            organizationType = OrganizationType.CARE;
            return false;
        }
    });

    var address1;
    var city;
    var zipCode;
    var country;

    try {
        var parts = prospect.address.split(', ');
        if (parts.length == 3) {
            address1 = parts[0];
            country = COUNTRY_CODES[parts[2]];

            var cityParts = parts[1].split(' ');
            if (cityParts.length > 1) {
                zipCode = cityParts[0];
                city = cityParts.slice(1, cityParts.length).join(' ');
            } else {
                // only zipCode in address
                zipCode = cityParts[0];
                city = null;
            }
        }
    } catch (err) {
        console.log(err);
        address1 = prospect.address;
        city = zipCode = country = undefined;
    }

    // hide the prospect popup
    $('#prospect-info').modal('hide');
    showCustomerForm(CustomerFormType.NEW).data('prospect', prospect);
    initCustomerForm({
        name : prospect.name,
        address1 : address1,
        city : city,
        zip_code : zipCode,
        country : country,
        organization_type : organizationType
    });
};

var linkProspectToCustomer = function(customerId, prospect, callback) {
    showProcessing('Linking prospect...');
    sln.call({
        url : '/internal/shop/rest/prospect/link_to_customer',
        type : 'post',
        data : {
            data : JSON.stringify({
                customer_id : customerId,
                prospect_id : prospect.id
            })
        },
        success : function(data) {
            hideProcessing();
            if (!data.success) {
                showError(data.errormsg);
                return;
            }
            mergeObject(prospect, data.prospect);
            callback();
        },
        error : function() {
            hideProcessing();
            showError('An unknown error occurred. Check with the administrators.');
        }
    });
};

var setProspectStatus = function (newStatus, reason, actionTimestamp, assignee, comment, certainty, subscription, email,
                                  inviteLanguage, appointmentType) {
    var prospect = $('#prospect-info').data('prospect');

    showProcessing("Processing...");
    sln.call({
        url : '/internal/shop/rest/prospects/set_status',
        type : 'POST',
        data : {
            data : JSON.stringify({
                prospect_id : prospect.id,
                status : newStatus,
                reason : reason,
                action_timestamp : actionTimestamp,
                assignee : assignee,
                comment : comment || null,
                certainty: certainty,
                subscription: subscription,
                email: email,
                invite_language: inviteLanguage,
                appointment_type: appointmentType
            })
        },
        success : function(data) {
            hideProcessing();
            if (!data.success) {
                showError(data.errormsg);
                return;
            }

            mergeObject(prospect, data.prospect);
            showProspectInfo(prospect);

            var marker = $('#prospect-info').data('marker');
            if (marker) {
                var markerIcon = getMarkerIcon(prospect.status);
                marker.setIcon(markerIcon);
            }
            if (data.calendar_error) {
                showError(data.calendar_error);
            } else {
                $('#prospect-info').modal('hide');
            }
        },
        error : function() {
            hideProcessing();
            showError('An unknown error occurred. Check with the administrators.');
        }
    });
};

var startEditingProspect = function() {
    var modal = $('#prospect-info');
    var prospect = modal.data('prospect');

    $('.modal-body .edit', modal).show().siblings().hide();
    $('.modal-footer .btn', modal).not('.edit').hide();
    $('.modal-footer .btn.edit', modal).show();

    // Prospect comments
    $('.modal-body .prospect-comments', modal).parent().show();

    // Prospect types
    $('#prospect-types-modal').find('input[type="checkbox"]').each(function () {
        var $this = $(this);
        $this.prop('checked', prospect.types.indexOf($this.val()) != -1);
    });

    $('#prospect-categories-modal').find('input[type="checkbox"]').each(function () {
        var $this = $(this);
        $this.prop('checked', prospect.categories.indexOf($this.val()) !== -1);
    });

    modal.data('editing', true);
};

var startCreatingProspect = function() {
    showProspectInfo({
        comments : [],
        status : StatusType.TODO,
        categories : [],
        types: [],
        creating: true
    }, false, function (modal) {
        startEditingProspect();
        modal.data('creating', true);
        $('.modal-body .create', modal).show();


        setTimeout(function () {
            $('.edit-prospect-app-id', modal).focus();
        }, 500);
    });

};

$(function() {
    $('#menu_new_prospect').click(function() {
        startCreatingProspect();
    });

    var prospectInfoPopup = $('#prospect-info');

    prospectInfoPopup.find('.status-schedule-appointment').click(function () {
        var prospect = $('#prospect-info').data('prospect');
        askTime(function (timestamp, assignee, comment, certainty, subscription, email, inviteLanguage, appointmentType) {
            setProspectStatus(StatusType.APPOINTMENT_MADE, '',
                timestamp, assignee, comment, certainty, subscription, email, inviteLanguage, appointmentType);
        }, true, prospect, StatusType.APPOINTMENT_MADE);
    });

    prospectInfoPopup.find('.status-call-back').click(function () {
        var prospect = $('#prospect-info').data('prospect');
        askTime(function (timestamp, assignee, comment, certainty, subscription, email) {
            setProspectStatus(StatusType.CALL_BACK,
                'Prospect asked to call back', timestamp, assignee, comment, certainty, subscription, email);
        }, true, prospect, StatusType.CALL_BACK);
    });

    $('#prospect-info .status-not-answering, #prospect-info .status-answering-machine').click(function() {
        var prospect = $('#prospect-info').data('prospect');
        if (prospect.status == StatusType.CALL_BACK) {
            prospectInfoPopup.find('.status-call-back').click();
        } else {
            var reason = $(this).hasClass('status-not-answering') ? 'Did not pick up the phone' : 'Answering machine';
            // Auto-schedule callback
            setProspectStatus(StatusType.NOT_ANSWERED, reason);
        }
    });

    prospectInfoPopup.find('.status-not-interested').click(function () {
        var prospect = $('#prospect-info').data('prospect');
        var status;
        if (prospect.status == StatusType.APPOINTMENT_MADE) {
            status = StatusType.NOT_INTERESTED_AFTER_APPOINTMENT;
        } else {
            status = StatusType.NOT_INTERESTED;
        }
        askReason(function(reason) {
            setProspectStatus(status, reason);
        });
    });

    prospectInfoPopup.find('.status-irrelevant').click(function () {
        askReason(function(reason) {
            setProspectStatus(StatusType.IRRELEVANT, reason);
        });
    });

    prospectInfoPopup.find('.status-contact-later').click(function () {
        setProspectStatus(StatusType.CONTACT_LATER, '');
    });

    prospectInfoPopup.find('.status-not-existing').click(function () {
        setProspectStatus(StatusType.NOT_EXISTING, '');
    });

    prospectInfoPopup.find('.status-new-customer').click(function () {
        var prospect = $('#prospect-info').data('prospect');
        if (prospect.has_customer) {
            setProspectStatus(StatusType.CUSTOMER);
        } else {
            convertToCustomer(prospect);
        }
    });

    prospectInfoPopup.find('.status-already-customer').click(function () {
        var prospect = prospectInfoPopup.data('prospect');
        if (prospect.has_customer) {
            setProspectStatus(StatusType.CUSTOMER);
        } else {
            $('#customer_form').data('prospect', prospect);
            $('#prospect-info').modal('hide');
            showCustomerForm(CustomerFormType.LINK_PROSPECT);
        }
    });

    prospectInfoPopup.find('.edit-btn').click(function () {
        startEditingProspect();
    });

    prospectInfoPopup.find('.save-btn').click(function () {
        var modal = prospectInfoPopup;

        var creating = modal.data('creating');

        var prospect = creating ? {} : modal.data('prospect');

        var data = {
            prospect_id : prospect.id,
            name : $('.edit-prospect-name', modal).val(),
            phone : $('.edit-prospect-phone', modal).val(),
            address : $('.edit-prospect-address', modal).val(),
            email : $('.edit-prospect-email', modal).val() || null,
            website : $('.edit-prospect-website', modal).val() || null,
            comment : $('.edit-prospect-comment', modal).val() || null,
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

        if (!data.categories.length) {
            showError('Category is required');
            return;
        }

        if (creating) {
            data.prospect_id = null;
            data.status = StatusType.TODO;
            data.app_id = $('.edit-prospect-app-id').val();

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
            url : '/internal/shop/rest/prospect/put',
            type : 'post',
            data : {
                data : JSON.stringify(data)
            },
            success : function(data) {
                hideProcessing();
                if (!data.success) {
                    showError(data.errormsg);
                    return;
                }
                mergeObject(prospect, data.prospect);
                showProspectInfo(prospect);
            },
            error : function() {
                hideProcessing();
                showError('An unknown error occurred. Check with the administrators.');
            }
        });
    });

    prospectInfoPopup.find('.cancel-btn').click(function () {
        var modal = $('#prospect-info');
        if (modal.data('creating')) {
            modal.data('creating', false);
            modal.hide();
        } else {
            showProspectInfo(modal.data('prospect'));
        }
    });

    prospectInfoPopup.find('.edit-prospect-type-btn').click(function () {
        $('#prospect-types-modal').modal('show');
    });

    prospectInfoPopup.find('.edit-prospect-categories-btn').click(function () {
        $('#prospect-categories-modal').modal('show');
    });

    // store the modal status
    // these events are also triggered when a child of #prospect-info is being shown/hidden
    prospectInfoPopup.on('show', function (e) {
        if (e.target.id == 'prospect-info')
            $('#prospect-info').data('state', 'showing');
    }).on('shown', function(e) {
        if (e.target.id == 'prospect-info')
            $('#prospect-info').data('state', 'shown');
    }).on('hide', function(e) {
        if (e.target.id == 'prospect-info')
            $('#prospect-info').data('state', 'hiding').data('prospect', null).data('marker', null);
    }).on('hidden', function(e) {
        if (e.target.id == 'prospect-info')
            $('#prospect-info').data('state', 'hidden');
    }).data('state', 'hidden');


    for(var i = 1; i <= 10; i++){
        $('#certainty').append($('<option></option>').attr('value', i * 10).text(i * 10 + '%'));
    }

    $('#prospect-types-modal').on('hide', function() {
        var types = $('#prospect-types-modal input[type="checkbox"]:checked').map(function() {
            return this.value;
        }).get();
        $('#prospect-info, #tab-prospect').find('.prospect-type').text(types.join(', '));
    });

    $('#prospect-categories-modal').on('hide', function () {
        var types = $('#prospect-categories-modal').find('input[type="checkbox"]:checked').map(function () {
            return this.value;
        }).get();
        $('#prospect-info, #tab-prospect').find('.prospect-categories').text(types.join(', '));
    });

    $.each(PROSPECT_REASONS, function(i, reason) {
        addReasonToHTML(reason);
    });

    $('#prospect-types-modal').find('.modal-body').append($.tmpl(JS_TEMPLATES.prospect_types, {
        GOOGLE_PLACE_TYPES : GOOGLE_PLACE_TYPES
    }));

    var channelUpdates = function(data) {
        if (data.type == 'shop.prospect.updated') {
            var currentProspect = prospectInfoPopup.data('prospect');
            if (currentProspect && currentProspect.id == data.prospect.id) {
                mergeObject(currentProspect, data.prospect);
                // Checking modalState to prevent a hiding popup being shown again
                var modalState = $('#prospect-info').data('state');
                if (modalState == 'showing' || modalState == 'shown') {
                    showProspectInfo(currentProspect);
                }
            }
        }
    };

    sln.registerMsgCallback(channelUpdates);
});
