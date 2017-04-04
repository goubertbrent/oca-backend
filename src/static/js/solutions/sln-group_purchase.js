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
    var groupPurhcaseEnabled = true;
    
    var TMPL_SET_GROUP_PURCHASE_VISIBLE = '<div class="btn-group">'
        + '      <button class="btn btn-success" id="groupPurchaseVisible">' + CommonTranslations.VISIBLE
        + '</button>' + '      <button class="btn" id="groupPurchaseInvisible">&nbsp;</button>' + '</div>';

    var channelUpdates = function(data) {
        if (data.type == "rogerthat.system.channel_connected") {
            loadGroupPurchases();
            loadSettings();
        } else if (data.type == "solutions.common.group_purchase.update") {
            loadGroupPurchases();
        }
    };
    
    $('#create_group_purchase').click(function() {
        initGroupPurchaseModal();

        setTimeout(function() {
            $("#groupPurchaseModal .modal-body").scrollTop(0);
        }, 300);
    });

    $('#contact_group_purchase_subscriptions').click(function() {
        var gp = $(this).data("group_purchase");
        $("#groupPurchaseSubscriptionsModal").modal('hide');
        sln.inputBox(function(message) {
            sln.call({
                url : "/common/group_purchase/broadcast",
                type : "POST",
                data : {
                    data : JSON.stringify({
                        group_purchase_id : parseInt(gp.id),
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
        }, CommonTranslations.CONTACT_PARTICIPANTS, null, CommonTranslations.TITLE + ": " + gp.title + "<br>" + CommonTranslations.UNITS + ": " + gp.units + "<br>" + CommonTranslations.PRICE_P_UNIT + ": " + gp.unit_price_in_euro);
    });

    $('#add_group_purchase_subscriptions').click(function() {
        var gp = $(this).data("group_purchase");
        $("#groupPurchaseSubscriptionsModal").modal('hide');
        $("#add_particimant_group_purchase_subscriptions").data("group_purchase", gp);
        $("#group_purchase_participant_name").val("");
        $("#group_purchase_participant_units").val(1);
    });

    $('#add_particimant_group_purchase_subscriptions').click(function() {
        var gp = $(this).data("group_purchase");

        var name = $("#group_purchase_participant_name").val();
        var units = $("#group_purchase_participant_units").val();
        var units_f = parseInt(units);

        var errorlist = [];
        if (!name) {
            errorlist.push("<li>" + CommonTranslations.NAME_IS_REQUIRED + "</li>");
        }
        if (isNaN(units_f)) {
            errorlist.push("<li>" + CommonTranslations.TOTAL_UNITS_IS_AN_INVALID_NUMBER + "</li>");
        }

        if (errorlist.length > 0) {
            errorlist.splice(0, 0, "<ul>");
            errorlist.push("</ul>");
            sln.alert(errorlist.join(""), null, CommonTranslations.ERROR);
            return;
        }

        if (units_f < 1) {
            sln.alert(CommonTranslations.YOU_NEED_TO_PURCHASE_AT_LEAST_1_UNIT, null, CommonTranslations.ERROR);
            return;
        }

        if ((gp.units_available - units_f) < 0) {
            sln.alert(CommonTranslations.THERE_ARE_NOT_ENOUGH_UNITS, null, CommonTranslations.ERROR);
            return;
        }

        sln.call({
            url : "/common/group_purchase/subscriptions/add",
            type : "POST",
            data : {
                data : JSON.stringify({
                    group_purchase_id : parseInt(gp.id),
                    name: name,
                    units: units_f
                })
            },
            success : function(data) {
                if (!data.success) {
                    return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
                $("#groupPurchaseSubscriptionsAddModal").modal('hide');
            },
            error : sln.showAjaxError
        });
    });

    var loadGroupPurchases = function() {
        sln.call({
            url : "/common/group_purchase/load",
            type : "GET",
            success : function(data) {
                var groupPurchase = $("#group_purchase #group_purchase_table tbody");
                $.each(data, function(i, o) {
                    o.time_from_str = sln.formatDate(o.time_from, true, false, false);
                    o.time_until_str = sln.formatDate(o.time_until, true, false, false);
                });
                var now = (new Date().getTime()) / 1000;

                data.sort(function(a, b) {
                    if (now > a.time_until || now > b.time_until) {
                        return a.time_until - b.time_until;
                    }
                    if((a.time_from - b.time_from) != 0)
                        return a.time_from - b.time_from;
                    if((a.time_until - b.time_until) != 0)
                        return a.time_until - b.time_until;
                    return sln.caseInsensitiveStringSort(a.title, b.title);
                });
                var html = $.tmpl(templates.group_purchase, {
                    group_purchases : data,
                    CommonTranslations : CommonTranslations,
                    CURRENCY: CURRENCY
                });
                groupPurchase.empty().append(html);

                $.each(data, function(i, o) {
                   $("#"+ o.id).data("group_purchase", o);
                });

                $('#group_purchase button[action="edit"]').click(function() {
                    var groupPurchaseId = $(this).attr("group_purchase_id");
                    var gp = $("#" + groupPurchaseId).data("group_purchase");
                    initGroupPurchaseModal(gp);

                    setTimeout(function() {
                        $("#groupPurchaseModal .modal-body").scrollTop(0);
                    }, 300);
                });

                $('#group_purchase button[action="delete"]').click(function() {
                    var groupPurchaseId = $(this).attr("group_purchase_id");
                    sln.confirm(CommonTranslations.GROUP_PURCHASE_DELETE_CONFIRMATION, function() {
                        sln.call({
                            url : "/common/group_purchase/delete",
                            type : "POST",
                            data : {
                                data : JSON.stringify({
                                    group_purchase_id : parseInt(groupPurchaseId)
                                })
                            },
                            success : function(data) {
                                if (!data.success) {
                                    return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                                }
                                fadeOutMessageAndUpdateBadge(groupPurchaseId);
                            },
                            error : sln.showAjaxError
                        });
                    });
                });

                $('#group_purchase button[action="subscriptions"]').click(function() {
                    var groupPurchaseId = $(this).attr("group_purchase_id");
                    var gp = $("#" + groupPurchaseId).data("group_purchase");

                    $("#contact_group_purchase_subscriptions").data("group_purchase", gp);
                    $("#add_group_purchase_subscriptions").data("group_purchase", gp);

                    var groupPurchaseSubscriptions = $("#group_purchase #group_purchase_subscriptions_table tbody");

                    $.each(gp.subscriptions, function(i, o) {
                        o.time_str = sln.formatDate(o.timestamp, true, false, false);
                    });

                    gp.subscriptions.sort(function(a, b) {
                        return b.timestamp - a.timestamp;
                    });

                    var html = $.tmpl(templates.group_purchase_subscriptions, {
                        group_purchases_subscriptions : gp.subscriptions,
                        group_purchase_id : gp.id
                    });
                    groupPurchaseSubscriptions.empty().append(html);
                });

                $('.sln-group-purchase-badge').text(data.length || '');
                sln.resize_header();
            },
            error : sln.showAjaxError
        });
    };

    var initGroupPurchaseModal = function(gp) {
        $('#group_purchase_time_from_time').timepicker({
            defaultTime : "18:00",
            showMeridian : false
        });

        $('#group_purchase_time_until_time').timepicker({
            defaultTime : "20:00",
            showMeridian : false
        });
        
        var p = $('#group_purchase_picture');
        p.replaceWith( p = p.clone( true ) );

        if (gp === undefined) {
            $('#group_purchase_picture_existing img').attr('src', '');
            $('#group_purchase_picture_existing').hide();
            $("#groupPurchaseModallLabel").text(CommonTranslations.CREATE_GROUP_PURCHASE);
            $("#save_group_purchase").data("group_purchase", null);
            $("#group_purchase_title").val("");
            $("#group_purchase_description").val("");
            $("#group_purchase_units").val(20);
            $("#group_purchase_units_price").val(4.99);
            $("#group_purchase_units_description").val("");
            $("#group_purchase_units_min").val(1);
            $("#group_purchase_units_max").val(0);
            $("#group_purchase_units_max_enabled").prop('checked', false);

            var today = sln.today();
            $('#group_purchase_time_from_date').datepicker({
                format : sln.getLocalDateFormat()
            }).datepicker('setValue',today);

            $('#group_purchase_time_until_date').datepicker({
                format : sln.getLocalDateFormat()
            }).datepicker('setValue', today.setDate(today.getDate() + 1));

        } else {
            if (gp.picture) {
                $('#group_purchase_picture_existing').show();
                $("#group_purchase_picture_existing img").attr('src', gp.picture);
                $("#group_purchase_picture_existing button").click(function() {
                    $("#group_purchase_picture_existing img").attr('src', '');
                    $("#group_purchase_picture_existing").hide();
                });
                $('#group_purchase_picture').change(function() {
                    $('#group_purchase_picture_existing img').attr('src', '');
                    $('#group_purchase_picture_existing').hide();
                });
            } else {
                $('#group_purchase_picture_existing img').attr('src', '');
                $('#group_purchase_picture_existing').hide();
            }
            $("#groupPurchaseModallLabel").text(CommonTranslations.UPDATE_GROUP_PURCHASE);
            $("#save_group_purchase").data("group_purchase", gp);
            $("#group_purchase_title").val(gp.title);
            $("#group_purchase_description").val(gp.description);
            $("#group_purchase_units").val(gp.units);
            $("#group_purchase_units_price").val(gp.unit_price / 100);
            $("#group_purchase_units_description").val(gp.unit_description);
            $("#group_purchase_units_min").val(gp.min_units_pp);
            $("#group_purchase_units_max").val(gp.max_units_pp ? gp.max_units_pp : 0);
            $("#group_purchase_units_max_enabled").prop('checked', gp.max_units_pp ? true : false);

            var startDate = new Date(gp.time_from * 1000);
            $('#group_purchase_time_from_date').datepicker({
                format : sln.getLocalDateFormat()
            }).datepicker('setValue', new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate()));
            var eventStartEpoch = parseInt(startDate.getHours() * 3600 + startDate.getMinutes() * 60);
            $("#group_purchase_time_from_time").timepicker('setTime', sln.intToTime(eventStartEpoch));

            var endDate = new Date(gp.time_until * 1000);
            $('#group_purchase_time_until_date').datepicker({
                format : sln.getLocalDateFormat()
            }).datepicker('setValue', new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate()));
            var eventEndEpoch = parseInt(endDate.getHours() * 3600 + endDate.getMinutes() * 60);
            $("#group_purchase_time_until_time").timepicker('setTime', sln.intToTime(eventEndEpoch));
        }
    };

    $("#save_group_purchase").click(function() {
        var gp = $(this).data("group_purchase");

        var title = $("#group_purchase_title").val();
        var description = $("#group_purchase_description").val();
        var units = $("#group_purchase_units").val();
        var unit_price = $("#group_purchase_units_price").val();
        var unit_description = $("#group_purchase_units_description").val();
        var unit_min = $("#group_purchase_units_min").val();
        var unit_max = $("#group_purchase_units_max").val();

        var unit_max_enabled = $("#group_purchase_units_max_enabled").is(':checked');
        var time_from_date = Math.floor($("#group_purchase_time_from_date").data('datepicker').date.valueOf() / 1000);
        var fromPicker = $("#group_purchase_time_from_time").data("timepicker");
        var time_from_time = fromPicker.hour * 3600 + fromPicker.minute * 60;
        var time_from = time_from_date + time_from_time;

        var time_until_date = Math.floor($("#group_purchase_time_until_date").data('datepicker').date.valueOf() / 1000);
        var untilPicker = $("#group_purchase_time_until_time").data("timepicker");
        var time_until_time = untilPicker.hour * 3600 + untilPicker.minute * 60;
        var time_until = time_until_date + time_until_time;

        var now_ = sln.nowUTC();

        var errorlist = [];
        if (!title) {
            errorlist.push("<li>" + CommonTranslations.TITLE_IS_REQUIRED + "</li>");
        }
        if (!description) {
            errorlist.push("<li>" + CommonTranslations.DESCRIPTION_IS_REQUIRED + "</li>");
        }
        if (!units) {
            errorlist.push("<li>" + CommonTranslations.TOTAL_NUMBER_OF_UNITS_IS_REQUIRED + "</li>");
        }
        if (!unit_price) {
            errorlist.push("<li>" + CommonTranslations.UNIT_PRICE_IS_REQUIRED + "</li>");
        }
        if (!unit_description) {
            errorlist.push("<li>" + CommonTranslations.UNIT_DESCRIPTION_IS_REQUIRED + "</li>");
        }
        if (!unit_min) {
            errorlist.push("<li>" + CommonTranslations.MINIMUM_UNITS_IS_REQUIRED + "</li>");
        }
        if (unit_max_enabled && !unit_max) {
            errorlist.push("<li>" + CommonTranslations.MAXIMUM_UNITS_IS_REQUIRED + "</li>");
        }
        if (time_from >= time_until) {
            errorlist.push("<li>" + CommonTranslations.TIME_START_END_SMALLER + "</li>");
        }
        if (time_until <= now_) {
            errorlist.push("<li>" + CommonTranslations.YOU_CANNOT_MAKE_A_GROUP_PURCHASE_IN_THE_PAST + "</li>");
        }

        if (errorlist.length > 0) {
            errorlist.splice(0, 0, "<ul>");
            errorlist.push("</ul>");
            sln.alert(errorlist.join(""), null, CommonTranslations.ERROR);
            return;
        }
         

        var units_f = parseInt(units);
        var unit_price_f = parseFloat(unit_price);
        var unit_min_f = parseInt(unit_min);
        var unit_max_f = 0;
        if (unit_max_enabled)
            unit_max_f = parseInt(unit_max);

        errorlist = [];
        if (isNaN(units_f)) {
            errorlist.push("<li>" + CommonTranslations.UNITS_IS_AN_INVALID_NUMBER + "</li>");
        }
        if (isNaN(unit_price_f)) {
            errorlist.push("<li>" + CommonTranslations.UNIT_PRICE_IS_AN_INVALID_NUMBER + "</li>");
        }
        if (isNaN(unit_min_f)) {
            errorlist.push("<li>" + CommonTranslations.MINIMUM_UNITS_IS_AN_INVALID_NUMBER + "</li>");
        }
        if (isNaN(unit_max_f)) {
            errorlist.push("<li>" + CommonTranslations.MAXIMUM_UNITS_IS_AN_INVALID_NUMBER + "</li>");
        }

        if (errorlist.length > 0) {
            errorlist.splice(0, 0, "<ul>");
            errorlist.push("</ul>");
            sln.alert(errorlist.join(""), null, CommonTranslations.ERROR);
            return;
        }

        unit_price_f = Math.round(unit_price_f*100);
        sln.showProcessing(CommonTranslations.SAVING_DOT_DOT_DOT);
        var picture = null;
        var new_picture = false;
        var post = function() {
            var groupPurchaseTO = {
                    id: gp ? gp.id : null,
                    title: title,
                    description: description,
                    picture: picture,
                    new_picture: new_picture,
                    units: units_f,
                    unit_description: unit_description,
                    unit_price: unit_price_f,
                    unit_price_in_euro: null,
                    min_units_pp: unit_min_f,
                    max_units_pp: (unit_max_enabled ? unit_max_f : null),
                    time_from: time_from,
                    time_until: time_until
                };
                console.log("Saving group purchase");
                console.log(groupPurchaseTO);

                sln.call({
                   url : "/common/group_purchase/save",
                   type : "POST",
                   data : {
                       data : JSON.stringify({
                           group_purchase : groupPurchaseTO
                       })
                   },
                   success : function(data) {
                       sln.hideProcessing();
                       if (!data.success) {
                           return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                       }
                       $("#groupPurchaseModal").modal('hide');
                   },
                   error : sln.showAjaxError
                });
        };

        var eventPictureElement = document.getElementById('group_purchase_picture');
        if (eventPictureElement.files.length > 0) {
            var file = eventPictureElement.files[0];

            var canvas = document.createElement("canvas");
            var ctx = canvas.getContext("2d");
            var reader = new FileReader();
            reader.onload = function(e) {
                var img = new Image();
                img.onload = function() {
                    var MAX_WIDTH = 640;
                    var width = img.width;
                    var height = img.height;
                    
                    height *= MAX_WIDTH / width;
                    width = MAX_WIDTH;
                    
                    canvas.width = width;
                    canvas.height = height;
                    
                    ctx.drawImage(img, 0, 0, width, height);
                    picture = canvas.toDataURL("image/png");
                    new_picture = true;
                    post();
                }
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        } else {
            var existingPicture = $("#group_purchase_picture_existing img").attr('src');
            if (existingPicture)
                picture = existingPicture;
            post();
        }
    });

    var fadeOutMessageAndUpdateBadge = function(groupPurchaseId) {
        $('#group_purchase tr[group_purchase_id="' + groupPurchaseId + '"]').fadeOut('slow', function() {
            $(this).remove();
        });
        var badge = $('.sln-group-purchase-badge');
        var newBadgeValue = badge.text() - 1;
        badge.text(newBadgeValue > 0 ? newBadgeValue : '');
        sln.resize_header();
    };
    
    var setGroupPurchaseVisible = function(newEnabled) {
        groupPurhcaseEnabled = newEnabled;
        if (newEnabled) {
            $('#groupPurchaseVisible').addClass("btn-success").text(CommonTranslations.GROUP_PURCHASE_ENABLED);
            $('#groupPurchaseInvisible').removeClass("btn-danger").html('&nbsp;');
            $("#topmenu li[menu|='group_purchase']").css('display', 'block');
        } else {
            $('#groupPurchaseVisible').removeClass("btn-success").html('&nbsp;');
            $('#groupPurchaseInvisible').addClass("btn-danger").text(CommonTranslations.GROUP_PURCHASE_DISABLED);
            $("#topmenu li[menu|='group_purchase']").css('display', 'none');
        }
        sln.resize_header();
    };
    
    var loadSettings = function() {
        sln.call({
            url : "/common/group_purchase/settings/load",
            type : "GET",
            success : function(data) {
                setGroupPurchaseVisible(data.visible);
            },
            error : sln.showAjaxError
        });
    };
    
    var saveSettings = function() {
        sln.call({
            url : "/common/group_purchase/settings/save",
            type : "POST",
            data : {
                data : JSON.stringify({
                    group_purchase_settings : {
                        visible : groupPurhcaseEnabled
                    }
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
    
    
    sln.registerMsgCallback(channelUpdates);
    
    $(".sln-set-group_purchase-visibility").html(TMPL_SET_GROUP_PURCHASE_VISIBLE);
    
    $('#groupPurchaseVisible').click(function() {
        setGroupPurchaseVisible(!groupPurhcaseEnabled);
        saveSettings();
    });
    $('#groupPurchaseInvisible').click(function() {
        setGroupPurchaseVisible(!groupPurhcaseEnabled);
        saveSettings();
    });
});
