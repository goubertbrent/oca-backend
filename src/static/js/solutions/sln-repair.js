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

$(function() {
    var STATUS_RECEIVED = 1;
    var STATUS_COMPLETED = 2;

    var solutionInboxMessageRepairOrders = {};
    var solutionInboxMessageRepairRequests = {};
    var repair_orders = {};

    var REPAIR_ORDER_TEMPLATE = '{{each repair_orders}}'
            + ' <tr {{if $value.status == 2 }}class="success"{{/if}} order_key="${$value.key}">'
            + '     <td>${$value.date_time}</td>'
            + '     <td><img class="avatar" src="${$value.sender_avatar_url}">${$value.sender_name}</td>'
            + '     <td>${$value.description}</td>'
            + '     <td>'
            + '         <button action="view" order_key="${$value.key}" class="btn btn-success control">${CommonTranslations.VIEW_REPAIR_ORDER}</button>'
            + '         <button action="delete" order_key="${$value.key}" class="btn btn-warning control">${CommonTranslations.DELETE}</button>'
            + '     </td>' //
            + ' </tr>' //
            + '{{/each}}';

    var channelUpdates = function(data) {
        if (data.type == "rogerthat.system.channel_connected") {
            loadRepairOrders();
            loadRepairSettings();
        }
        else if (data.type == 'solutions.common.repair_orders.update') {
            loadRepairOrders();
        } else if (data.type == 'solutions.common.repair.settings.update') {
            loadRepairSettings();
        }
    };
    
    var loadRepairSettings = function() {
        $.ajax({
            url : "/common/repair/settings/load",
            type : "GET",
            success : function(data) {
                $("#repair_settings_text1").val(data.text_1);
            },
            error : sln.showAjaxError
        });
    };
    
    var putRepairSettings = function() {
        $.ajax({
            url : "/common/repair/settings/put",
            type : "POST",
            data : {
                data : JSON.stringify({
                    text_1: $("#repair_settings_text1").val()
                })
            },
            success : function(data) {
                if (!data.success) {
                    return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
            },
            error : sln.showAjaxError
        });
    };
    
    var getActionsForOrder = function(order) {
        var toolbar = $('<div class="btn-toolbar"></div>');
        var group = $('<div class="btn-group"></div>');
        
        if (order.status == STATUS_RECEIVED) {
            var btnReady = $('<button action="ready" class="btn btn-large btn-success"><i class="icon-ok icon-white"></i></button>').attr("order_key", order.key).click(
                function(event) {
                    event.stopPropagation();
                    var orderKey = $(this).attr("order_key");
                    readyRepairOrderPressed(orderKey);
                }
            );
            group.append(btnReady);
        }
        var btnDelete = $('<button action="delete" class="btn btn-large btn-warning"><i class="icon-remove icon-white"></i></button>').attr("order_key", order.key).click(deleteRepairOrderPressed);
        group.append(btnDelete);
        
        toolbar.append(group);
        return toolbar;
    };

    var loadRepairOrders = function() {
        solutionInboxMessageRepairOrders = {}
        sln.call({
            url : "/common/repair_order/load",
            type : "GET",
            success : function(data) {
                var repair = $("#repair table");
                var repairContent = $("tbody", repair);
                var repairNone = $("#repair_none");
                if (data.length > 0) {
                    repairNone.hide();
                    repair.show();
                    $.each(data, function(i, o) {
                        o.date_time = sln.formatDate(o.timestamp, true);
                        repair_orders[o.key] = o;
                        
                        if (o.solution_inbox_message_key) {
                            solutionInboxMessageRepairOrders[o.solution_inbox_message_key] = o;
                            if (solutionInboxMessageRepairRequests[o.solution_inbox_message_key]) {
                                sln.setInboxActions(o.solution_inbox_message_key, getActionsForOrder(o));
                                delete solutionInboxMessageRepairRequests[o.solution_inbox_message_key];
                            }
                        }
                    });
                    var html = $.tmpl(REPAIR_ORDER_TEMPLATE, {
                        repair_orders : data
                    });
                    repairContent.empty().append(html);
                    $('#repair button[action="view"]').click(function() {
                        var orderKey = $(this).attr("order_key");
                        viewRepairOrderPressed(orderKey);
                    });
                    $('#repair button[action="delete"]').click(deleteRepairOrderPressed);
                } else {
                    repair.hide();
                    repairNone.show();
                }

                $('.sln-repair-badge').text(data.length || '');
                sln.resize_header();
            },
            error : sln.showAjaxError
        });
    };

    var fadeOutMessageAndUpdateBadge = function(orderKey) {
        $('#repair tr[message_key="' + orderKey + '"]').fadeOut('slow', function() {
            $(this).remove();
        });
        var badge = $('.sln-repair-badge');
        var newBadgeValue = badge.text() - 1;
        badge.text(newBadgeValue > 0 ? newBadgeValue : '');
        sln.resize_header();
    };
    
    var viewRepairOrderPressed = function(orderKey) {
        var repairOrder = repair_orders[orderKey];

        var html = $.tmpl(templates.repair_order, {
            header : CommonTranslations.DETAILS,
            closeBtn : CommonTranslations.CLOSE,
            sendMessageBtn : CommonTranslations.REPLY,
            sendOrderReadyBtn : CommonTranslations.READY_FOR_COLLECTION,
            order_key : orderKey,
            sender_avatar_url : repairOrder.sender_avatar_url,
            sender_name : repairOrder.sender_name,
            description : repairOrder.description,
            picture_url : repairOrder.picture_url,
            CommonTranslations : CommonTranslations
        });
        var modal = sln.createModal(html);

        $('button[action="sendmessage"]', html).click(function(){
            modal.modal('hide');
            sln.inputBox(function(message) {
                sln.call({
                    url : "/common/repair_order/sendmessage",
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
            }, CommonTranslations.REPLY, null, CommonTranslations.REPLY_TO_MORE_INFO.replace("%(username)s", repairOrder.sender_name));
        });

        if (repairOrder.status == STATUS_COMPLETED) {
            $('button[action="sendorderready"]', html).hide();
        }
        
        $('button[action="sendorderready"]', html).click(function(){
            modal.modal('hide');
            readyRepairOrderPressed(orderKey);
        });
    };
    
    var readyRepairOrderPressed = function(orderKey) {
        sln.inputBox(function(message, btn) {
            var msg = message;
            if (btn == 2) {
                msg = ""; 
            }
            sln.call({
                url : "/common/repair_order/sendmessage",
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
        }, CommonTranslations.READY, CommonTranslations.READY, null, CommonTranslations.REPLY_REPAIR_READY, null, CommonTranslations.dont_send_message);
    };

    var deleteRepairOrderPressed = function(event) {
        event.stopPropagation();
        var orderKey = $(this).attr("order_key");
        sln.inputBox(function(message, btn) {
            var msg = message;
            if (btn == 2) {
                msg = ""; 
            }
            sln.call({
                url : "/common/repair_order/delete",
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
                    var repairOrder = repair_orders[orderKey];
                    delete solutionInboxMessageRepairOrders[repairOrder.solution_inbox_message_key];
                    sln.setInboxActions(repairOrder.solution_inbox_message_key, undefined);
                }
            });
        }, CommonTranslations.DELETE, CommonTranslations.DELETE, null, CommonTranslations.REPLY_REPAIR_CANCEL, null, CommonTranslations.dont_send_message);
    };

    sln.registerMsgCallback(channelUpdates);
    
    sln.registerInboxActionListener("repair", function(chatId) {
        var o = solutionInboxMessageRepairOrders[chatId];
        if (o) {
            sln.setInboxActions(o.solution_inbox_message_key, getActionsForOrder(o));
        } else {
            solutionInboxMessageRepairRequests[chatId] = chatId;
        }
    });
    sln.configureDelayedInput($("#repair_settings_text1"), putRepairSettings);
});
