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

$(function () {

    var reviewMessages = {};
    var reviewMessageRequests = {};

    var loadReviewRequests = function () {
        sln.call({
            url: '/common/news/reviews',
            type: 'get',
            data: {
                app_id: CITY_APP_ID,
            },
            success: function (data) {
                reviewMessages = {};
                $.each(data, function (i, review) {
                    var chatId = review.inbox_message_key;
                    if (chatId) {
                        reviewMessages[chatId] = review;
                        if (reviewMessageRequests[chatId]) {
                            addActionsToMessage(chatId, review);
                            delete reviewMessageRequests[chatId];
                        }
                    }
                });
            },
            error: sln.showAjaxError
        });
    };

    var reviewAction = function (reviewKey, ok) {
        if (ok) {
            publish(reviewKey, false);
        } else {
            sendReply(reviewKey);
        }
    };

    var publish = function (reviewKey) {
        sln.confirm(CommonTranslations.news_review_publish_this_news_item, function() {
            sln.call({
                url: '/common/news/review/publish',
                type: 'post',
                data: {
                    review_key: reviewKey,
                },
                success: function (data) {
                    if (data.errormsg && !data.success) {
                        var msg = CommonTranslations[data.errormsg] || data.errormsg;
                        sln.alert(msg, null, CommonTranslations.ERROR);
                    }
                    // should add the returned news item to news list?
                },
                error: sln.showAjaxError
            });
        });
    };

    var sendReply = function (reviewKey) {
        function sendMessage(message) {
            sln.call({
                url: '/common/news/review/reply',
                type: 'post',
                data: {
                    review_key: reviewKey,
                    message: message
                },
                success: function (data) {
                    if (!data.success) {
                        sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    }
                },
                error: sln.showAjaxError
            });
        }

        sln.inputBox(sendMessage, CommonTranslations.reason, CommonTranslations.SEND,
            CommonTranslations.news_review_not_ok, null, null, '', true,
            CommonTranslations.news_review_not_ok_fill_reason);
    };

    var getButtonGroup = function (review, onRight) {
        var group = $('<div class="btn-group custom-group"></div>').attr('review_key', review.key);

        var btnOk = $('<button action="ok" class="btn btn-large btn-success"><i class="fa fa-check"></i> ' + CommonTranslations['reservation-approve'] + '</button>').attr('key', review.key);
        var btnNotOk = $('<button action="notok" class="btn btn-large btn-warning"><i class="fa fa-times"></i> ' + CommonTranslations['reservation-decline'] + '</button>').attr('key', review.key);

        btnOk.click(function (event) {
            event.stopPropagation();
            reviewAction(review.key, true);
        });
        btnNotOk.click(function (event) {
            event.stopPropagation();
            reviewAction(review.key, false);
        });

        group.append(btnOk);
        group.append(btnNotOk);
        if (onRight) {
            group.addClass("pull-right");
        }
        return group;
    };

    var getActionsForReview = function (review) {
        var toolbar = $('<div class="btn-toolbar"></div>').attr('review_key', review.key);
        var group = getButtonGroup(review);
        toolbar.append(group);
        return toolbar;
    };

    var addActionsToMessage = function (chatId, review) {
        sln.setInboxActions(chatId, getActionsForReview(review));
    };

    var channelUpdates = function (data) {
        switch (data.type) {
            case 'solutions.common.news.review.update':
                loadReviewRequests();
                break;
            default:
                break;
        }
    };

    function newNewsReviewMessage(chatId) {
        var review = reviewMessages[chatId];
        if (review) {
            addActionsToMessage(chatId, review);
        } else {
            reviewMessageRequests[chatId] = chatId;
        }
    }

    sln.registerMsgCallback(channelUpdates);
    loadReviewRequests();
    sln.registerInboxActionListener("news_review", newNewsReviewMessage);

    var inboxReply = $('#inbox-reply');
    inboxReply.bind('message-details-loaded', function () {
        var parentMessageId = inboxReply.find('tbody > tr').first().attr('message_key');
        var review = reviewMessages[parentMessageId];
        var prevButtonGroup = inboxReply.find('.btn-toolbar .btn-group').last();
        if (prevButtonGroup.hasClass('custom-group"')) {
            prevButtonGroup.remove();
        }
        if (review) {
            var buttonGroup = getButtonGroup(review, true);
            inboxReply.find('.btn-toolbar .btn-group').last().after(buttonGroup);
        }
    });

});
