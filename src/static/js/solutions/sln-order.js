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

$(function () {
    var STATUS_RECEIVED = 1;
    var STATUS_COMPLETED = 2;

    var solutionInboxMessageOrders = {};
    var solutionInboxMessageOrderRequests = {};
    var ordersDict = {};
    var orders = [];
    var showAllOrders = false;

    var pauseEndTimeout;

    var channelUpdates = function (data) {
        switch (data.type) {
            case 'solutions.common.orders.update':
                Requests.getOrderSettings().then(function (orderSettings) {
                    loadOrders(orderSettings);
                });
                break;
            case 'solutions.common.orders.deleted':
                fadeOutMessageAndUpdateBadge(data.order_key);
                break;
            case 'solutions.common.order.settings.timeframe.update':
                loadorderTimeframes();
                break;
        }
    };

    var settingsSection = $('#section_settings_order');
    settingsSection.find('input[type=radio]').change(putOrderSettings);
    settingsSection.find('input[type=checkbox]').change(putOrderSettings);

    function updateShowHideOrders() {
        $("#ordersShowTodo").toggleClass('btn-success', !showAllOrders)
            .html(showAllOrders ? '&nbsp;' : CommonTranslations.TODO);
        $("#ordersShowAll").toggleClass('btn-success', showAllOrders)
            .html(showAllOrders ? CommonTranslations.ALL : '&nbsp;');
    }

    function renderOrderSettings(data) {
        var headerMenuElement = $('#topmenu').find('li[menu=menu]');
        if (data.order_type === CONSTS.ORDER_TYPE_ADVANCED) {
            headerMenuElement.removeClass('hide');
        } else if (MODULES.indexOf('menu') === -1) {
            headerMenuElement.addClass('hide');
        }
        if (modules.menu) {
            Requests.getMenu().then(modules.menu.renderMenu);
        }
        $("#order_settings_text1").val(data.text_1);
        $("#order_ready_default_message").val(data.order_ready_message);
        settingsSection.find('input[type=radio][value=' + data.order_type + ']').prop('checked', true);
        $('#order_leaptime').val(data.leap_time);
        $('#order_leaptime_type').val(data.leap_time_type);
        $('#pause-orders-enabled').prop('checked', data.pause_settings.enabled);
        if (data.order_type === CONSTS.ORDER_TYPE_SIMPLE) {
            $('#order_timeframes_container').slideUp();
            $('#order-limitations').slideUp();
            $('#intro_text_container').slideDown();

        } else if (data.order_type === CONSTS.ORDER_TYPE_ADVANCED) {
            loadorderTimeframes();
            $('#order_timeframes_container').slideDown();
            $('#order-limitations').slideDown();
            $('#intro_text_container').slideUp();
        }
        $('#mobile_payments_available').toggle(data.order_type === CONSTS.ORDER_TYPE_ADVANCED);
        $('#mobile_payments_unavailable').toggle(data.order_type !== CONSTS.ORDER_TYPE_ADVANCED);
        if (data.manual_confirmation) {
            $('input[name=auto_or_manual_confirmation][value=manual]').prop('checked', true);
        } else {
            $('input[name=auto_or_manual_confirmation][value=automatic]').prop('checked', true);
        }
        $('#pause-settings-message').val(data.pause_settings.message);
        $('#disable-order-outside-hours').prop('checked', data.disable_order_outside_hours);
        $('#outside-hours-message').val(data.outside_hours_message);
        renderOrders(data);
        if (data.pause_settings.paused_until) {
            if (!pauseEndTimeout) {
                var timeout = new Date(data.pause_settings.paused_until).getTime() - new Date().getTime();
                pauseEndTimeout = setTimeout(function () {
                    renderOrderSettings(data);
                }, timeout);
            }
        }
    }

    function putOrderSettings(pausedUntil, pausedMessage) {
        Requests.getOrderSettings().then(function (orderSettings) {
            var leapTime = parseInt($('#order_leaptime').val());
            var confirmation = $('input[name=auto_or_manual_confirmation]:checked').val();
            if (isNaN(leapTime)) {
                leapTime = 60;
            }
            var leapTimeType = parseInt($('#order_leaptime_type').val());
            var paused = (typeof pausedUntil === 'string' || pausedUntil === null) ? pausedUntil : orderSettings.pause_settings.paused_until;
            var data = {
                text_1: $("#order_settings_text1").val(),
                order_type: parseInt($('#section_settings_order').find('input[name=setting_advanced_order_fields]:checked').val()),
                leap_time: leapTime,
                leap_time_type: leapTimeType,
                order_ready_message: $('#order_ready_default_message').val().trim() || orderSettings.order_ready_message,
                manual_confirmation: confirmation === 'manual',
                pause_settings: {
                    enabled: $('#pause-orders-enabled').prop('checked'),
                    paused_until: paused,
                    message: pausedMessage || $('#pause-settings-message').val(),
                },
                disable_order_outside_hours: $('#disable-order-outside-hours').prop('checked'),
                outside_hours_message: $('#outside-hours-message').val().trim(),
            };
            pauseEndTimeout = null;
            Requests.saveOrderSettings(data).then(renderOrderSettings);
        });
    }

    var getActionsForOrder = function (order, orderSettings) {
        var toolbar = $('<div class="btn-toolbar"></div>');
        var group = $('<div class="btn-group"></div>');

        if (order.status !== STATUS_COMPLETED && orderSettings.manual_confirmation) {
            var btnConfirm = $('<button action="confirm" class="btn btn-large btn-primary"><i class="fa fa-reply"><i></button>');
            btnConfirm.click(function (event) {
                event.stopPropagation();
                sendMessage(order, CommonTranslations.order_confirmed);
            });
            group.append(btnConfirm);
        }
        if (order.status === STATUS_RECEIVED) {
            var btnReady = $('<button action="ready" class="btn btn-large btn-success"><i class="icon-ok icon-white"></i></button>').attr("order_key", order.key).click(
                function (event) {
                    event.stopPropagation();
                    var orderKey = $(this).attr("order_key");
                    readyOrderPressed(orderKey);
                }
            );
            group.append(btnReady);
        }
        if (order.status !== STATUS_COMPLETED) {
            var btnDelete = $('<button action="delete" class="btn btn-large btn-warning"><i class="fa fa-times"></i></button>')
                .attr("order_key", order.key).click(orderDeletePressed);
            group.append(btnDelete);
        }
        toolbar.append(group);
        return toolbar;
    };

    function loadOrders(orderSettings) {
        solutionInboxMessageOrders = {};
        sln.call({
            url: "/common/orders/load",
            type: "GET",
            success: function (data) {
                $.each(data, function (i, o) {
                    o.date_time = sln.formatDate(o.timestamp, false);
                    o.takeaway_time_formatted = o.takeaway_time ? sln.formatDate(o.takeaway_time, false) : '';
                    ordersDict[o.key] = o;

                    if (o.solution_inbox_message_key) {
                        solutionInboxMessageOrders[o.solution_inbox_message_key] = o;
                        if (solutionInboxMessageOrderRequests[o.solution_inbox_message_key]) {
                            sln.setInboxActions(o.solution_inbox_message_key, getActionsForOrder(o, orderSettings));
                            delete solutionInboxMessageOrderRequests[o.solution_inbox_message_key];
                        }
                    }
                });
                orders = data;
                renderOrders(orderSettings);
            }
        });
    }

    function filterOrders(order) {
        if (showAllOrders) {
            return true;
        }
        return order.status === STATUS_RECEIVED;
    }

    function isPaused(orderSettings) {
        return orderSettings.pause_settings.paused_until !== null && new Date(orderSettings.pause_settings.paused_until) > new Date();
    }

    var renderOrders = function (orderSettings) {
        var orderElement = $("#orders-list");
        var localOrders = orders.filter(filterOrders);
        var pausedUntil = orderSettings.pause_settings.paused_until;
        var paused = isPaused(orderSettings);
        var pausedMessage = paused ? T('orders_currently_paused_until', {date: sln.format(new Date(pausedUntil))}) : '';
        var html = $.tmpl(templates.order_list, {
            orders: localOrders,
            advancedOrder: orderSettings.order_type === CONSTS.ORDER_TYPE_ADVANCED,
            formatHtml: sln.formatHtml,
            paused: paused,
            T: T,
            pausedMessage: pausedMessage,
            pauseEnabled: orderSettings.pause_settings.enabled,
        });
        orderElement.html(html);
        orderElement.find('button[action="view"]').click(function () {
            var orderKey = $(this).attr("order_key");
            orderViewPressed(orderKey);
        });
        orderElement.find('button[action="delete"]').click(orderDeletePressed);
        var badge = $('.sln-orders-badge');
        if (showAllOrders) {
            badge.text('');
        } else {
            badge.text(localOrders.length || '');
        }
        sln.resize_header();
        updateShowHideOrders();
        $("#ordersShowTodo, #ordersShowAll").click(function () {
            showAllOrders = !showAllOrders;
            renderOrders(orderSettings);
        });
        $('#btn-pause-orders').toggle(orderSettings.pause_settings.enabled).click(function () {
            if (isPaused(orderSettings)) {
                putOrderSettings(null);
            } else {
                var html = $.tmpl(templates.pause_orders_modal, {
                    T: T,
                    message: orderSettings.pause_settings.message,
                });
                var modal = sln.createModal(html, onShown);

                function onShown() {
                    var defaultTime = new Date().getHours() + 2;
                    var timePickerElem = $('#paused-until-time');
                    timePickerElem.timepicker({
                        defaultTime: defaultTime + ":00",
                        showMeridian: false,
                    });
                    $('button[action="submit"]', modal).click(function () {
                        var time = timePickerElem.val().split(':').map(function (d) {
                            return parseInt(d);
                        });
                        var hour = time[0];
                        var minute = time[1];
                        var date = new Date();
                        date.setHours(hour);
                        date.setMinutes(minute);
                        date.setSeconds(0);
                        var message = modal.find('#orders-paused-message').val();
                        modal.modal('hide');
                        putOrderSettings(date.toISOString(), message);
                    });
                }
            }
        });
    };

    var fadeOutMessageAndUpdateBadge = function (orderKey) {
        $('#order').find('tr[order_key="' + orderKey + '"]').fadeOut('normal', function () {
            $(this).remove();
        });
        var badge = $('.sln-orders-badge');
        var newBadgeValue = badge.text() - 1;
        badge.text(newBadgeValue > 0 ? newBadgeValue : '');
        sln.resize_header();
    };

    var sendMessage = function (order, defaultMessage) {
        sln.inputBox(function (message) {
                sln.call({
                    url: "/common/order/sendmessage",
                    type: "POST",
                    data: {
                        data: JSON.stringify({
                            order_key: order.key,
                            order_status: STATUS_RECEIVED,
                            message: message
                        })
                    },
                    success: function (data) {
                        if (!data.success) {
                            return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                        }
                    }
                });
            }, CommonTranslations.REPLY, null,
            CommonTranslations.REPLY_TO_MORE_INFO.replace("%(username)s", order.sender_name),
            defaultMessage);
    };
    
    function capitalize(s) {
        return s.charAt(0).toUpperCase() + s.substr(1);
    }

    function orderViewPressed(orderKey) {
        Requests.getOrderSettings().then(function (orderSettings) {
            var order = ordersDict[orderKey];
            order.takeaway_time_formatted = sln.format(new Date(order.takeaway_time * 1000));
            var html = $.tmpl(templates.order, {
                header: CommonTranslations.DETAILS,
                closeBtn: CommonTranslations.CLOSE,
                sendMessageBtn: CommonTranslations.REPLY,
                sendOrderReadyBtn: CommonTranslations.READY_FOR_COLLECTION,
                order_key: orderKey,
                order: order,
                advancedOrder: orderSettings.order_type === CONSTS.ORDER_TYPE_ADVANCED,
                CommonTranslations: CommonTranslations,
                T: T,
                formatHtml: sln.formatHtml,
                transactionStatus: order.transaction ? T(capitalize(order.transaction.status)) : null,
            });
            var modal = sln.createModal(html);

            $('button[action="sendmessage"]', html).click(function () {
                modal.modal('hide');
                var defaultMessage = null;
                if (orderSettings.manual_confirmation) {
                    defaultMessage = CommonTranslations.order_confirmed;
                }
                sendMessage(order, defaultMessage);
            });

            if (order.status === STATUS_COMPLETED) {
                $('button[action="sendorderready"]', html).hide();
            }

            $('button[action="sendorderready"]', html).click(function () {
                modal.modal('hide');
                readyOrderPressed(orderKey);
            });
        });
    }

    var readyOrderPressed = function (orderKey) {
        Requests.getOrderSettings().then(function (orderSettings) {
            sln.inputBox(function (message, btn) {
                    var msg = message;
                    if (btn == 2) {
                        msg = "";
                    }
                    sln.call({
                        url: "/common/order/sendmessage",
                        type: "POST",
                        data: {
                            data: JSON.stringify({
                                order_key: orderKey,
                                order_status: STATUS_COMPLETED,
                                message: msg
                            })
                        },
                        success: function (data) {
                            if (!data.success) {
                                return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                            }
                        }
                    });
                }, CommonTranslations.READY, CommonTranslations.READY, null, orderSettings.order_ready_message, null,
                CommonTranslations.dont_send_message);
        });
    };

    var orderDeletePressed = function (event) {
        event.stopPropagation();
        var orderKey = $(this).attr("order_key");
        sln.inputBox(function (message, btn) {
            var msg = message;
            if (btn == 2) {
                msg = "";
            }
            sln.call({
                url: "/common/order/delete",
                type: "POST",
                data: {
                    data: JSON.stringify({
                        order_key: orderKey,
                        message: msg
                    })
                },
                success: function (data) {
                    if (!data.success) {
                        return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    }
                    fadeOutMessageAndUpdateBadge(orderKey);
                    var order = ordersDict[orderKey];
                    delete solutionInboxMessageOrders[order.solution_inbox_message_key];
                    sln.setInboxActions(order.solution_inbox_message_key, undefined);
                }
            });
        }, CommonTranslations.DELETE, CommonTranslations.DELETE, null, CommonTranslations.REPLY_ORDER_CANCEL, null, CommonTranslations.dont_send_message);
    };

    var initorderTimeframeModal = function (day, time_from, time_until) {
        settingsSection.find('#dates').val(day);
        settingsSection.find('#timepickerEnabledFrom').timepicker('setTime', sln.intToTime(time_from));
        settingsSection.find('#timepickerEnabledUntil').timepicker('setTime', sln.intToTime(time_until));
    };

    var loadorderTimeframes = function () {
        sln.call({
            url: "/common/order/settings/timeframe/load",
            type: "GET",
            success: function (data) {
                var timeframes = $("#order_timeframes");

                data.sort(function (tf1, tf2) {
                    if (tf1.day < tf2.day)
                        return -1;
                    if (tf1.day > tf2.day)
                        return 1;

                    if (tf1.time_from < tf2.time_from)
                        return -1;
                    if (tf1.time_from > tf2.time_from)
                        return 1;

                    if (tf1.time_until < tf2.time_until)
                        return -1;
                    if (tf1.time_until > tf2.time_until)
                        return 1;

                    return 0;
                });

                $.each(data, function (i, d) {
                    d.time_from_str = sln.intToTime(d.time_from, false);
                    d.time_until_str = sln.intToTime(d.time_until, false);
                });

                var html = $.tmpl(templates.timeframe_template, {
                    timeframes: data,
                    type: 'order'
                });
                timeframes.find('tbody').html(html);
                $.each(data, function (i, d) {
                    $("#" + d.id).data("timeframe", d);
                });

                timeframes.find('button[action="edit"]').click(function () {
                    var timeframeId = $(this).attr("timeframe_id");
                    $("#save_order_timeframe").attr("timeframe_id", timeframeId);
                    $("#orderTimeframeModalLabel").text(CommonTranslations.TIMEFRAME_UPDATE);
                    var timeframe = $("#" + timeframeId).data("timeframe");
                    initorderTimeframeModal(timeframe.day, timeframe.time_from, timeframe.time_until);
                });
                timeframes.find('button[action="delete"]').click(function () {
                    var timeframeId = $(this).attr("timeframe_id");
                    sln.call({
                        url: "/common/order/settings/timeframe/delete",
                        type: "POST",
                        data: {
                            data: JSON.stringify({
                                timeframe_id: parseInt(timeframeId)
                            })
                        },
                        success: function (data) {
                            if (!data.success) {
                                return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                            }
                        }
                    });
                });
            }
        });
    };

    $("#create_order_timeframe").click(function () {
        $("#save_order_timeframe").attr("timeframe_id", null);
        $("#orderTimeframeModalLabel").text(CommonTranslations.TIMEFRAME_CREATE);
        initorderTimeframeModal(0, 9 * 3600, 18 * 3600);
    });

    $("#save_order_timeframe").click(function () {
        var old_timeframe_id = $(this).attr("timeframe_id");
        var day = parseInt(settingsSection.find("#dates").val());
        var fromPicker = settingsSection.find("#timepickerEnabledFrom").data("timepicker");
        var timeFrom = fromPicker.hour * 3600 + fromPicker.minute * 60;
        var untilPicker = settingsSection.find("#timepickerEnabledUntil").data("timepicker");
        var timeUntil = untilPicker.hour * 3600 + untilPicker.minute * 60;

        if (timeFrom == timeUntil) {
            return sln.alert(CommonTranslations.TIME_START_END_EQUAL);
        }
        if (timeFrom >= timeUntil) {
            return sln.alert(CommonTranslations.TIME_START_END_SMALLER);
        }
        sln.call({
            url: "/common/order/settings/timeframe/put",
            type: "POST",
            data: {
                data: JSON.stringify({
                    timeframe_id: old_timeframe_id ? parseInt(old_timeframe_id) : null,
                    day: day,
                    time_from: timeFrom,
                    time_until: timeUntil
                })
            },
            success: function (data) {
                if (!data.success) {
                    return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
                $("#orderTimeframeModal").modal('hide');
            }
        });
    });

    settingsSection.find('#timepickerEnabledFrom').timepicker({
        defaultTime: "09:00",
        showMeridian: false,
        minuteStep: 5
    });
    settingsSection.find('#timepickerEnabledUntil').timepicker({
        defaultTime: "18:00",
        showMeridian: false,
        minuteStep: 5
    });

    function loadPaymentSettings(refresh) {
        var promises = [Requests.getPaymentSettings({cached: !refresh}), Requests.getPaymentProviders({cached: !refresh})];
        Promise.all(promises).then(function (results) {
            var paymentSettings = results[0];
            var paymentProviders = results[1];
            renderPaymentSettings(paymentSettings, paymentProviders);
        });
    }

    function renderPaymentSettings(paymentSettings, paymentProviders) {
        var settings = paymentProviders.reduce(function (acc, provider) {
            acc[provider.provider_id] = provider;
            return acc;
        }, {});
        var html = $.tmpl(templates['payments'], {
            payconiqHtml: templates['payconiq_nl'],
            paymentSettings: paymentSettings,
            paymentProviders: paymentProviders,
            settings: settings,
        });
        $('#section_settings_mobile_payments').html(html);

        $('.downloaded-hint').click(function () {
            var self = $(this);
            if (!self.next('p').length) {
                self.after(
                    '<p>' + CommonTranslations.file_downloaded_explanation + '</p>'
                );
            }
        });
        $('#payments_optional').change(savePaymentSettings);
        sln.configureDelayedInput($('#payment_min_amount_for_fee'), savePayconiqSettings);
        sln.configureDelayedInput($("#payconicMerchantId"), savePayconiqSettings);
        sln.configureDelayedInput($("#payconiqAccessToken"), savePayconiqSettings);
        $('#payconiq_enabled').change(savePayconiqSettings);
        sln.configureDelayedInput($("#threefold_address"), saveThreefoldSettings);
        $('#threefold_enabled').change(saveThreefoldSettings);
    }

    function savePaymentSettings() {
        var data = {
            optional: $('#payments_optional').prop('checked')
        };
        Requests.savePaymentSettings(data).then(function (updatedSettings) {
            Requests.getPaymentProviders().then(function (paymentProviders) {
                renderPaymentSettings(updatedSettings, paymentProviders);
            });
        });
    }

    var savePayconiqSettings = function() {
        var data = {
            provider_id: 'payconiq',
            enabled: $('#payconiq_enabled').prop('checked'),
            settings: {
                merchant_id: $("#payconicMerchantId").val().trim(),
                jwt: $("#payconiqAccessToken").val().trim(),
            },
            fee: {
                min_amount: Math.round(parseFloat($('#payment_min_amount_for_fee').val()) * 100),
                fee: 15,
                precision: 2,
                currency: 'EUR',
            }
        };
        Requests.savePaymentProvider('payconiq', data).then(function () {
            loadPaymentSettings(true);
        });
    };

    function saveThreefoldSettings() {
        var data = {
            provider_id: 'threefold',
            enabled: $('#threefold_enabled').prop('checked'),
            settings: {
                address: $("#threefold_address").val().trim(),
            },
            fee: {
                min_amount: 0,
                fee: 0,
                precision: 9,
                currency: 'TFT',
            }
        };
        Requests.savePaymentProvider('threefold', data).then(function () {
            loadPaymentSettings(true);
        });
    }

    sln.registerMsgCallback(channelUpdates);
    Requests.getOrderSettings().then(function (orderSettings) {
        renderOrderSettings(orderSettings);
        loadOrders(orderSettings);
    });
    loadPaymentSettings();


    sln.registerInboxActionListener("order", function (chatId) {
        Requests.getOrderSettings().then(function (orderSettings) {
            var o = solutionInboxMessageOrders[chatId];
            if (o) {
                sln.setInboxActions(o.solution_inbox_message_key, getActionsForOrder(o, orderSettings));
            } else {
                solutionInboxMessageOrderRequests[chatId] = chatId;
            }
        });
    });
    var _putOrderSettings = function () {
        putOrderSettings();
    };
    sln.configureDelayedInput($("#order_settings_text1"), _putOrderSettings);
    sln.configureDelayedInput($("#order_leaptime"), _putOrderSettings);
    sln.configureDelayedInput($("#order_leaptime_type"), _putOrderSettings);
    sln.configureDelayedInput($("#order_ready_default_message"), _putOrderSettings);
    sln.configureDelayedInput($("#pause-settings-message"), _putOrderSettings);
    sln.configureDelayedInput($("#outside-hours-message"), _putOrderSettings);

});
