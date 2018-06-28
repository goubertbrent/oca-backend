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

$(function () {
    'use strict';
    var TMPL_HINT_SET_FACEBOOK_PAGE = '<div class="alert alert-info">'
        + '    <button id="set_facebook_page" type="button" class="btn btn-info pull-right">${CommonTranslations.SET_NOW}</button>' //
        + '    <h4>${CommonTranslations.HINT}</h4> ${CommonTranslations.SET_FACEBOOK_PAGE_AND_START_SHARING}'
        + '</div>';

    var ATTACHMENT_TEMPLATE = '{{each attachments}}'
        + ' <tr>'
        + '     <td><div class="span4">${$value.name}</div> <div class="btn-group pull-right">'
        + '         <a href="${$value.download_url}" target="_blank"> <button action="link" class="btn"><i class="fa fa-external-link"></i></button></a>'
        + '         <button key="${$index}" download_url="${$value.download_url}" action="delete" class="btn"><i class="fa fa-trash"></i></button>'
        + '     </div></td>' //
        + ' </tr>' //
        + '{{/each}}';

    var URL_TEMPLATE = '{{each urls}}'
        + ' <tr>'
        + '     <td><div class="span4">${$value.name}</div> <div class="btn-group pull-right">'
        + '         <a href="${$value.url}" target="_blank"> <<button action="link" class="btn"><i class="fa fa-external-link"></i></button></a>'
        + '         <button key="${$index}" url="${$value.url}" action="delete" class="btn"><i class="fa fa-trash"></i></button>'
        + '     </div></td>' //
        + ' </tr>' //
        + '{{/each}}';

    var GENDER_MALE_OR_FEMALE = "MALE_OR_FEMALE";

    var totalReachData;
    var targetAudienceEnabled = false;
    var targetAudienceMinAge = 0;
    var targetAudienceMaxAge = 0;
    var targetAudienceGender = GENDER_MALE_OR_FEMALE;

    var DEFAULT_TIME_EPOCH = 20 * 3600;
    var broadcastTimeEpoch = DEFAULT_TIME_EPOCH;

    var msgAttachments = [];
    var msgUrls = [];

    var elemPageMessage = $('#broadcast_page_message'),
        elemInputBroadcastTarget = $('#input-broadcast-target'),
        elemTargetAudience = $('#target_audience');

    var elemBroadcastOnTwitter = $("#broadcast_message_on_twitter").find("input");

    init();

    var numberOnlyCheckKeyup = function (e) {
        if (/\D/g.test($(this).val())) {
            $(this).val($(this).val().replace(/\D/g, ''));
        }
        if (!$(this).val()) {
            if ($(this).attr("id") == "age-min") {
                $(this).val('0');
            } else {
                $(this).val('100');
            }
        }
        displayReach();
    };

    var plusClick = function (elem) {
        return function (e) {
            elem.val(parseInt(elem.val()) + 1);
            displayReach();
        };
    };
    var minClick = function (elem) {
        return function (e) {
            var current = parseInt(elem.val());
            if (current > 0)
                elem.val(current - 1);
            else
                elem.val(0);
            displayReach();
        };
    };

    var attachmentUploadedHandlers = [];

    function addAttachment() {
        var html = $.tmpl(templates.addattachment, {
            t: CommonTranslations,
            website: false
        });

        var modal = sln.createModal(html, function () {
            $('#attachmentName').focus().select();
        });

        $('button[action="submit"]', modal).click(function () {
            var fileInput = $('#attachment-files', modal)[0];
            if(fileInput.files[0] === undefined) {
                sln.alert(T('please_select_attachment'), null, CommonTranslations.ERROR);
                return;
            }
            sln.showProcessing(CommonTranslations.UPLOADING_TAKE_A_FEW_SECONDS);
            var formElement = document.querySelector('#attachment-form');
            var request = new XMLHttpRequest();
            request.open('POST', '/common/broadcast/attachment/upload');
            request.send(new FormData(formElement));
        });
    }

    function registerAttachmentUploadedHandler(handler) {
        if (attachmentUploadedHandlers.indexOf(handler) === -1) {
            attachmentUploadedHandlers.push(handler);
        }
    }

    function attachmentUploaded(url, name) {
        // Hide the modal, add attachment
        $('#addAttachmentModal').modal('hide');

        $.each(attachmentUploadedHandlers, function(i, handler) {
            handler(url, name);
        });

        msgAttachments.push({
            download_url: url,
            name: name
        });
        displayAttachments();
    }

    function attachmentUploadFailed(error) {
        $('#addAttachmentModal').modal('hide');
        sln.alert(error, null, CommonTranslations.ERROR);
    }

    var attachmentDeletePressed = function () {
        var key = $(this).attr("key");
        msgAttachments.splice(key, 1);
        displayAttachments();
    };

    var displayAttachments = function () {
        if (msgAttachments.length > 0) {
            var attachments = $("#attachments").find("tbody");
            var html = $.tmpl(ATTACHMENT_TEMPLATE, {
                attachments: msgAttachments
            });
            attachments.empty().append(html);
            $('#attachments').show().find('button[action="delete"]').click(attachmentDeletePressed);
        } else {
            $("#attachments").hide();
        }
    };

    var addUrl = function () {
        var html = $.tmpl(templates.addattachment, {
            t: CommonTranslations,
            website: true
        });

        var modal = sln.createModal(html, function () {
            $('#attachmentUrl').focus();
        });
        $('button[action="submit"]', modal).prop('disabled', true);

        sln.configureDelayedInput($('#attachmentUrl', modal), function () {
            $('#attachmentUrl', modal).removeClass("success");
            $('#attachmentUrl', modal).removeClass("error");
            $("#attachment-error", modal).hide();
            $("#attachment-validating", modal).show();
            $('button[action="submit"]', modal).prop('disabled', true);

            sln.call({
                url: "/common/broadcast/validate/url",
                type: "POST",
                data: {
                    data: JSON.stringify({
                        url: $('#attachmentUrl', modal).val()
                    })
                },
                success: function (data) {
                    $("#attachment-validating", modal).hide();
                    $('#attachmentUrl', modal).val(data.url);
                    if (!data.success) {
                        $("#attachment-error", modal).show();
                        $("#attachment-error-msg", modal).html(sln.htmlize(data.errormsg));
                        $('#attachmentUrl', modal).addClass("error");
                        return;
                    }
                    $('#attachmentUrl', modal).addClass("success");
                    $('button[action="submit"]', modal).prop('disabled', false);
                },
                error: sln.showAjaxError
            });
        });

        $('button[action="submit"]', modal).click(
            function () {
                var url = $("#attachmentUrl", modal).val();
                var urlName = $("#attachmentName", modal).val();

                var urlValid = sln.validate($("#urlerror", modal), $("#attachmentUrl", modal),
                    CommonTranslations.URL_IS_REQUIRED);
                var nameValid = sln.validate($("#nameerror", modal), $("#attachmentName", modal),
                    CommonTranslations.NAME_IS_REQUIRED);

                if (!(urlValid && nameValid))
                    return;

                msgUrls.push({
                    url: url,
                    name: urlName
                });
                displayUrls();
                modal.modal('hide');
            });
    };

    var urlDeletePressed = function () {
        var key = $(this).attr("key");
        msgUrls.splice(key, 1);
        displayUrls();
    };

    var displayUrls = function () {
        if (msgUrls.length > 0) {
            $("#urls").show();
            var urls = $("#urls tbody");
            var html = $.tmpl(URL_TEMPLATE, {
                urls: msgUrls
            });
            urls.empty().append(html);
            $('#urls button[action="delete"]').click(urlDeletePressed);
        } else {
            $("#urls").hide();
        }
    };

    var defaultBroadcastChecks = function (bt, message) {
        if (!bt.val()) {
            sln.alert(CommonTranslations.BROADCAST_TYPE_REQUIRED);
            return false;
        }

        if (!message.val()) {
            sln.alert(CommonTranslations.PLEASE_ENTER_A_MESSAGE);
            return false;
        }

        var checkTargetAudience = $('#configure_target_audience input');
        if (checkTargetAudience.prop('checked')) {
            targetAudienceEnabled = true;
            targetAudienceMinAge = parseInt($("#age_min").val());
            targetAudienceMaxAge = parseInt($("#age_max").val());
            targetAudienceGender = $("#gender").val();

            if (targetAudienceMinAge > targetAudienceMaxAge) {
                sln.alert(CommonTranslations.AGE_MIN_MAX_LESS);
                return false;
            }
        } else {
            targetAudienceEnabled = false;
            targetAudienceMinAge = 0;
            targetAudienceMaxAge = 0;
            targetAudienceGender = GENDER_MALE_OR_FEMALE;
        }
        return true;
    };

    var broadcast = function () {
        var bt = $('#broadcast input[name=broadcast_types]:checked');
        var message = $('#broadcast #broadcast_message');
        var allOk = defaultBroadcastChecks(bt, message);
        if (!allOk)
            return;

        var twitterEnabled = elemBroadcastOnTwitter.prop('checked');
        if (twitterEnabled) {
            var twitterUsername = elemBroadcastOnTwitter.val();
            if (twitterUsername === "") {
                sln.alert(CommonTranslations.TWITTER_PAGE_REQUIRED);
                return;
            }
        }

        var checkFacebook = $('#broadcast #broadcast_message_on_facebook input');
        if (checkFacebook.prop('checked')) {
            var facebookPageId = $("#broadcast_message_on_facebook input").val();
            if (facebookPageId == "") {
                sln.alert(CommonTranslations.FACEBOOK_PLACE_REQUIRED);
                return;
            } else {
                FB.login(function (response) {
                    if (response.authResponse) {
                        var fbAccessToken = response.authResponse.accessToken;
                        var userId = response.authResponse.userID;
                        var params = "/" + userId + "/accounts?access_token=" + fbAccessToken;
                        FB.api(params,
                            function (response) {
                                if (response && !response.error) {
                                    var userIsAdmin = false;
                                    var userHasModeratePermissions = false;
                                    for (var i = 0; i < response.data.length; i++) {
                                        if (response.data[i].id === facebookPageId) {
                                            userIsAdmin = true;
                                            if (response.data[i].perms.indexOf("MODERATE_CONTENT") > 0) {
                                                userHasModeratePermissions = true;
                                            }
                                            break;
                                        }
                                    }
                                    if (userIsAdmin && userHasModeratePermissions) {
                                        var fbRequest = {message: message.val(), access_token: fbAccessToken};
                                        if (msgAttachments.length > 0) {
                                            fbRequest["link"] = msgAttachments[0].download_url;
                                        } else if (msgUrls.length > 0) {
                                            fbRequest["link"] = msgUrls[0].download_url;
                                        }

                                        FB.api("/" + facebookPageId + "/feed", "post", fbRequest,
                                            function (response) {
                                                console.log("response broadcast", response, fbRequest);
                                                if (response && !response.error) {
                                                    doBroadcastToRogerthat(bt.val(), message.val(), true, targetAudienceEnabled,
                                                        targetAudienceMinAge, targetAudienceMaxAge, targetAudienceGender,
                                                        msgAttachments, msgUrls, null, twitterEnabled);
                                                }
                                                else {
                                                    sln.confirm(sln.htmlize(CommonTranslations.FACEBOOK_VISIBILITY_APP)
                                                            .replace("%(fb_url)s", '<a href="https://www.facebook.com/settings?tab=applications" target="_blank">https://www.facebook.com/settings?tab=applications</a>'),
                                                        function () {
                                                            // Retry
                                                            broadcast();
                                                        }, function () {
                                                            // Continue
                                                            doBroadcastToRogerthat(bt.val(), message.val(), false, targetAudienceEnabled,
                                                                targetAudienceMinAge, targetAudienceMaxAge, targetAudienceGender,
                                                                msgAttachments, msgUrls, null, twitterEnabled);
                                                        }, CommonTranslations.RETRY, CommonTranslations.CONTINUE_WITHOUT_FACEBOOK_POST, CommonTranslations.INSUFFICIENT_PERMISSIONS);
                                                }
                                            }
                                        );
                                    }
                                    else {
                                        if (!userIsAdmin) {
                                            sln.alert(CommonTranslations.FACEBOOK_ADMIN_REQUIRED);
                                            // or you didn't grant us permissions
                                        }
                                        else if (!userHasModeratePermissions) {
                                            sln.alert(CommonTranslations.FACEBOOK_ADMIN_PERMISSIONS_REQUIRED);
                                        }
                                    }
                                }
                                else {
                                    // Error occurred while getting accounts
                                    doBroadcastToRogerthat(bt.val(), message.val(), false, targetAudienceEnabled,
                                        targetAudienceMinAge, targetAudienceMaxAge, targetAudienceGender, msgAttachments, msgUrls, null, twitterEnabled);
                                }
                            }
                        );
                    } else {
                        // The person cancelled the login dialog
                        doBroadcastToRogerthat(bt.val(), message.val(), false, targetAudienceEnabled,
                            targetAudienceMinAge, targetAudienceMaxAge, targetAudienceGender, msgAttachments, msgUrls, null, twitterEnabled);
                    }
                }, {scope: 'manage_pages,publish_actions'});
            }
        } else {
            doBroadcastToRogerthat(bt.val(), message.val(), false, targetAudienceEnabled, targetAudienceMinAge,
                targetAudienceMaxAge, targetAudienceGender, msgAttachments, msgUrls, null, twitterEnabled);
        }
    };

    var to_epoch = function (textField) {
        return Math.floor(textField.data('datepicker').date.valueOf() / 1000);
    };

    var scheduleBroadcast = function () {
        var bt = $('#broadcast input[name=broadcast_types]:checked');
        var message = $('#broadcast #broadcast_message');
        var allOk = defaultBroadcastChecks(bt, message);
        if (!allOk)
            return;

        var html = $.tmpl(templates.broadcast_schedule, {
            header: CommonTranslations.SCHEDULE_BROADCAST,
            cancelBtn: CommonTranslations.CANCEL,
            submitBtn: CommonTranslations.SEND,
            CommonTranslations: CommonTranslations
        });

        $('#broadcast-time', html).timepicker({
            defaultTime: "20:00",
            showMeridian: false
        });
        broadcastTimeEpoch = DEFAULT_TIME_EPOCH;

        $('#broadcast-time', html).on('changeTime.timepicker', function (e) {
            broadcastTimeEpoch = e.time.hours * 3600 + e.time.minutes * 60;
        });

        var twitterEnabled = elemBroadcastOnTwitter.prop('checked');
        if (twitterEnabled) {
            var twitterUsername = elemBroadcastOnTwitter.val();
            if (twitterUsername == "") {
                sln.alert(CommonTranslations.TWITTER_PAGE_REQUIRED);
                return;
            }
        }

        var checkFacebook = $('#broadcast #broadcast_message_on_facebook input');
        if (checkFacebook.prop('checked')) {
            $("#broadcast-note", html).show();
        } else {
            $("#broadcast-note", html).hide();
        }

        $('.date', html).datepicker({
            format: sln.getLocalDateFormat()
        }).datepicker('setValue', sln.today());

        var modal = sln.createModal(html);

        $('button[action="submit"]', modal).click(
            function () {
                var selectDate = new Date(((to_epoch($("#broadcast-date", html))) + broadcastTimeEpoch) * 1000);
                var broadcastDate = {
                    year: selectDate.getFullYear(),
                    month: selectDate.getMonth() + 1,
                    day: selectDate.getDate(),
                    hour: selectDate.getHours(),
                    minute: selectDate.getMinutes()
                };
                modal.modal('hide');
                doBroadcastToRogerthat(bt.val(), message.val(), false, targetAudienceEnabled, targetAudienceMinAge,
                    targetAudienceMaxAge, targetAudienceGender, msgAttachments, msgUrls, broadcastDate,
                    twitterEnabled);
            });
    };

    var lastDisplayReachInvocation = 0;
    var displayReach = function () {
        lastDisplayReachInvocation = new Date().getTime();
        $("#broadcastReachCalculation").show();
        $("#broadcastReach").hide();
        setTimeout(function () {
            if ((new Date().getTime() - lastDisplayReachInvocation) < 1000)
                return;
            var targetAudienceMinAge = null;
            var targetAudienceMaxAge = null;
            var targetAudienceGender = null;
            if (targetAudienceEnabled) {
                targetAudienceMinAge = parseInt($("#age_min").val());
                targetAudienceMaxAge = parseInt($("#age_max").val());
                targetAudienceGender = $("#gender").val();
            }
            var broadcastToAllLocations = $("#broadcast_message_to_all_locations input").prop('checked');
            sln.call({
                url: "/common/broadcast/subscribed",
                type: "get",
                data: {
                    broadcast_type: $("input[type='radio'][name='broadcast_types']:checked").val(),
                    min_age: targetAudienceMinAge,
                    max_age: targetAudienceMaxAge,
                    gender: targetAudienceGender,
                    broadcast_to_all_locations: broadcastToAllLocations
                },
                success: function (data) {
                    totalReachData = data;
                    $("#broadcastReached").text(totalReachData.subscribed_users);
                    $("#broadcastTotal").text(totalReachData.total_users);
                    $("#broadcastReachCalculation").hide();
                    $("#broadcastReach").show();
                },
                error: sln.showAjaxError
            });
        }, 1000);
    };

    function renderBroadcastTypes() {
        Requests.getBroadcastOptions().then(function (broadcastOptions) {
            var html = $.tmpl(templates.broadcast_types, {
                broadcast_types: broadcastOptions.broadcast_types
            });
            $("#broadcast_types").html(html);
            $("#broadcast").find("input[name=broadcast_types]:radio").change(function () {
                displayReach();
            });
            modules.settings.renderBroadcastSettings(); // Defined in sln-settings
        });
    }

    $(document).on("click", '#scheduled_broadcasts tbody button[action="delete"]', function () {
        var key = $(this).attr("key");

        sln.call({
            url: "/common/broadcast/scheduled/delete",
            type: "POST",
            data: {
                data: JSON.stringify({
                    key: key
                })
            },
            success: function (data) {
                if (!data.success) {
                    sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    return;
                }
                loadScheduledBroadcasts();
            }
        });
    });

    var loadScheduledBroadcasts = function () {
        sln.call({
            url: "/common/broadcast/scheduled/load",
            type: "GET",
            success: function (data) {
                $("#scheduled_broadcasts").toggle(!!data.length);
                if (data.length !== 0) {
                    $.each(data, function (i, d) {
                        var broadcastDate = new Date(d.scheduled.year, d.scheduled.month - 1, d.scheduled.day,
                            d.scheduled.hour, d.scheduled.minute);

                        d.date = sln.parseDateToDateTime(broadcastDate);
                        d.htmlMessage = sln.htmlize(d.message);
                    });

                    var html = $.tmpl(templates.broadcast_schedule_items, {
                        data: data,
                        CommonTranslations: CommonTranslations
                    });

                    $("#scheduled_broadcasts").find("tbody").html(html);
                }
            }
        });
    };

    function doBroadcastToRogerthat(broadcast_type, message, broadcast_on_facebook, target_audience_enabled,
                                    target_audience_min_age, target_audience_max_age, target_audience_gender, msg_attachments, msg_urls,
                                    broadcast_date, broadcast_on_twitter) {
        sln.showProcessing(CommonTranslations.SENDING_DOT_DOT_DOT);

        var broadcastToAllLocations = $("#broadcast_message_to_all_locations input").prop('checked');

        sln.call({
            url: "/common/broadcast",
            type: "POST",
            data: {
                data: JSON.stringify({
                    broadcast_type: broadcast_type,
                    message: message,
                    broadcast_on_facebook: broadcast_on_facebook,
                    target_audience_enabled: target_audience_enabled,
                    target_audience_min_age: target_audience_min_age,
                    target_audience_max_age: target_audience_max_age,
                    target_audience_gender: target_audience_gender,
                    msg_attachments: msg_attachments,
                    msg_urls: msg_urls,
                    broadcast_date: broadcast_date,
                    broadcast_on_twitter: broadcast_on_twitter,
                    broadcast_to_all_locations: broadcastToAllLocations
                })
            },
            success: function (data) {
                sln.hideProcessing();
                if (data.success) {
                    $('#broadcast #broadcast_message').val('');
                    $('#broadcast input[name=broadcast_types]:checked').prop('checked', false);
                    $('#broadcast_message_on_facebook input').prop('checked', broadcast_on_facebook);
                    $("#broadcast_message_to_all_locations input").prop('checked', false);
                    $('#configure_target_audience input').prop('checked', false);
                    elemTargetAudience.css("display", "none");
                    targetAudienceEnabled = false;
                    $("#broadcastReached").text(0);
                    $("#broadcastTotal").text(0);
                    msgAttachments = [];
                    msgUrls = [];
                    totalReachData = undefined;
                    displayAttachments();
                    displayUrls();
                    $("#char_count").text(0);
                    elemBroadcastOnTwitter.removeProp("disabled");
                    elemBroadcastOnTwitter.attr("_status", "enabled");
                    $("#twitter_disabled_reason_chars").hide();

                    if (broadcast_date === null) {
                        sln.alert(CommonTranslations.BROADCAST_SEND_SUCCESSFULLY, null, CommonTranslations.SUCCESS);
                    } else {
                        sln.alert(CommonTranslations.BROADCAST_PLANNED_SUCCESSFULLY, null, CommonTranslations.SUCCESS);
                    }
                } else {
                    sln.alert(data.errormsg.replace("\n", "<br><br>"), null, CommonTranslations.FAILED);
                }
            },
            error: sln.showAjaxError
        });
    }

    function channelUpdates(data) {
        switch (data.type) {
            case 'solutions.common.settings.facebookPageChanged':
                $("#broadcast_message_on_facebook").find("input").val(data.facebook_page || '');
                $(".sln-broadcast-hint").toggle(!!data.facebook_page);
                break;
            case 'solutions.common.settings.updates_pending':
                if (!data.updatesPending) {
                    Requests.getBroadcastOptions({cached: false}).then(function () {
                    });
                }
                break;
            case 'solutions.common.broadcast.scheduled.updated':
                loadScheduledBroadcasts();
                break;
            case 'solutions.common.twitter.updated':
                $("#broadcast_message_on_twitter").find("input").val(data.username ? data.username : "");
                break;
            case 'solutions.common.broadcast.attachment.upload.success':
                sln.hideProcessing();
                attachmentUploaded(data.url, data.name);
                break;
            case 'solutions.common.broadcast.attachment.upload.failed':
                sln.hideProcessing();
                attachmentUploadFailed(data.message);
                break;
        }
    }

    function setFacebookPage() {
        $("#topmenu").find("li").removeClass("active");
        var li = $("li[menu=settings]").addClass("active");

        $("div.page").hide();
        $("div#" + li.attr("menu")).show();

        var new_position = $('.sln-set-facebook-place').offset();
        if (new_position === undefined) {
            return;
        }
        window.scrollTo(new_position.left, new_position.top);
    }

    $("#set_facebook_page").click(setFacebookPage);
    $("#age_min").keyup(numberOnlyCheckKeyup);
    $("#age_max").keyup(numberOnlyCheckKeyup);

    $("#age_max_plus").click(plusClick($("#age_max")));
    $("#age_min_plus").click(plusClick($("#age_min")));
    $("#age_max_min").click(minClick($("#age_max")));
    $("#age_min_min").click(minClick($("#age_min")));

    $('#broadcast button#broadcast-button').click(broadcast);
    $('#broadcast button#schedule-broadcast-button').click(scheduleBroadcast);

    $('#configure_target_audience').find('input').change(function () {
        targetAudienceEnabled = !!this.checked;
        elemTargetAudience.toggle(targetAudienceEnabled);
        displayReach();
    });

    $("#broadcast_message_to_all_locations input").change(function () {
        displayReach();
    });

    $("#gender").change(displayReach);
    $("#add_attachment").click(addAttachment);
    $("#add_url").click(addUrl);

    $("li[menu=broadcast] a").click(function () {
        displayAttachments();
        displayUrls();
    });

    $("#broadcast_message").on(
        "keyup change",
        function () {
            var l = $("#broadcast_message").val().length;
            $("#char_count").text(l);
            var _previous_status = elemBroadcastOnTwitter .attr("_status");
            if (l > 140) {
                if (_previous_status != "disabled") {
                    elemBroadcastOnTwitter .prop("disabled", "disabled");
                    elemBroadcastOnTwitter .attr("_backup_selected",
                        elemBroadcastOnTwitter .prop("checked"));
                    elemBroadcastOnTwitter .prop("checked", false);
                    elemBroadcastOnTwitter .attr("_status", "disabled");
                    $("#twitter_disabled_reason_chars").show();
                }
            } else {
                if (_previous_status != "enabled") {
                    elemBroadcastOnTwitter .removeProp("disabled");
                    var twB = elemBroadcastOnTwitter .attr("_backup_selected");
                    if (twB == "true") {
                        elemBroadcastOnTwitter .prop("checked", true);
                    } else if (twB == "false") {
                        elemBroadcastOnTwitter .prop("checked", false);
                    }

                    elemBroadcastOnTwitter .attr("_status", "enabled");
                    $("#twitter_disabled_reason_chars").hide();
                }
            }
        });

    function init() {
        ROUTES['broadcast'] = router;
        modules.broadcast = {
            addAttachment: addAttachment,
            registerAttachmentUploadedHandler: registerAttachmentUploadedHandler,
        };

        elemInputBroadcastTarget.change(displayReach);
        sln.registerMsgCallback(channelUpdates);

        if (!modules.menu) {
            modules.menu = {
                loadMenu: returnNothing
            };
        }
        if (!modules.sandwich) {
            modules.sandwich = {
                getSandwichSettings: returnNothing
            };
        }
    }

    function returnNothing() {
        return Promise.resolve();
    }

    function router(urlHash) {
        var page = urlHash[1];
        Requests.getBroadcastOptions().then(function (broadcastOptions) {
            // determine what to show depending if news is enabled or not
            if (!broadcastOptions.news_enabled) {
                elemPageMessage.show();
                renderBroadcastTypes(broadcastOptions);
                var html_hint = $.tmpl(TMPL_HINT_SET_FACEBOOK_PAGE, {
                    CommonTranslations: CommonTranslations
                });

                $('.sln-broadcast-hint').html(html_hint);
                if (!$('#broadcast_message_on_facebook').find('input').val()) {
                    $('.sln-broadcast-hint').hide();
                }
                loadScheduledBroadcasts();
            }
        });
    }

});
