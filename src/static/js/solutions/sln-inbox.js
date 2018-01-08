/*
 * Copyright 2017 Mobicage NV
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
 * @@license_version:1.2@@
 */

$(function() {
    var INBOX_NAME_UNREAD = "unread";
    var INBOX_NAME_STARRED = "starred";
    var INBOX_NAME_READ = "read";
    var INBOX_NAME_TRASH = "trash";
    var INBOX_NAME_DELETED = "deleted";

    var messagesList = [];
    var inboxData = {};
    inboxData[INBOX_NAME_DELETED] = {count:0};

    var currentReplyMessageKey = null;
    var inboxReply = $("#inbox-reply");
    var inboxOverview = $("#inbox-overview");

    function getMessageByKey(messageKey) {
        return messagesList.filter(function(m) {
            return m.key === messageKey;
        })[0];
    }

    function removeMessage(message) {
        messagesList.splice(messagesList.indexOf(message), 1);
    }

    /**
     * To be used to update a single message that isn't being moved to a different inbox.
     * @param message The message to be updated
     */
    function getMessageHtml(message) {
        return $.tmpl(templates.inbox_messages, {
            messages: [message],
            CommonTranslations: CommonTranslations,
            showEmails: EMAIL_SETTINGS["inbox"] === true,
            formatHtml: sln.formatHtml,
            canForward: MODULES.indexOf('city_app') !== -1 /* city service only */
        });
    }

    function addMessageToInbox(message, inbox) {
        var html = getMessageHtml(message);
        $('#inbox-' + inbox).find('tbody').prepend(html);
        sln.getInboxActions(message.category, message.key);
        inboxData[message.inbox].count++;
        updateBadges(INBOX_NAME_UNREAD, INBOX_NAME_UNREAD);
    }

    var channelUpdates = function(data) {
        if (data.type == 'solutions.common.messaging.update') {
            data.message.date_time = sln.formatDate(data.message.timestamp, true);
            var fromInbox = null;
            var destinationInbox = data.message.inbox;
            var message = getMessageByKey(data.message.key);
            if(message) {
                fromInbox = message.inbox;
            } else {
                // new message
                messagesList.push(data.message);
                message = data.message;
                addMessageToInbox(message, INBOX_NAME_UNREAD);
            }

            if(destinationInbox === INBOX_NAME_DELETED) {
                removeMessage(message);
                fadeOutMessageAndUpdateBadge(message, INBOX_NAME_DELETED, fromInbox);
            }
            else if(fromInbox) {
                // Message updated, update its properties.
                for(var messageProperty in data.message) {
                    if(data.message.hasOwnProperty(messageProperty))
                        message[messageProperty] = data.message[messageProperty];
                }
                if(currentReplyMessageKey !== null && currentReplyMessageKey === data.message.key) {
                    // Message details updated.
                    loadMessageDetail(true);
                }
                else if(fromInbox === destinationInbox) {
                    // Updated message in same inbox. Re-render only this particular message.
                    var html = getMessageHtml(message);
                    $('#' + message.key).html(html.html());
                    sln.getInboxActions(message.category, message.key);
                } else {
                    // Message moved from inbox. Delete from current inbox and re-render destination inbox.
                    fadeOutMessageAndUpdateBadge(message, message.inbox, fromInbox);
                    renderMessagesForInbox(message.inbox);
                }
            }
        } else if (data.type == 'solutions.common.messaging.deleted') {
            // delete all messages from trash
            deleteAllTrashedMessages();
        }
    };

    var inboxLoadAll = function() {
        sln.call({
            url : "/common/inbox/load/all",
            type : "GET",
            success : function(data) {
                //Render all inboxes
                $.each(data, function(i, o) {
                    addMessagesToInbox(true, o);
                });
                validateLoadMore();
            }
        });
    };

    var addMessagesToInbox = function(refresh, o) {
        if (refresh) {
            messagesList = messagesList.filter(function(message) {
                return message.inbox !== o.name;
            });
        }
        if(inboxData[o.name]) {
            inboxData[o.name].count += o.messages.length;
            inboxData[o.name].cursor = o.cursor;
            inboxData[o.name].has_more = o.has_more;
            inboxData[o.name].loading = false;
        } else {
            inboxData[o.name] = {
                name: o.name,
                count: o.messages.length,
                cursor: o.cursor,
                has_more: o.has_more,
                loading: false
            };
        }

        for(var i = 0; i < o.messages.length; i++) {
            var message = o.messages[i];
            message.date_time = sln.formatDate(message.timestamp, true);
            messagesList.push(message);
        }
        renderMessagesForInbox(o.name);
    };


    var renderMessagesForInbox = function(inboxName) {
        var slnInboxBadgeElem = $('.sln-inbox-badge');
        var inboxElem = $("#inbox-" + inboxName);
        var _tmpCount;
        var tmp_messages = messagesList.filter(function(message) {
            return message.inbox === inboxName;
        }).sort(function(message1, message2) {
            return message2.timestamp - message1.timestamp;
        });

        var html = $.tmpl(templates.inbox_messages, {
            messages : tmp_messages,
            CommonTranslations : CommonTranslations,
            showEmails: EMAIL_SETTINGS["inbox"] === true,
            formatHtml: sln.formatHtml,
            canForward: MODULES.indexOf('city_app') !== -1 /* city service only */
        });

        switch(inboxName) {
            case INBOX_NAME_UNREAD:
                if(inboxData[inboxName].has_more) {
                    _tmpCount = tmp_messages.length > 10 ? 10 : tmp_messages.length;
                slnInboxBadgeElem.text(_tmpCount + '+');
                } else {
                    slnInboxBadgeElem.text(tmp_messages.length || '');
                }
                break;
            case INBOX_NAME_DELETED:
                return;
        }

        inboxElem.attr("_count", tmp_messages.length).find("tbody").html(html);
        if(inboxData[inboxName].has_more) {
            _tmpCount = tmp_messages.length > 10 ? 10 : tmp_messages.length;
            inboxOverview.find('.nav').find('li[section="inbox-' + inboxName + '"] span').text(_tmpCount + '+');
        } else {
            inboxOverview.find('.nav').find('li[section="inbox-' + inboxName + '"] span').text(tmp_messages.length || '');
        }

        inboxElem.find(".load-more").toggle(tmp_messages.length && inboxData[inboxName].has_more);
        for(var i = 0; i < tmp_messages.length; i++) {
            if(tmp_messages[i].category) {
                sln.getInboxActions(tmp_messages[i].category, tmp_messages[i].key);
            }
        }
    };

    var fadeOutMessageAndUpdateBadge = function(message, newInbox, fromInbox) {
        inboxOverview.find('#' + message.key).fadeOut('normal', function() {
            $(this).remove();
        });
        validateLoadMore();
        updateBadges(newInbox, fromInbox);
    };

    function updateBadges(newInbox, fromInbox) {
        var messageDeleted = (fromInbox === INBOX_NAME_TRASH && newInbox === INBOX_NAME_TRASH);
        inboxData[fromInbox].count--;
        if(!messageDeleted) {
            inboxData[newInbox].count++;
        }
        var fromCount = inboxData[fromInbox].count;
        if(fromInbox === INBOX_NAME_UNREAD) {
            if(inboxData[INBOX_NAME_UNREAD].has_more) {
                var _tmpCount = fromCount > 10 ? 10 : fromCount;
                $('.sln-inbox-badge').text(_tmpCount + '+');
            } else {
                $('.sln-inbox-badge').text(fromCount || '');
            }
        } else if(newInbox === INBOX_NAME_UNREAD) {
            var newCount = inboxData[INBOX_NAME_UNREAD].count;
            if(inboxData[INBOX_NAME_UNREAD].has_more) {
                var _tmpCount = newCount > 10 ? 10 : newCount;
                $('.sln-inbox-badge').text(_tmpCount + '+');
            } else {
                $('.sln-inbox-badge').text(newCount || '');
            }
        }
        sln.resize_header();

        if(inboxData[fromInbox].has_more) {
            var _tmpCount = fromCount > 10 ? 10 : fromCount;
            inboxOverview.find('.nav li[section="inbox-' + fromInbox + '"] span').text(_tmpCount + '+');
        } else {
            inboxOverview.find('.nav li[section="inbox-' + fromInbox + '"] span').text(fromCount || '');
        }
    }

    var markMessageAsRead = function(message) {
        if(!message) {
            return;
        }
        var button = inboxOverview.find('.inbox-message-action-read[message_key="' + message.key + '"] i')
            .toggleClass('fa-eye', !message.read)
            .toggleClass("fa-eye-slash", message.read);
        if (message.inbox === INBOX_NAME_UNREAD || message.inbox === INBOX_NAME_READ) {
            button.parents('tr').fadeTo(300, 0.5);
        }
        sln.call({
            url : "/common/inbox/message/update/read",
            type : "POST",
            data : {
                data : JSON.stringify({
                    key: message.key,
                    read: message.read
                })
            }
        });
    };

    var loadMessageDetail = function(refresh) {
        sln.call({
            url : "/common/inbox/load/detail",
            type : "get",
            data : {key:currentReplyMessageKey},
            success : function(data) {
                if (currentReplyMessageKey === null) {
                    return;
                }
                var message = getMessageByKey(currentReplyMessageKey);
                if(!message) {
                    return;
                }
                if (!refresh) {
                    inboxReply.find(".inbox-reply-title i").attr("class", "fa " + data[0].icon).css("color", data[0].icon_color);
                    inboxReply.find(".inbox-reply-title span").text(data[0].chat_topic);

                    inboxReply.find(".inbox-message-action-starred").show().find('i')
                        .toggleClass("fa-star", data[0].starred)
                        .toggleClass("fa-star-o", !data[0].starred);
                    inboxReply.find(".inbox-message-action-read").show().find('i')
                        .toggleClass('fa-eye', !data[0].read)
                        .toggleClass("fa-eye-slash", data[0].read);
                    inboxReply.find(".inbox-message-action-trash").show();
                    inboxReply.find(".inbox-reply-input").toggle(data[0].reply_enabled);
                } else {
                    inboxReply.find('.inbox-message-action-starred[message_key="' + currentReplyMessageKey + '"] i')
                        .toggleClass("fa-star", message.starred)
                        .toggleClass("fa-star-o", !message.starred);

                    inboxReply.find('.inbox-message-action-read[message_key="' + currentReplyMessageKey + '"] i')
                        .toggleClass('fa-eye', !message.read)
                        .toggleClass("fa-eye-slash", message.read);
                }

                $.each(data, function(i, m) {
                    m.date_time = sln.formatDate(m.timestamp, true);
                });

                var html = $.tmpl(templates.inbox_detail_messages, {
                    messages : data,
                    CommonTranslations: CommonTranslations,
                    formatHtml: sln.formatHtml
                });

                inboxReply.find("tbody").html(html);
                inboxReply.trigger('message-details-loaded');
            }
        });
    };

    $(document).on("click", '.inbox-message-action-reply', function(event) {
        event.stopPropagation();
        var messageKey = $(this).attr("message_key");
        inboxReply.find("tbody").html("<tr><td>" + CommonTranslations.LOADING_DOT_DOT_DOT + "</td></tr>");
        inboxReply.find(".inbox-message-action-starred, .inbox-message-action-read, .inbox-message-action-trash")
            .hide().attr("message_key", messageKey);
        inboxReply.find(".inbox-reply-input").hide();
        inboxReply.find(".inbox-reply-input button").attr("message_key", messageKey);
        inboxReply.find(".inbox-reply-input textarea").val("");
        inboxOverview.hide();
        inboxReply.show();
        currentReplyMessageKey = messageKey;
        loadMessageDetail(false);
    });

    $(document).on('click', '.inbox-message-action-forward', function(event) {
        event.stopPropagation();
        var messageKey = $(this).attr("message_key");
        var html = $.tmpl(templates['services/service_search'], {
            title: CommonTranslations.forward_message_to_service,
            placeholder: CommonTranslations.service_name,
        });

        var modal = sln.createModal(html, function(modal) {
            $('#service_name_input', modal).focus();
        });

        var input = $('#service_name_input', modal);
        function serviceSelected(serviceEmail) {
            sln.call({
                url: '/common/inbox/message/forward',
                showProcessing: true,
                type: 'post',
                data: {
                    key: messageKey,
                    to_email: serviceEmail,
                },
                success: function(status) {
                    if (!status.success) {
                        sln.alert(CommonTranslations[status.errormsg]);
                    }
                },
                error: sln.showAjaxError
            });
            modal.modal('hide');
        }

        sln.serviceSearch(input, ORGANIZATION_TYPES, CONSTS.ORGANIZATION_TYPES.CITY,
                          serviceSelected);
    });

    $(document).on("click", '.inbox-message-action-starred', function(event) {
        event.stopPropagation();
        var messageKey = $(this).attr("message_key");
        goBackToInboxOverview();
        var message = getMessageByKey(messageKey);
        if(!message) {
            return;
        }
        message.starred = !message.starred;
        sln.call({
            url: "/common/inbox/message/update/starred",
            type: "POST",
            data: {
                data: JSON.stringify({
                    key: messageKey,
                    starred: message.starred
                })
            }
        });
        inboxOverview.find('.inbox-message-action-starred[message_key="' + messageKey + '"] i')
            .toggleClass('fa-star-o', !message.starred)
            .toggleClass("fa-star", message.starred)
            .parents('tr').fadeTo(300, 0.5);
    });

    $(document).on("click", '.inbox-message-action-read', function(event) {
        event.stopPropagation();
        var messageKey = $(this).attr("message_key");
        goBackToInboxOverview();
        var message = getMessageByKey(messageKey);
        if(!message) {
            return;
        }
        message.read = !message.read;
        markMessageAsRead(message);
    });

    $(document).on("click", '.inbox-message-action-trash', function(event) {
        event.stopPropagation();
        var messageKey = $(this).attr("message_key");
        goBackToInboxOverview();
        sln.call({
            url : "/common/inbox/message/update/trashed",
            type : "POST",
            data : {
                data : JSON.stringify({
                    key : messageKey,
                    trashed : true
                })
            }
        });
    });

    var inboxMenuItem = $('#topmenu').find('li[menu=inbox]');

    var validateLoadMore = function() {
        var id_ = inboxOverview.find(".nav li.active").attr("section");
        var name_ = id_.replace("inbox-", "");
        if(inboxData[name_] === undefined) {
            return;
        }
        var inboxIsOpen = inboxMenuItem.hasClass('active');

        if(inboxIsOpen && sln.isOnScreen($("#" + id_).find("table tr:last"))) {
            if(inboxData[name_].has_more && inboxData[name_].loading === false) {
                inboxData[name_].loading = true;
                sln.call({
                    url : "/common/inbox/load/more",
                    type : "get",
                    data : inboxData[name_],
                    success : function(data) {
                        addMessagesToInbox(false, data);
                        inboxData[name_].loading = false;
                        validateLoadMore();
                    }
                });
            }
        }
    };

    $(window).scroll(function() {
        validateLoadMore();
    });

    inboxOverview.find(".nav li a").on("click", function () {
        inboxOverview.find(".nav li").removeClass("active");
        var li = $(this).parent().addClass("active");
        inboxOverview.find("section").hide();
        inboxOverview.find("section#" + li.attr("section")).show();
        validateLoadMore();
    });

    $("#inbox-trash-all").on("click", function() {
        inboxData[INBOX_NAME_TRASH].has_more = false;
        sln.call({
            url : "/common/inbox/message/update/deleted",
            type : "POST",
            data : {
                data : JSON.stringify({})
            },
            success : function(data) {
                if(data.success) {
                    deleteAllTrashedMessages();
                } else {
                    sln.alert(data.errormsg);
                }
            }
        });
    });

    function deleteAllTrashedMessages() {
        messagesList = messagesList.filter(function(message) {
            return message.inbox !== INBOX_NAME_TRASH;
        });
        renderMessagesForInbox(INBOX_NAME_TRASH);
    }

    var goBackToInboxOverview = function() {
        currentReplyMessageKey = null;
        inboxOverview.show();
        $("#inbox-reply").hide();
    };

    $("#inbox-reply-back").click(goBackToInboxOverview);

    $(".inbox-reply-input button").on("click", function() {
        var messageKey = $(this).attr("message_key");
        var message = inboxReply.find(".inbox-reply-input textarea").val();
        if (message == "") {
            sln.alert(CommonTranslations.PLEASE_ENTER_A_MESSAGE);
            return;
        }
        goBackToInboxOverview();
        sln.call({
            url : "/common/inbox/message/update/reply",
            type : "POST",
            data : {
                data : JSON.stringify({
                    key : messageKey,
                    message : message
                })
            },
            success : function(data) {
            },
            error : sln.showAjaxError
        });
    });

    sln.registerMsgCallback(channelUpdates);

    sln.registerInboxCallbackListener(function(chatId, actions) {
        $('#' + chatId).find('div.inbox-module-actions').html(actions);
    });
    inboxLoadAll();

});
