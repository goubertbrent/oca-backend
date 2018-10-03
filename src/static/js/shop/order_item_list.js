'use strict';

class OrderItemList {

    constructor(containerElement, legalEntity, products, organizationType) {
        this.containerElement = containerElement;
        this.legalEntity = legalEntity;
        this.products = products;
        this.organizationType = organizationType;
        this.products.sort(this._compareProduct);
        this.productsMapping = products.reduce((acc, product) => {
            acc[product.code] = product;
            return acc;
        }, {});
        this.selectedItems = [];
    }

    addOrderItem(productCode, count, comment, price, mode) {
        var newOrderItem = {
            product: productCode,
            count: count,
            comment: comment,
            price: price,
        };
        // first check if this item hasn't been added already.
        var hasItem = this.selectedItems.some(i => i.product === productCode);
        if (mode === 'new' && hasItem) {
            sln.alert('The product ' + productCode + ' has already been added');
            return;
        }
        if (hasItem) {
            this.selectedItems = sln.updateItem(this.selectedItems, newOrderItem, 'product');
        } else {
            this.selectedItems.push(newOrderItem);
        }
    }

    render() {
        var orderItems = this.selectedItems.map(item => {
            var product = this.productsMapping[item.product];
            return Object.assign({}, item, {
                price: (item.price / 100),
                total: (item.count * item.price / 100),
                description: product.description
            });
        });
        var total = orderItems.reduce((acc, item) => acc + item.total, 0);
        var vatPercent = this.legalEntity.getVatPercent();
        var vat = (total * vatPercent / 100);
        var html = $.tmpl(JS_TEMPLATES['customer_popup/new_order_list'], {
            orderItems: orderItems,
            legalEntity: this.legalEntity,
            order: {
                total: total.toFixed(2),
                vatTotal: vat.toFixed(2),
                totalWithVat: (total + vat).toFixed(2),
            }
        });
        this.containerElement.html(html);
        html.find('tbody > tr').click(event => this.showEditItemDialog(event.currentTarget));
    }

    showEditItemDialog(element) {
        var tr = $(element);
        this._addPopupEvents();
        $('#button_delete_order_item').show();
        $('#order_item_error').hide();
        this.prepareItemDialog();
        var productCode = tr.attr('data-product-code');
        var product = this.productsMapping[productCode];
        var countElem = $('#order_item_count');
        var priceElem = $('#order_item_price');
        var orderItem = this.selectedItems.find(p => p.product === productCode);
        if (orderItem) {
            priceElem.prop('disabled', !product.can_change_price);
            countElem.val(orderItem.count);
            priceElem.val(orderItem.price / 100);
            $('#order_item_comment').val(orderItem.comment);
            $('#order_item_product').val(orderItem.product);
        }
        if (product.possible_counts.length > 0) {
            countElem.hide();
            var select = $('#possible_order_item_count');
            select.empty();
            $.each(product.possible_counts, function (i, o) {
                select.append($('<option></option>').attr('value', o).text(o));
            });
            if (orderItem) {
                select.val(orderItem.count);
            }
            select.show();
        } else {
            countElem.show();
            $('#possible_order_item_count').hide();
        }
        $('#order_item_form').data('productCode', productCode);
        $('#order_item_form').modal('show').attr('mode', 'edit');
    }

    prepareItemDialog() {
        $('#form_order_item').get(0).reset();
    }

    showAddItemDialog() {
        $('#order_item_error').hide();
        $('#button_delete_order_item').hide();
        $('#order_item_form').modal('show').attr('mode', 'new');
        this.prepareItemDialog();
        this._addPopupEvents();
    }

    _addPopupEvents() {
        this._setProducts();
        var productSelect = $('#order_item_product');
        productSelect.unbind('change').change(() => {
            var productCode = productSelect.val();
            var form = $('#order_item_form');
            if (productCode) {
                var product = this.productsMapping[productCode];
                form.find('#order_item_price').val((product.price / 100)).prop('disabled', !product.can_change_price);
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

        $('#button_save_order_item').unbind('click').click(() => {
            var oldProductCode = $('#order_item_form').data('productCode');
            var productCode = $('#order_item_form #order_item_product').val();
            var count = parseInt($('#possible_order_item_count').val());
            var comment = $('#order_item_form #order_item_comment').val();
            var mode = $('#order_item_form').attr('mode');
            if (!(productCode && count)) {
                $('#order_item_error span').text('Not all required fields are filled in!');
                $('#order_item_error').show();
                return;
            }
            var product = this.productsMapping[productCode];
            if (product.possible_counts.length === 0) {
                count = parseInt($('#order_item_form #order_item_count').val());
            }
            var price = product.can_change_price ? (parseFloat($('#order_item_price').val()) * 100) : product.price;
            if (oldProductCode !== productCode) {
                this.selectedItems = this.selectedItems.filter(item => item.product !== oldProductCode);
            }
            this.addOrderItem(productCode, count, comment, price, mode);
            this.render();
            $('#order_item_form').modal('hide');
        });
        $('#button_delete_order_item').unbind('click').click(() => {
            var removedProductCode = $('#order_item_form').data('productCode');
            $('#order_item_form').modal('hide');
            this.selectedItems = this.selectedItems.filter(item => item.product !== removedProductCode);
            this.render();
        });
    }

    _compareProduct(a, b) {
        return a.description.localeCompare(b.description, undefined, {sensitivity: 'base'});
    }

    _setProducts() {
        var select = $("#order_item_product").empty();
        select.append($('<option></option>').attr('value', '').text("Select product"));
        for (const p of this.products) {
            if (p.organization_types.length === 0 || p.organization_types.includes(this.organizationType)) {
                const elem = $('<option></option>')
                    .attr('value', p.code)
                    .text(p.description + ' (' + this.legalEntity.currency + ' ' + p.price_in_euro + ')');
                select.append(elem);
            }
        }
    }
}
