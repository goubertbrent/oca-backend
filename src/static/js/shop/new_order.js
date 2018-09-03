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

var SUBSCRIPTION_MODULES = {
    city: ['OCAM', 'APLS', 'APPL'],
    gold: ['NWSG'],
    platinum: ['NWSP']
};
/**
 * Subscription type from the currently chosen subscription. Can be silver, gold or platinum.
 * @type string
 */
var currentSubscription;
var chargeIntervalElem;
var selectedItems = [];

$(document).ready(function () {
    $('#button_add_order_item').unbind('click').click(function () {
        $('#order_item_error').hide();
        $('#button_delete_order_item').hide();
        $('#order_item_form input, #order_item_form textarea').val('');
        $('#possible_order_item_count').hide();
        $('#order_item_count').show();
        $('#order_item_form').modal('show').attr('mode', 'new');
        $("#order_item_product").val("");
        $('#order_item_price').val('');
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

    $('#button_save_order_item').click(function () {
        var productCode = $('#order_item_form #order_item_product').val();
        var count = parseInt($('#order_item_form #order_item_count').val());
        var comment = $('#order_item_form #order_item_comment').val();
        var mode = $('#order_item_form').attr('mode');
        if (!(productCode && count)) {
            $('#order_item_error span').text('Not all required fields are filled in!');
            $('#order_item_error').show();
            return;
        }
        var product = products[productCode];
        var price = product.can_change_price ? (parseFloat($('#order_item_price').val()) * 100) : product.price;
        addOrderItem(productCode, count, comment, price, mode);
        $('#order_item_form').modal('hide');
    });
    chargeIntervalElem = $('#new_order_charge_interval');
});

function addOrderItem(productCode, count, comment, price, mode) {
    var newOrderItem = {
        product: productCode,
        count: count,
        comment: comment,
        price: price,
    };
    // first check if this item hasn't been added already.
    var hasItem = selectedItems.some(i => i.product === productCode);
    if (mode === 'new' && hasItem) {
        sln.alert('The product ' + productCode + ' has already been added');
        return;
    }
    if (hasItem) {
        selectedItems = sln.updateItem(selectedItems, newOrderItem, 'product');
    } else {
        selectedItems.push(newOrderItem);
    }
    renderOrderItems(selectedItems);
}

function renderOrderItems(selectedItems) {
    getLegalEntity(function (legalEntity) {
        var orderItems = selectedItems.map(item => {
            var product = products[item.product];
            return Object.assign({}, item, {
                price: (item.price / 100),
                total: (item.count * item.price / 100),
                description: product.description
            });
        });
        var total = orderItems.reduce((acc, item) => acc + item.total, 0);
        var vatPercent = legalEntity.getVatPercent();
        var vat = (total * vatPercent / 100);
        var html = $.tmpl(JS_TEMPLATES.new_order_list, {
            orderItems: orderItems,
            legalEntity: legalEntity,
            order: {
                total: total.toFixed(2),
                vatTotal: vat.toFixed(2),
                totalWithVat: (total + vat).toFixed(2),
            }
        });
        $('#order-item-list').html(html);
        html.find('tbody > tr').click(edit_order_item);
    });
}
    var form = $('#customer_form');
    form.find("#button_create_new_order").unbind('click').click(function () {
        if($(this).attr('disabled')){
            return;
        }
        var customer = currentCustomer;
        var contact = parseInt(form.find('#new_order_contact').val());
        if (!selectedItems.length) {
            $('#new_order_error').show().find('span').text('You need to select at least 1 product');
            return;
        }
        if (!(customer && contact)) {
            $('#new_order_error').show().find('span').text('Not all required fields are filled!');
            return;
        }

        $("#new_order_customer_credit_card_error").css("display", "none");
        $("#button_create_new_order").attr('disabled', true);
        var chargeInterval = parseInt(chargeIntervalElem.val());
        sln.call({
            url: '/internal/shop/rest/order/new',
            type: 'POST',
            data: {
                data: JSON.stringify({
                    customer_id: customer.id,
                    contact_id: contact,
                    items: selectedItems,
                    replace: false,
                    charge_interval: chargeInterval,
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
                                        items: selectedItems,
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
                }
                else {
                    selectedItems = [];
                    renderOrderItems(selectedItems);
                    $('#new_order_error').hide();
                    showCreateService();
                }
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
        var productCode = tr.attr('data-product-code');
        var product = products[productCode];
        var order_item = selectedItems.find(p => p.product === productCode);
        $('#order_item_form #order_item_product').val(order_item.product);
        $('#order_item_form #order_item_count').val(order_item.count);
        var priceElem = $('#order_item_form #order_item_price');
        priceElem.val(order_item.price / 100);
        priceElem.prop('disabled', !product.can_change_price);
        $('#order_item_form #order_item_comment').val(order_item.comment);
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
        $('#button_delete_order_item').data('productCode', productCode);
        $('#order_item_form').modal('show').attr('mode', 'edit').data('tr', tr);
    };
    $('#button_delete_order_item').unbind('click').click(function () {
        var removedProductCode = $(this).data('productCode');
        $('#order_item_form').data('tr').detach();
        $('#order_item_form').modal('hide');
        selectedItems = selectedItems.filter(item => item.product !== removedProductCode);
        renderOrderItems(selectedItems);
    });
