/*
 * Copyright 2016 Mobicage NV
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
 * @@license_version:1.1@@
 */

var SUBSCRIPTION_MODULES = {
    silver: ['MSUP', 'BEAC', 'ILOS'],
    gold: ['MSUP', 'BEAC', 'KSUP', 'ILOS'],
    platinum: ['MSUP', 'BEAC', 'SETX', 'KSPP', 'ILOS']
};
/**
 * Subscription type from the currently chosen subscription. Can be silver, gold or platinum.
 * @type string
 */
var currentSubscription;

$(document).ready(function () {
    $('#button_add_order_item').unbind('click').click(function () {
        $('#order_item_error').hide();
        $('#button_delete_order_item').hide();
        $('#order_item_form input, #order_item_form textarea').val('');
        $('#possible_order_item_count').hide();
        $('#order_item_count').show();
        $('#order_item_form').modal('show').attr('mode', 'new');
        $("#order_item_product").val("");
    });

    $('#order_item_product').change(function () {
        var select = $(this);
        var productCode = select.val();
        var form = $('#order_item_form');
        if (select.val()) {
            var product = products[productCode];
            form.find('#order_item_count').val(product.default_count);
            form.find('#order_item_comment').val(product.default_comment);
            if (product.possible_counts.length > 0) {
                form.find('#order_item_count').hide();
                var possibleCountSelect = $('#possible_order_item_count');
                possibleCountSelect.empty();
                var count = product.default_count;
                if (productCode === 'XCTY') {
                    if (currentSubscription === 'gold') {
                        count *= 2;
                    } else if (currentSubscription === 'platinum') {
                        count *= 3;
                    }
                }
                $.each(product.possible_counts, function (i, o) {
                    possibleCountSelect.append($('<option></option>').attr('value', o).text(o));
                });
                possibleCountSelect.val(count);
                possibleCountSelect.show();
            } else {
                form.find('#order_item_count').show();
                form.find('#possible_order_item_count').hide();
            }
        } else {
            form.find('#order_item_comment').val('');
        }
    });

    $('#possible_order_item_count').change(function () {
        $('#order_item_count').val($(this).val());
    });

    $('#button_save_order_item').unbind('click').click(function () {
        var product = $('#order_item_form #order_item_product').val();
        var count = parseInt($('#order_item_form #order_item_count').val());
        var comment = $('#order_item_form #order_item_comment').val();
        var mode = $('#order_item_form').attr('mode');
        if (!(product && count)) {
            $('#order_item_error span').text('Not all required fields are filled!');
            $('#order_item_error').show();
            return;
        }
        add_order_item(product, count, comment, mode);
        recalc_totals();

        $('#order_item_form').modal('hide');
    });

});

function getSubscriptionOrderRemainingLength(callback) {
    sln.call({
        url: '/internal/shop/rest/order/subscription_order_length',
        data: {customer_id: currentCustomer.id},
        success: callback
    });
}
    var add_order_item = function (product, count, comment, mode) {
        var order_item = {product: product, count: count, comment: comment};
        // first check if this item hasn't been added already.
        var isDuplicate = false;
        if(mode == 'new') {
            $('#new_order table tbody > tr').each(function () {
                var item = $(this).data('order_item');
                if (item.product == product && product != 'XCTY') {
                    var err = $('#duplicate_error');
                    err.find('span').text('The product ' + product + ' has already been added');
                    err.slideDown(700).delay(5000).slideUp(700);
                    isDuplicate = true;
                }
            });
        }
        if (!isDuplicate) {
            getLegalEntity(function (legalEntity) {
                var tr = $('#order_item_template > table > tbody > tr').clone();
                $('td.product_code', tr).text(product);
                $('span.description', tr).text(products[product].description);
                $('span.comment', tr).text(comment);
                $('td.price', tr).html(legalEntity.currency + ' ' + (products[product].price / 100).toFixed(2));
                $('td.count', tr).text(count);
                $('td.total', tr).html(legalEntity.currency + ' ' + (count * products[product].price / 100).toFixed(2));
                tr.data('order_item', order_item);
                tr.unbind('click').click(edit_order_item);
                $('#new_order table tbody').append(tr);
                if (mode != 'new') {
                    $('#order_item_form').data('tr').detach();
                }
            });
        }
    };

var recalc_totals = function () {
        var total = 0;
        $('#new_order').find('table tbody > tr').each(function () {
            var tr = $(this);
            var item = tr.data('order_item');
            total += products[item.product].price * item.count / 100;
        });
        if (currentCustomer.id) {
            getLegalEntity(function (legalEntity) {
                var vatPercent = legalEntity.getVatPercent();
                $('#new_order_vat_percentage').text(vatPercent);
                var vat = total * vatPercent / 100;
                $('#new_order_vat').html(legalEntity.currency + ' ' + vat.toFixed(2));
                $('#new_order_total_excl_vat').html(legalEntity.currency + ' ' + total.toFixed(2));
                $('#new_order_total_incl_vat').html(legalEntity.currency + ' ' + (total + vat).toFixed(2) + '</strong>');
            });
        }
    };

    var form = $('#customer_form');
    form.find("#button_create_new_order").unbind('click').click(function () {
        if($(this).attr('disabled')){
            return;
        }
        var customer = currentCustomer;
        var contact = parseInt(form.find('#new_order_contact').val());
        var items = [];
        $('#new_order').find('table tbody > tr').each(function () {
            var tr = $(this);
            var item = tr.data('order_item');
            items.push(item);
        });
        if (!items.length) {
            $('#new_order_error').show().find('span').text('You need to select at least 1 product');
            return;
        }
        if (!(customer && contact)) {
            $('#new_order_error').show().find('span').text('Not all required fields are filled!');
            return;
        }


        $("#new_order_customer_credit_card_error").css("display", "none");
        $("#button_create_new_order").attr('disabled', true);
        sln.call({
            url: '/internal/shop/rest/order/new',
            type: 'POST',
            data: {
                data: JSON.stringify({
                    customer_id: customer.id,
                    contact_id: contact,
                    items: items
                })
            },
            success: function (data) {
                if (!data.success) {
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
                                        items: items,
                                        replace: true
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
                                }, complete: function(){
                                    // Force the service and orders tabs to be reloaded
                                    currentCustomer.ordersLoaded = false;
                                    currentCustomer.default_modules = false;
                                    loadCustomer(currentCustomer.id, function(customer){
                                        for (var k in customer){
                                            if(customer.hasOwnProperty(k)){
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
            },complete: function(){
                currentCustomer.ordersLoaded = false;
                currentCustomer.default_modules = false;
                $("#button_create_new_order").attr('disabled', false);
            }
        });
    });
    var edit_order_item = function () {
        var tr = $(this);
        $('#button_delete_order_item').show();
        $('#order_item_error').hide();
        $('#order_item_form input, #order_item_form textarea').val('');
        var order_item = tr.data('order_item');
        $('#order_item_form #order_item_product').val(order_item.product);
        $('#order_item_form #order_item_count').val(order_item.count);
        $('#order_item_form #order_item_comment').val(order_item.comment);
        var product = products[order_item.product];
        if (product.possible_counts.length > 0) {
            $('#order_item_form #order_item_count').hide();
            var select = $('#possible_order_item_count');
            select.empty();
            $.each(product.possible_counts, function (i, o) {
                select.append($('<option></option>').attr('value', o).text(o));
            });
            select.val(order_item.count);
            select.show();
        } else {
            $('#order_item_form #order_item_count').show();
            $('#order_item_form #possible_order_item_count').hide();
        }
        $('#order_item_form').modal('show').attr('mode', 'edit').data('tr', tr);
    };
    $('#button_delete_order_item').unbind('click').click(function () {
        $('#order_item_form').data('tr').detach();
        recalc_totals();
        $('#order_item_form').modal('hide');
    });
