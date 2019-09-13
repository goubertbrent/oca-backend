/*
 * Copyright 2019 Green Valley Belgium NV
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
 * @@license_version:1.5@@
 */

$(function() {
    'use strict';

    loadCustomerCharges();
    var cursor, isLoading = false, hasMore = true;
    var loadedCharges = [];

    function showLoadinSpinner() {
        $('#loading_indicator').html(TMPL_LOADING_SPINNER);
        isLoading = true;
    }

    function hideLoadingSpinner() {
        $('#loading_indicator').empty();
        isLoading = false;
    }

    function loadCustomerCharges() {
        showLoadinSpinner();
        sln.call({
            url: '/internal/shop/customer/charges',
            type: 'get',
            data: {
                paid: window.location.href.endsWith('paid'),
                cursor: cursor
            },
            success: function(data) {
                if(cursor === data.cursor) {
                    hasMore = false;
                }
                cursor = data.cursor;
                renderCustomerCharges(data);
                hideLoadingSpinner();
            },
            error: function() {
                hideLoadingSpinner();
                sln.showAjaxError();
            }
        });
    }

    function renderCustomerCharges(data) {
        var admin, payment_admin, is_reseller;
        var chargesTable = $('#customer_charges > tbody');

        admin = data.is_admin;
        payment_admin = data.is_payment_admin;
        is_reseller = data.is_reseller;

        $.each(data.customer_charges, function(i, customer_charge) {
            var charge = customer_charge.charge;
            var cacheKey = customer_charge.customer.id + "." + charge.id;
            if(loadedCharges.indexOf(cacheKey) === -1) {
                var chargeRow = $.tmpl(JS_TEMPLATES.charge, {
                    customer: customer_charge.customer,
                    charge: charge,
                    admin: admin,
                    payment_admin: payment_admin,
                    is_reseller: is_reseller
                });
                chargesTable.append(chargeRow);
                loadedCharges.push(cacheKey);
            }
        });

        validateLoadMoreCharges();
    }

    function validateLoadMoreCharges() {
        var lastChargeRow = $('.charge-row').last();
        if(sln.isOnScreen(lastChargeRow) && hasMore && !isLoading) {
            loadCustomerCharges();
        }
    }

    $(window).scroll(validateLoadMoreCharges);

    getLegalEntity(function (legalEntity) {
        if (legalEntity.is_mobicage) {
            $(document).on('click', 'a.start-on-site-payment', function () {
                var a = $(this);
                startOnSitePayment(parseInt(a.attr('customer_id')), a.attr('customer_name'), a.attr('customer_user_email'),
                        a.attr('order_number'), parseInt(a.attr('charge_id')), parseInt(a.attr('charge_amount')),
                        a.attr('charge_reference'), true);
            });
        }
    });

    $(document).on('click', 'a.send-payment-info', function() {
        var a = $(this);
        var customer_id = parseInt(a.attr('customer_id'));
        var order_number = a.attr('order_number');
        var charge_id = parseInt(a.attr('charge_id'));
        showProcessing("Sending payment info ...");
        sln.call({
            url: '/internal/shop/rest/charge/send_payment_info',
            type: 'POST',
            data: {
                data: JSON.stringify({
                    customer_id: customer_id,
                    order_number: order_number,
                    charge_id: charge_id
                })
            },
            success: function (data) {
                hideProcessing();
                if (data)
                    alert(data);
                else
                    window.location.reload();
            },
            error: function () {
                hideProcessing();
                alert('An unknown error occurred. Check with the administrators.');
            }
        });
    });

    $(document).on('click', 'a.set-po-number', function() {
        var a = $(this);
        var customerId = parseInt(a.attr('customer_id'));
        var orderNumber = a.attr('order_number');
        var chargeId = parseInt(a.attr('charge_id'));
        var submit = function(val) {
            showProcessing("Saving PO number...");
            sln.call({
                url: '/internal/shop/rest/charge/set_po_number',
                type: 'POST',
                data: {
                    data: JSON.stringify({
                        customer_id: customerId,
                        order_number: orderNumber,
                        charge_id: chargeId,
                        customer_po_number: val
                    })
                },
                success: function (data) {
                    hideProcessing();
                    if (!data.success) {
                        alert(data.errormsg);
                        return;
                    }
                    a.attr('customer_po_number', val);
                },
                error: function () {
                    hideProcessing();
                    alert('An unknown error occurred. Check with the administrators.');
                }
            });
            return true;
        };
        askInput(submit, 'Set a PO number', null, null, a.attr('customer_po_number'));
    });

    $(document).on('click', 'a.payment-in-advance', function () {
        var a = $(this);
        var customer_id = parseInt(a.attr('customer_id'));
        console.log("customer_id: " + customer_id);
        var order_number = a.attr('order_number');
        var charge_id = parseInt(a.attr('charge_id'));
        var charge_amount = parseInt(a.attr('charge_amount'));
        var charge_amount_paid_in_advance = parseInt(a.attr('charge_amount_paid_in_advance'));
        sln.input(function(value) {
            sln.call({
                showProcessing: true,
                url: '/internal/shop/rest/charge/set_advance_payment',
                type: 'POST',
                data: {
                    data: JSON.stringify({
                        customer_id: customer_id,
                        order_number: order_number,
                        charge_id: charge_id,
                        amount: parseInt(Math.round(100 * value))
                    })
                },
                success: function (data) {
                    if (!data.success)
                        alert(data.errormsg);
                    else
                        window.location.reload();
                },
                error: function () {
                    alert('An unknown error occurred. Check with the administrators.');
                }
            });
        }, null, null, null, (charge_amount_paid_in_advance || Math.round(charge_amount / 2.0)) / 100.0, 'number');
    });

    $(document).on('click', 'a.manual-payment', function() {
        var a = $(this);
        var customer_id = parseInt(a.attr('customer_id'));
        console.log("customer_id: " + customer_id);
        var order_number = a.attr('order_number');
        var charge_id = parseInt(a.attr('charge_id'));
        var paid = a.attr('paid') == 'true';
        var customer_name = a.attr('customer_name');
        var structured_info = a.attr('structured_info');
        showConfirmation("Please confirm manual payment.<br>Customer: " + customer_name + "<br>Structured info: " + structured_info, function() {
            showProcessing("Sending invoice ...");
            sln.call({
                url: '/internal/shop/rest/charge/execute_manual',
                type: 'POST',
                data: {
                    data: JSON.stringify({
                        customer_id: customer_id,
                        order_number: order_number,
                        charge_id: charge_id,
                        paid: paid
                    })
                },
                success: function (data) {
                    hideProcessing();
                    if (data)
                        alert(data);
                    else
                        window.location.reload();
                },
                error: function () {
                    hideProcessing();
                    alert('An unknown error occurred. Check with the administrators.');
                }
            });
        });
    });

    $(document).on('click', 'a.cancel-charge', function () {
        var $this = $(this);
        var chargeId = parseInt($this.attr('charge_id'));
        var orderNumber = $this.attr('order_number');
        var customerId = parseInt($this.attr('customer_id'));
        var message = 'Are you sure you want to cancel charge from order ' + orderNumber + '?';
        sln.confirm(message, doCancelCharge);
        function doCancelCharge () {
            sln.call({
                url: '/internal/shop/rest/charge/cancel',
                method: 'post',
                data: {
                    charge_id: chargeId,
                    customer_id: customerId,
                    order_number: orderNumber
                },
                success: function (data) {
                    if (data.success === true) {
                        $('#charge-' + chargeId).remove();
                    } else {
                        sln.alert(data.errormsg);
                    }
                }
            });
        }
    });

});
