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

$(function() {
    "use strict";
    var STATUS_RECEIVED = 1;
    var STATUS_COMPLETED = 2;
    
    var solutionInboxMessagePharmacyOrders = {};
    var solutionInboxMessagePharmacyOrderRequests = {};
    var pharmacyOrders = [];
    var showAllPharmacyOrders = false;

    var channelUpdates = function(data) {
        if (data.type == 'solutions.common.pharmacy_orders.update') {
            loadOrders();
        }
    };

    $("#pharmacyOrdersShowTodo, #pharmacyOrdersShowAll").click(function () {
        showAllPharmacyOrders = !showAllPharmacyOrders;
        updateShowHidePharmacyOrders();
    });

    function updateShowHidePharmacyOrders () {
        $("#pharmacyOrdersShowTodo").toggleClass('btn-success', !showAllPharmacyOrders)
            .html(showAllPharmacyOrders ? '&nbsp;' : CommonTranslations.TODO);
        $("#pharmacyOrdersShowAll").toggleClass('btn-success', showAllPharmacyOrders)
            .html(showAllPharmacyOrders ? CommonTranslations.ALL : '&nbsp;');
        renderOrders();
    }
    
    var getActionsForOrder = function(order) {
        var toolbar = $('<div class="btn-toolbar"></div>');
        var group = $('<div class="btn-group"></div>');
        
        if (order.status == STATUS_RECEIVED) {
            var btnReady = $('<button action="ready" class="btn btn-large btn-success"><i class="icon-ok icon-white"></i></button>').attr("order_key", order.key).click(
                function(event) {
                    event.stopPropagation();
                    var orderKey = $(this).attr("order_key");
                    readyOrderPressed(orderKey);
                }
            );
            group.append(btnReady);
            var btnDelete = $('<button action="delete" class="btn btn-large btn-warning"><i class="icon-remove icon-white"></i></button>').attr("order_key", order.key).click(orderDeletePressed);
            group.append(btnDelete);
        }

        toolbar.append(group);
        return toolbar;
    };

    var loadOrders = function() {
        solutionInboxMessagePharmacyOrders = {};
        sln.call({
            url : "/common/pharmacy_orders/load",
            type : "GET",
            success : function(data) {
                pharmacyOrders = data;
                updateShowHidePharmacyOrders();
            }
        });
    };

    function renderOrders () {
        var pharmacyOrdersElem = $("#pharmacy_orders");
        var inbox = pharmacyOrdersElem.find("tbody");
        var unreadPharmacyOrders = pharmacyOrders.filter(function(order){
            return order.status === STATUS_RECEIVED;
        });
        $.each(pharmacyOrders, function (i, o) {
            o.date_time = sln.formatDate(o.timestamp, true);

            if (o.solution_inbox_message_key) {
                solutionInboxMessagePharmacyOrders[o.solution_inbox_message_key] = o;
                if (solutionInboxMessagePharmacyOrderRequests[o.solution_inbox_message_key]) {
                    sln.setInboxActions(o.solution_inbox_message_key, getActionsForOrder(o));
                    delete solutionInboxMessagePharmacyOrderRequests[o.solution_inbox_message_key];
                }
            }
        });
        var html = $.tmpl(templates.pharmacy_order_list, {
            orders: showAllPharmacyOrders ? pharmacyOrders : unreadPharmacyOrders
        });
        inbox.empty().append(html);
        pharmacyOrdersElem.find('button[action="view"]').click(function () {
            var orderKey = $(this).attr("order_key");
            orderViewPressed(orderKey);
        });
        pharmacyOrdersElem.find('button[action="delete"]').click(orderDeletePressed);
        $('.sln-pharmacy_orders-badge').text(unreadPharmacyOrders.length || '');
    }

    function getOrder (orderKey) {
        return pharmacyOrders.filter(function (order) {
            return order.key === orderKey;
        })[0];
    }

    var fadeOutMessageAndUpdateBadge = function(orderKey) {
        $('#pharmacy_orders').find('tr[order_key="' + orderKey + '"]').fadeOut('slow', function () {
            $(this).remove();
        });
        var badge = $('.sln-pharmacy_orders-badge');
        var newBadgeValue = badge.text() - 1;
        badge.text(newBadgeValue > 0 ? newBadgeValue : '');
    };

    var orderViewPressed = function(orderKey) {
        var order = getOrder(orderKey);
        
        var html = $.tmpl(templates.pharmacy_order, {
            header : CommonTranslations.details,
            closeBtn : CommonTranslations.CLOSE,
            sendMessageBtn : CommonTranslations.REPLY,
            sendOrderReadyBtn : CommonTranslations.READY_FOR_COLLECTION,
            order_key : orderKey,
            sender_avatar_url : order.sender_avatar_url,
            sender_name : order.sender_name,
            description : order.description != null ? sln.htmlize(order.description) : null,
            remarks : order.remarks != null ? sln.htmlize(order.remarks) : null,
            picture_url : order.picture_url,
            CommonTranslations : CommonTranslations
        });
        var modal = sln.createModal(html);
        
        $('button[action="sendmessage"]', html).click(function(){
            modal.modal('hide');
            sln.inputBox(function(message) {
                sln.call({
                    url : "/common/pharmacy_order/sendmessage",
                    type : "POST",
                    data : {
                        data : JSON.stringify({
                            order_key : orderKey,
                            order_status : STATUS_RECEIVED,
                            message : message
                        })
                    },
                    success : function(data) {
                        if (!data.success) {
                            return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                        }
                    },
                    error : sln.showAjaxError
                });
            }, CommonTranslations.REPLY, null, CommonTranslations.REPLY_TO_MORE_INFO.replace("%(username)s", order.sender_name));
        });
        
        if (order.status == STATUS_COMPLETED) {
            $('button[action="sendorderready"]', html).hide();
        }
        
        $('button[action="sendorderready"]', html).click(function(){
            modal.modal('hide');
            readyOrderPressed(orderKey);
        });
    };
    
    var readyOrderPressed = function(orderKey) {
        sln.inputBox(function(message, btn) {
            var msg = message;
            if (btn == 2) {
                msg = ""; 
            }
            sln.call({
                url : "/common/pharmacy_order/sendmessage",
                type : "POST",
                data : {
                    data : JSON.stringify({
                        order_key : orderKey,
                        order_status : STATUS_COMPLETED,
                        message : msg
                    })
                },
                success : function(data) {
                    if (!data.success) {
                        return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    }
                }
            });
        }, CommonTranslations.READY, CommonTranslations.READY, null, CommonTranslations.REPLY_ORDER_READY, null, CommonTranslations.dont_send_message);
    };

    var orderDeletePressed = function(event) {
        event.stopPropagation();
        var orderKey = $(this).attr("order_key");
        sln.inputBox(function(message, btn) {
            var msg = message;
            if (btn == 2) {
                msg = ""; 
            }
            sln.call({
                url : "/common/pharmacy_order/delete",
                type : "POST",
                data : {
                    data : JSON.stringify({
                        order_key : orderKey,
                        message : msg
                    })
                },
                success : function(data) {
                    if (!data.success) {
                        return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    }
                    fadeOutMessageAndUpdateBadge(orderKey);
                    var order = getOrder(orderKey);
                    delete solutionInboxMessagePharmacyOrders[order.solution_inbox_message_key];
                    sln.setInboxActions(order.solution_inbox_message_key, undefined);
                }
            });
        }, CommonTranslations.DELETE, CommonTranslations.DELETE, null, CommonTranslations.REPLY_ORDER_CANCEL, null, CommonTranslations.dont_send_message);
    };

    sln.registerMsgCallback(channelUpdates);
    loadOrders();
    
    sln.registerInboxActionListener("pharmacy_order", function(chatId) {
        var o = solutionInboxMessagePharmacyOrders[chatId];
        if (o) {
            sln.setInboxActions(o.solution_inbox_message_key, getActionsForOrder(o));
        } else {
            solutionInboxMessagePharmacyOrderRequests[chatId] = chatId;
        }
    });
});
