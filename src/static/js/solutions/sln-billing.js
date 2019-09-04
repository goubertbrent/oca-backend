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
var handler;
var logoUrl = '/static/images/shop/osa_white_' + LANGUAGE + '_64.jpg';
if (LOGO_LANGUAGES.indexOf(LANGUAGE) === -1) {
    logoUrl = '/static/images/shop/osa_white_en_64.jpg';
}
var manageCreditCardModal;

$(function() {
    modules.billing = {};

    handler = StripeCheckout.configure({
        key: STRIPE_PUBLIC_KEY,
        image: logoUrl,
        token: function (token) {
            sln.showProcessing(CommonTranslations.SAVING_DOT_DOT_DOT);
            var contact = $('#link_credit_card_contact', manageCreditCardModal).find(':selected').data('contact');
            sln.call({
                url: '/common/billing/card/link_stripe',
                type: 'POST',
                data: {
                    data: JSON.stringify({
                        stripe_token: token.id,
                        stripe_token_created: token.created,
                        contact_id: contact ? contact.id : null
                    })
                },
                success: function (message) {
                    sln.hideProcessing();
                    if (!message) {
                        manageCreditCardModal.modal('hide');
                        if (callBackAfterCCLinked) {
                            callBackAfterCCLinked();
                            callBackAfterCCLinked = undefined;
                        }
                        return;
                    }
                    sln.alert(message);
                },
                error: function () {
                    sln.hideProcessing();
                    sln.alert(CommonTranslations.ERROR_OCCURED_CREDIT_CARD_LINKING);
                }
            });
        }
    });

    var signaturePad = null;
    $('#button_sign_order').click(
            function() {
                if (!Modernizr.canvas) {
                    sln.alert(CommonTranslations.BROWSER_NOT_SUPPORT_ORDER_SIGNING, null,
                            CommonTranslations.BROWSER_NOT_FULLY_SUPPORTED);
                    return;
                }
                $('#sign_order_form').modal('show');
                if (signaturePad) {
                    signaturePad.clear();
                } else {
                    var canvas = document.querySelector("#signature_canvas");
                    signaturePad = new SignaturePad(canvas, {
                        penColor : "rgb(0,0,255)",
                        minWidth : 0.8,
                        maxWidth : 0.8,
                        backgroundColor : "rgb(255,255,255)"
                    });

                    // Force load custom font
                    var ctx = canvas.getContext("2d");
                    ctx.font = "1px Great Vibes"; // Dont forget to update the force load when changing the font
                    ctx.fillText('!', 0, 0);
                    signaturePad.clear();
                }
            });

    $('#button_clear_signature').click(function() {
        signaturePad.clear();
    });

    $('#button_write_signature').click(function() {
        sln.input(function(text) {
            var canvas = document.querySelector("#signature_canvas");
            var ctx = canvas.getContext("2d");
            var fontSize = 100;
            var textSize;
            while (true) {
                ctx.font = fontSize + "px Great Vibes"; // Dont forget to update the force load when changing the font
                textSize = ctx.measureText(text);
                if (textSize.width > canvas.width) {
                    fontSize -= 10;
                } else {
                    break;
                }
            }

            ctx.fillText(text, (canvas.width - textSize.width) / 2, canvas.height / 2);
        }, CommonTranslations.SIGN_USING_KEYBOARD, CommonTranslations.ADD);
    });

    $('#button_add_signature').click(function() {
        sln.showProcessing(CommonTranslations.SAVING_DOT_DOT_DOT);
        sln.call({
            url : '/common/billing/order/sign',
            type : 'POST',
            data : {
                data : JSON.stringify({
                    customer_id : $('#button_add_signature').data("customer_id"),
                    order_number : $('#button_add_signature').data("order_number"),
                    signature : signaturePad.toDataURL()
                })
            },
            success : function(data) {
                sln.hideProcessing();
                if (data) {
                    alert(data);
                    return;
                }
                $('#sign_order').modal('hide');
                $('#sign_order_form').modal('hide');
                loadUnsignedOrders();
                loadOrders();
            },
            error : function() {
                sln.hideProcessing();
                sln.alert(CommonTranslations.ERROR_OCCURED_UNKNOWN);
            }
        });
    });

    var loadUnsignedOrders = function() {
        sln.call({
            url : '/common/billing/orders/load_unsigned',
            data : {},
            success : function(data) {
                var orders = data;
                if (orders.length > 0) {
                    $("#billing_unsigned_orders").parents('.accordion-group').show();
                    var html = $.tmpl(templates.billing_settings_unsigned_orders_table, {
                        unsigned_orders : orders,
                        CommonTranslations : CommonTranslations
                    });
                    $("#billing_unsigned_orders tbody").empty().append(html);

                    $('a.sign-order', html).click(
                            function() {
                                var a = $(this);
                                var customer_id = parseInt(a.attr('customer_id'));
                                var order_number = a.attr('order_number');
                                $('#pdf-viewer').attr(
                                        'src',
                                        '/static/pdfdotjs/web/viewer.html?file='
                                                + encodeURIComponent('/common/order/pdf?customer_id=' + customer_id
                                                        + '&order_number=' + order_number + '&download=false'));
                                $('#sign_order').modal('show');
                                $('#button_add_signature').data("customer_id", customer_id).data("order_number",
                                        order_number);
                            });
                } else {
                    $("#billing_unsigned_orders").parents('.accordion-group').hide();
                }
            }
        });
    };

    var loadOrders = function() {
        sln.call({
            url : '/common/billing/orders/load',
            data : {},
            success : function(data) {
                var html = $.tmpl(templates.billing_settings_orders_table, {
                    orders : data,
                    CommonTranslations : CommonTranslations
                });
                $("#billing_orders tbody").html(html);
            }
        });
    };

    var loadInvoices = function() {
        sln.call({
            url : '/common/billing/invoices/load',
            data : {},
            success : function(data) {
                var html = $.tmpl(templates.billing_settings_invoices_table, {
                    invoices : data,
                    CommonTranslations : CommonTranslations
                });

                var allPaid = true;
                $.each(data, function(i, invoice) {
                    if (!invoice.paid) {
                        allPaid = false;
                        return false; // break
                    }
                });

                $('.credit-card-warning').toggle(!allPaid && IS_MOBICAGE_LEGAL_ENTITY);

                $("#billing_invoices tbody").empty().append(html);

                $('a.view-invoice').click(
                        function() {
                            var a = $(this);
                            var customer_id = parseInt(a.attr('customer_id'));
                            var order_number = a.attr('order_number');
                            var charge_id = a.attr('charge_id');
                            var invoice_number = a.attr('invoice_number');

                            var html = $.tmpl(templates.billing_view_invoice, {
                                header : CommonTranslations.INVOICE_VIEW,
                                cancelBtn : CommonTranslations.CLOSE,
                                CommonTranslations : CommonTranslations
                            });

                            var modal = sln.createModal(html);
                            $('#pdf-viewer', modal).attr(
                                    'src',
                                    '/common/invoice/pdf?customer_id=' + customer_id + '&order_number=' + order_number
                                            + '&charge_id=' + charge_id + '&invoice_number=' + invoice_number
                                            + '&download=false');
                        });
            }
        });
    };

    function loadBudget(callback) {
        sln.call({
            url: '/common/billing/budget',
            success: function (budget) {
                callback(budget);
            }
        });
    }
    modules.billing.loadBudget = loadBudget;

    function loadBudgetTransactions() {
        loadBudget(function (budget) {
            sln.call({
                url: '/common/billing/budget/transactions',
                success: function (transactions) {
                    renderBudgetTransactions(budget, transactions);
                }
            });
        });
    }

    function renderBudgetTransactions(budget, transactions) {
        var html = $.tmpl(templates.billing_budget, {
            budget: budget,
            transactions: transactions.map(function (t) {
                return Object.assign({}, t, {
                    timestamp: sln.format(new Date(t.timestamp)),
                    amount: t.amount * CONSTS.BUDGET_RATE
                });
            }),
            T: T,
            LEGAL_ENTITY_CURRENCY: LEGAL_ENTITY_CURRENCY
        });
        $("#billing_budget").html(html);
    }


    function channelUpdates(data){
        if(data.type === 'common.billing.orders.update'){
            loadOrders();
        }
        else if(data.type === 'common.billing.invoices.update'){
            loadInvoices();
            loadBudgetTransactions();
        }
    }

    $("#manage_credit_card").toggle(IS_MOBICAGE_LEGAL_ENTITY).click(manageCreditCard);

    loadUnsignedOrders();
    loadOrders();
    loadInvoices();
    loadBudgetTransactions();

    sln.registerMsgCallback(channelUpdates);
});

function manageCreditCard() {
    var html = $.tmpl(templates.billing_manage_credit_card, {
        header : CommonTranslations.MANAGE_CREDIT_CARD,
        cancelBtn : CommonTranslations.CLOSE,
        CommonTranslations : CommonTranslations
    });

    manageCreditCardModal = sln.createModal(html);

    sln.call({
        url : "/common/billing/card/info",
        type : "GET",
        data : {},
        success : function(data) {
            if (data) {
                $("#credit-card-info-brand", manageCreditCardModal).text(data.brand);
                $("#credit-card-info-exp-month", manageCreditCardModal).text(data.exp_month);
                $("#credit-card-info-exp-year", manageCreditCardModal).text(data.exp_year);
                $("#credit-card-info-last4", manageCreditCardModal).text(data.last4);
                $(".credit-card-info", manageCreditCardModal).show();
            }
            $(".credit-card-info-loading", manageCreditCardModal).hide();

        },
        error : sln.showAjaxError
    });
    sln.call({
        url : '/common/billing/contacts',
        data : {},
        success : function(data) {
            var select = $('#link_credit_card_contact', manageCreditCardModal);
            select.empty();
            $.each(data, function(i, c) {
                select.append($('<option></option>').attr('value', c.id).data('contact', c).text(
                        c.first_name + ' ' + c.last_name));
            });

            if (data && data.length > 0) {
                $(".credit-card-contacts", manageCreditCardModal).show();
            }
        }
    });
    $("#link_credit_card", manageCreditCardModal).click(function() {
        var contact = $('#link_credit_card_contact', manageCreditCardModal).find(':selected').data('contact');
        handler.open({
            name : CommonTranslations.OUR_CITY_APP,
            description : CommonTranslations.OUR_CITY_APP_SUBSCRIPTION,
            currency : 'eur',
            panelLabel : CommonTranslations.SUBSCRIBE,
            email : contact ? contact.email : service_user_email,
            allowRememberMe : false
        });
    });
}
