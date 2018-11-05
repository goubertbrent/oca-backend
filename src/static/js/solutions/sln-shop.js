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

var cart = [];

ROUTES.shop = shopRouter;

function shopRouter(urlHash) {
    $('#shoplink').click();
    var page = urlHash[1];
    // todo should be able to enable cache
    Requests.getOrderItems({cached: false}).then(function (data) {
        cart = data;
        switch (page) {
            case 'product':
                renderItem(urlHash[2]);
                break;
            case 'cart':
                renderCart(urlHash[2]);
                break;
            case 'payment-methods':
                renderPaymentMethods();
                break;
            case 'checkout':
                if (urlHash.length < 3) {
                    window.location.hash = '#/cart';
                    return;
                }
                renderCart(true, urlHash[2]);
                break;
            default:
                renderItem('');
        }
    });
}

function renderItem(productCode){
    Requests.getStoreProducts().then(function (products) {
        var foundProducts = products.filter(function (p) {
            return p.code === productCode;
        });
        if (!foundProducts.length && products.length) {
            window.location.hash = '/shop/product/' + products[0].code;
        } else {
            renderProduct(products, foundProducts[0]);
        }
    });
}

function renderProduct(products, product, error, success, loading) {
    if (product.code === 'BDGT') {
        Requests.getBudget().then(render);
    }else {
        render(null);
    }

    function render(budget) {
        var html = $.tmpl(templates['shop/product'], {
            product: product,
            error: error,
            success: success,
            loading: loading,
            t: CommonTranslations,
            LEGAL_ENTITY_CURRENCY: LEGAL_ENTITY_CURRENCY,
            budget: budget,
            products: products,
        });
        $('#store-current-page').html(html);
        $('#add-to-cart').click(function () {
            var count = parseInt($('#product-amount').val());
            var item = {code: product.code, count: count, loading: true};

            if (item.loading) {
                renderProduct(products, product, null, false, true);
            }
            var options = {
                method: 'POST',
                url: '/common/store/order/item/add',
                data: {
                    data: JSON.stringify({
                        item: item
                    })
                },
                success: function (data) {
                    // check if the save was successful.
                    if (data.success) {
                        // Check if there is a cart item with the same product code.
                        // If so, just add the count to it instead of creating a new cart item.
                        var newItem = data.order_item;
                        var hasItem = false;
                        for (var i = 0; i < cart.length; i++) {
                            if (cart[i].product === newItem.product) {
                                cart[i].count = newItem.count;
                                hasItem = true;
                            }
                        }
                        if (!hasItem) {
                            cart.push(newItem);
                        }
                    }
                    renderProduct(products, product, data.errormsg, true, false);
                },
                error: function () {
                    renderProduct(products, product, CommonTranslations.ERROR_OCCURED_UNKNOWN, false, false);
                }
            };
            sln.call(options);
        });
        renderGlobals();
    }
}

function renderGlobals(){
    var cartCount = '';
    if (cart.length) {
        cartCount = '(' + cart.length + ')';
    }
    $('.cart-item-count').text(cartCount);
}

function calculateTotals(cart, products) {
    var totalExclVat = 0, vat = 0, total = 0;

    for (var i = 0; i < cart.length; i++) {
        var product = cart[i];
        product.description = products.filter(function (p) {
            return p.code === product.product;
        })[0].description;
        var tot = product.price * product.count/100;
        var vatTemp = tot * VAT_PCT / 100;
        totalExclVat += tot;
        vat += vatTemp;
        total += tot + vatTemp;
    }
    return {totalExclVat: totalExclVat, vat: vat, total: total};
}

function getMethodTranslation(method) {
    var methods = {
        'payconiq': 'Payconiq',
        'creditcard': T('credit_card'),
    };
    return methods[method];
}

function renderCart(checkout, paymentMethod) {
    Requests.getStoreProducts().then(function (products) {
        var totals = calculateTotals(cart, products);
    var html = $.tmpl(templates['shop/shopping_cart'], {
        items: cart,
        vatPct: VAT_PCT,
        totalExclVat: totals.totalExclVat.toFixed(2),
        vat: totals.vat.toFixed(2),
        total: totals.total.toFixed(2),
        checkout: checkout,
        t: CommonTranslations,
        cartTitle: T(checkout ? 'overview_order' : 'cart'),
        LEGAL_ENTITY_CURRENCY: LEGAL_ENTITY_CURRENCY,
        paymentMethodText: paymentMethod ? T('payment_will_be_completed_using_x', {method: getMethodTranslation(paymentMethod)}) : null,
        payText: paymentMethod ? T('pay_with_x', {method: getMethodTranslation(paymentMethod)}) : null,
    });
    $('#store-current-page').html(html);
    $('button[data-item-id]').click(function(){
        var id = $(this).attr('data-item-id');
        var orderItem = cart.filter(function(cartitem){
            return cartitem.id === parseInt(id);
        })[0];
        if(orderItem){
            removeItemFromCart(orderItem, renderCart);
        }
    });
        renderGlobals();
        if (paymentMethod) {
            $('#shopping_cart_pay_button').click(function () {
                var button = $(this);
                var resultPromise;
                if (paymentMethod === 'payconiq') {
                    resultPromise = payWithPayconiq();
            } else {
                    resultPromise = payWithCreditcard();
            }
                button.prop('disabled', true)
                resultPromise.then(function () {
                    sln.alert(T('thank_you_for_your_order'), onClose, T('order_complete'));

                    function onClose() {
                        // Clear the shopping cart and redirect to the shop homepage
                        cart = [];
                        window.location.hash = '/shop/';
                    }
                }).catch(function (err) {
                    sln.alert(err, null, T('Error'));
                }).finally(function () {
                    button.prop('disabled', false);
            });
            });
        }
    });
}

function payWithCreditcard() {
    return new Promise(function (resolve, reject) {
        sln.showProcessing();
        var options = {
            method: 'post',
            url: '/common/store/order/pay',
            success: function (data) {
                // check if the save was successful.
                sln.hideProcessing();
                if (data.success) {
                    resolve();
                } else {
                    reject(data.errormsg);
                }
            },
            error: function () {
                reject(T('order_failed_contact_cs'));
                sln.hideProcessing();
            },
        };
        sln.call(options);
    });
}

function payWithPayconiq() {
    return new Promise(function (resolve, reject) {
        Requests.getPayconiqPaymentInfo().then(function (info) {
            var config = {widgetType: 'popup', transactionData: info};
            console.log('Opening payconiq widget', config);
            payconiq(config)
                .on('success', onSuccess)
                .on('error', onError)
                .on('failed', onFailed)
                .load();

            function onSuccess() {
                resolve();
            }

            function onError(error) {
                console.error(error.message, error);
                reject(error.message);
            }

            function onFailed(error) {
                console.error(error.message, error);
                reject(error.message);
            }
        });
    });

}


function renderPaymentMethods() {
    Requests.getStoreProducts().then(function (products) {
        var totals = calculateTotals(cart, products);
        if (totals.total === 0) {
            window.location.hash = '/shop';
            return;
        }
        var args = {
            loading: true,
            loadingSpinner: TMPL_LOADING_SPINNER,
            paymentMethods: [],
            T: T,
            amountMessage: T('choose_a_payment_method_for_payment_of_x', {amount: LEGAL_ENTITY_CURRENCY + totals.total}),
        };
        var html = $.tmpl(templates['shop/choose_payment_method'], args);
        var container = $('#store-current-page');
        container.html(html);
        Requests.getPaymentMethods().then(function (paymentMethods) {
            args.loading = false;
            args.paymentMethods = paymentMethods;
            html = $.tmpl(templates['shop/choose_payment_method'], args);
            container.html(html);
            $('#pay-creditcard').click(function () {
                Requests.getCreditcardInfo().then(function (creditCardInfo) {
                    if (creditCardInfo) {
                        window.location.hash = '#/shop/checkout/creditcard';
                    } else {
                        CreditcardManager.addCreditcard().then(function () {
                            window.location.hash = '#/shop/checkout/creditcard';
                        });
                    }
                });
            });
        });
        // Preload credit card info in cache so it goes faster when clicking it
        Requests.getCreditcardInfo();
    });
}

function removeItemFromCart(item, renderFx){
    var options = {
        method: 'post',
        url: '/common/store/order/item/delete',
        data: {
            data: JSON.stringify({
                item_id: item.id
            })
        },
        success: function (data) {
            // check if the save was successful.
            if (data.success === true) {
                cart.splice(cart.indexOf(item), 1);
                renderFx();
            } else {
                renderFx({error: data.errormsg});
            }
        },
        error: function () {
            // show generic error msg
            renderFx({error: CommonTranslations.ERROR_OCCURED_UNKNOWN});
        }
    };
    sln.call(options);
}
