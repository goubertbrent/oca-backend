/*
 * Copyright 2020 Green Valley Belgium NV
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
 * @@license_version:1.7@@
 */

// Connect event handlers after load
$(function() {
    var restaurant_settings = null;
    var restaurant_tables = {};
    var reservation_force_add = null;
    var reservation_cancel = null;
    var reservation_add = null;
    var reservation_loading = null;
    var broken_reservation_loading = null;
    var reservation_stats_loading = null;
    var reservation_stats = null;
    var making_reservation = false;

    var currentShiftStartTime = null;
    var hideForceAddFromMakingReservation = false;

    var setting_time = false;

    var STATUS_AVAILABLE = 'available';
    var STATUS_SHORT_NOTICE = 'short-notice';
    var STATUS_TO_MANY_PEOPLE = 'too-many-people';
    var STATUS_NO_TABLES = 'no-tables';

    var STATUS_ARRIVED = 8;
    var STATUS_CANCELLED = 2;

    var reservation_people_keyup = function(e) {
        if (/\D/g.test($(this).val())) {
            $(this).val($(this).val().replace(/\D/g, ''));
        }
        if (!$(this).val())
            $(this).val('1');
    };
    var reservation_people_plus_click = function(elem) {
        return function(e) {
            elem.val(parseInt(elem.val()) + 1);
        };
    };
    var reservation_people_min_click = function(elem) {
        return function(e) {
            var current = parseInt(elem.val());
            if (current > 1)
                elem.val(current - 1);
        };
    };

    var broken_reservation_handled = function(reservation_key) {
        return function() {
            var tr = $("tr[key='" + reservation_key + "']");
            if ($("tr", tr.closest('tbody')).size() == 1) {
                $("#broken_reservations").fadeOut('slow', function() {
                    $(this).empty().show();
                });
            } else {
                tr.fadeOut('slow', function() {
                    tr.detach();
                });
            }
        };
    };

    var move_broken_reservation = function() {
        var thiz = $(this);
        var reservation_key = thiz.closest('tr').attr('key');
        var shift_name = thiz.attr('shift');
        sln.call({
            url : '/common/restaurant/reservations/move_shift',
            type : 'POST',
            data : {
                data : JSON.stringify({
                    reservation_key : reservation_key,
                    shift_name : shift_name
                })
            },
            success : broken_reservation_handled(reservation_key),
            error : sln.showAjaxError
        });
    };

    var cancel_reservation_notified = function() {
        var thiz = $(this);
        var reservation_key = thiz.closest('tr').attr('key');
        sln.call({
            url : '/common/restaurant/reservations/notified',
            type : 'POST',
            data : {
                data : JSON.stringify({
                    reservation_key : reservation_key
                })
            },
            success : broken_reservation_handled(reservation_key),
            error : sln.showAjaxError
        });
    };

    var cancel_reservations_via_app = function() {
        sln.confirm(CommonTranslations.RESTAURANT_RESERVATIONS_CANCEL_BROKEN, function() {
            sln.showProcessing(CommonTranslations.SENDING_DOT_DOT_DOT);
            var reservations_to_cancel = [];
            $("#broken_reservations tr[via-rogerthat='true']").each(function() {
                reservations_to_cancel.push($(this).attr('key'));
            });
            sln.call({
                url : '/common/restaurant/reservations/send_cancel_via_app',
                type : 'POST',
                data : {
                    data : JSON.stringify({
                        reservation_keys : reservations_to_cancel
                    })
                },
                success : function() {
                    var loads = 0;
                    var after_load = function(jqXHR) {
                        loads++;
                        jqXHR.always(function() {
                            loads--;
                            if (loads == 0)
                                sln.hideProcessing();
                        });
                    };
                    after_load(load_broken_reservations());
                    var now = $(reservation_details).data('date');
                    after_load(loadReservations(now, false));
                },
                error : sln.showAjaxError
            });
        }, null, CommonTranslations.SEND, CommonTranslations.CANCEL);
    };

    var load_broken_reservations = function() {
        if (broken_reservation_loading)
            return;
        broken_reservation_loading = true;
        return sln.call({
            url : "/common/restaurant/reservations/broken",
            success : function(reservations) {
                broken_reservation_loading = false;
                $("#broken_reservations").empty();
                if (reservations.length == 0)
                    return;
                var via_rogerthat = 0;
                $.each(reservations, function(j, reservation) {
                    enhanceReservation(reservation, true);
                    if (reservation.via_rogerthat)
                        via_rogerthat++;
                });
                var html = $.tmpl(templates.reservation_broken_reservations, {
                    reservations : reservations,
                    via_rogerthat : via_rogerthat
                });
                $("button.move-shift", html).click(move_broken_reservation);
                $("button.notified", html).click(cancel_reservation_notified);
                $("button.via-rogerthat", html).click(cancel_reservations_via_app);
                $("#broken_reservations").append(html);
            },
            error : sln.showAjaxError
        });
    };

    var channelUpdates = function(data) {
        if (data.type == "rogerthat.system.channel_connected") {
            var loads = 0;
            var after_load = function(jqXHR) {
                loads++;
                jqXHR.always(function() {
                    loads--;
                    if (loads == 0)
                        sln.hideProcessing();
                });
            };
            after_load(loadRestaurantSettings(true));
            var now = $(reservation_details).data('date');
            after_load(updateStatistics(now));
            after_load(load_broken_reservations());

        } else if (data.type == "solutions.restaurant.reservations.update") {
            var shift_start = data.shift;
            if (shift_start == undefined) {
                loadReservations($(reservation_details).data('date'), false);
                updateStatistics(new Date());
            } else {
                var shift_start_times = $(reservation_details).data('shift_start_times');
                if (shift_start_times) {
                    var displaying = false;
                    $.each(shift_start_times, function(i, st) {
                        if (st.year == shift_start.year && st.month == shift_start.month && st.day == shift_start.day
                                && st.hour == shift_start.hour && st.minute == shift_start.minute) {
                            displaying = true;
                            return false;
                        }
                    });
                    if (displaying) {
                        loadReservations($(reservation_details).data('date'), false);
                    }
                }
                shift_start = new Date(shift_start.year, shift_start.month - 1, shift_start.day, shift_start.hour,
                        shift_start.minute);
                var stats_start = new Date(reservation_stats.start.year, reservation_stats.start.month - 1,
                        reservation_stats.start.day);
                var stats_end = new Date(reservation_stats.end.year, reservation_stats.end.month - 1,
                        reservation_stats.end.day);
                if (stats_start.getTime() < shift_start.getTime() && stats_end.getTime() > shift_start.getTime())
                    updateStatistics(new Date());
            }
        } else if (data.type == "solutions.restaurant.reservations.shift_changes_conflicts") {
            load_broken_reservations();
        } else if (data.type == "solutions.restaurant.tables.update") {
            loadRestaurantSettings(true);
        }
    };

    /* Shifts */

    var showEditShift = function(shift) {
        var html = $.tmpl(templates.reservation_addshift, {
            header : shift ? CommonTranslations.EDIT_SHIFT : CommonTranslations.ADD_SHIFT,
            cancelBtn : CommonTranslations.CANCEL,
            submitBtn : CommonTranslations.SAVE,
            CommonTranslations : CommonTranslations,
            DAYS_STR : DAYS_STR
        });
        var modal = sln.createModal(html);
        $('#shiftstart, #shiftend', modal).timepicker({
            showMeridian : false
        });
        $("i.icon-question-sign", modal).css('cursor', 'pointer').css('margin-left', '10px').click(function() {
            sln.alert($(this).attr('hint'), null, CommonTranslations.HELP);
        });
        if (shift) {
            $("#name", modal).val(shift.name);
            $("#capacity", modal).val(shift.capacity);
            $('#shiftstart', modal).timepicker('setTime', sln.intToTime(shift.start));
            $('#shiftend', modal).timepicker('setTime', sln.intToTime(shift.end));
            $("#leaptime", modal).val(shift.leap_time);
            $("#groupsize", modal).val(shift.max_group_size);
            $("#bookingthreshold", modal).val(shift.threshold);
            $.each(shift.days, function(i, o) {
                $('input[type="checkbox"][value="' + o + '"]', modal).attr("checked", true);
            });
        }
        $('button[action="submit"]', modal).click(
                function() {
                    var nameValid = sln.validate($("#nameerror", modal), $("#name", modal), CommonTranslations.NAME_IS_REQUIRED);
                    var capacityValid = sln.validate($("#capacityerror", modal), $("#capacity", modal),
                            CommonTranslations.CAPACITY_IS_REQUIRED, function(val) {
                                return sln.isNumber(val) && Number(val) > 0;
                            });
                    var startValid = sln.validate($("#starterror", modal), $("#shiftstart", modal), CommonTranslations.REQUIRED_LOWER);
                    var endValid = sln.validate($("#enderror", modal), $("#shiftend", modal), CommonTranslations.REQUIRED_LOWER);

                    if (!(nameValid && startValid && endValid && capacityValid))
                        return;

                    var name = $("#name", modal).val();
                    var startTime = $("#shiftstart", modal).val();
                    var endTime = $("#shiftend", modal).val();
                    var capacity = $("#capacity", modal).val();
                    var leaptime = $("#leaptime", modal).val();
                    var bookingThreshold = $("#bookingthreshold", modal).val();
                    var groupSize = $("#groupsize", modal).val();
                    var shiftDays = [];
                    $('input:checked[type="checkbox"]', modal).each(function() {
                        shiftDays.push(Number($(this).val()));
                    });

                    if (!shiftDays.length) {
                        sln.alert(CommonTranslations.NO_DAYS_SELECTED_FOR_THIS_SHIFT, null, CommonTranslations.ERROR);
                        return;
                    }

                    var add = !shift;
                    if (add)
                        shift = {};

                    var timetoseconds = function(time) {
                        var time = time.split(":");
                        return Number(time[0]) * 60 * 60 + Number(time[1]) * 60;
                    };

                    shift.name = name;
                    shift.start = timetoseconds(startTime);
                    shift.end = timetoseconds(endTime);
                    shift.leap_time = Number(leaptime);
                    shift.capacity = Number(capacity);
                    shift.threshold = Number(bookingThreshold);
                    shift.max_group_size = Number(groupSize);
                    shift.days = shiftDays;

                    if (add)
                        restaurant_settings.shifts.push(shift);

                    sln.call({
                        url : "/common/restaurant/settings/shifts/save",
                        type : "POST",
                        data : {
                            data : JSON.stringify({
                                shifts : restaurant_settings.shifts
                            })
                        },
                        success : function(data) {
                            if (!data.success) {
                                sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                                return;
                            }
                            loadRestaurantSettings(false);
                            modal.modal('hide');
                        },
                        error : sln.showAjaxError
                    });
                });
    };

    var addShift = function() {
        showEditShift();
    };

    var editShift = function() {
        showEditShift($(this).parents('tr').data('shift'));
    };

    var deleteShift = function() {
        var shift = $(this).parents('tr').data('shift');
        var index = -1;
        $.each(restaurant_settings.shifts, function(i, s) {
            if (s === shift)
                index = i;
        });

        sln.confirm(CommonTranslations.SHIFT_REMOVE_CONFIRMATION, function() {
            restaurant_settings.shifts.splice(index, 1);
            sln.call({
                url : "/common/restaurant/settings/shifts/save",
                type : "POST",
                data : {
                    data : JSON.stringify({
                        shifts : restaurant_settings.shifts
                    })
                },
                success : function(data) {
                    if (!data.success) {
                        sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    }
                    loadRestaurantSettings(false);
                },
                error : sln.showAjaxError
            });
        }, null, CommonTranslations.YES, CommonTranslations.NO, CommonTranslations.CONFIRM);

    };

    var loadRestaurantSettings = function(load_reservations) {
        return sln.call({
            url : "/common/restaurant/settings/load",
            type : "GET",
            success : function(data) {
                restaurant_settings = data;
                restaurant_tables = {};

                restaurant_settings.tables.sort(function(table1, table2) {
                    return sln.smartSort(table1.name, table2.name);
                });

                $.each(restaurant_settings.tables, function(i, table) {
                    restaurant_tables[table.key] = table;
                });

                if (load_reservations) {
                    var now = $(reservation_details).data('date');
                    loadReservations(now, false);
                }

                renderShift();
                renderTables();


                if (restaurant_settings.shifts.length == 0) {
                    $("#reservations_menu span.badge").removeClass("badge-success").removeClass("badge-warning")
                    .removeClass("badge-important").addClass('badge-important').text('!');

                    $(".reservations-has-shifts").hide();
                    $(".reservations-no-shifts").show();
                } else {
                    $(".reservations-no-shifts").hide();
                    $(".reservations-has-shifts").show();
                }
            },
            error : sln.showAjaxError
        });
    };

    var updateStatistics = function(date) {
        if (reservation_stats_loading)
            return;

        if (restaurant_settings && restaurant_settings.shifts && restaurant_settings.shifts.length == 0) {
            return;
        }

        reservation_stats_loading = true;
        return sln.call({
            url : "/common/restaurant/reservation-stats",
            data : {
                year : date.getFullYear(),
                month : date.getMonth() + 1,
                day : date.getDate()
            },
            success : function(stats) {
                reservation_stats_loading = false;

                if (restaurant_settings && restaurant_settings.shifts && restaurant_settings.shifts.length == 0) {
                    return;
                }

                $.each([ 'today', 'tomorrow', 'next_week' ], function(i, when) {
                    var stts = stats[when];
                    var rate = stts.capacity == 0 ? 0 : stts.reservations / stts.capacity * 100;
                    var threshold_rate = stts.capacity_threshold / stts.capacity * 100;
                    var success_rate = 0;
                    var warning_rate = 0;
                    var error_rate = 0;
                    var badge_class = "success";
                    rate = isNaN(rate) ? 0 : rate;
                    if (rate > threshold_rate) {
                        badge_class = "warning";
                        success_rate = threshold_rate;
                        warning_rate = Math.min(100, rate) - success_rate;
                        if (Math.max(100, rate) > 100) {
                            badge_class = "important";
                            success_rate = Math.round(success_rate / rate * 100);
                            warning_rate = Math.round(warning_rate / rate * 100);
                            error_rate = 100 - success_rate - warning_rate;
                        }
                    } else
                        success_rate = rate;
                    if (when == 'today') {
                        $("#reservations_menu span.badge").removeClass("badge-success").removeClass("badge-warning")
                                .removeClass("badge-important").addClass('badge-' + badge_class).text(
                                        Math.round(rate) + '%');
                    }

                    var div = $("#" + when + "-capacity");
                    $("span", div).empty().text(Math.round(rate) + '%');
                    div = $("div.progress", div).empty();
                    div.append($("<div></div>").addClass('bar').addClass('bar-success').css('width',
                            Math.round(success_rate) + '%'));
                    if (warning_rate > 0)
                        div.append($("<div></div>").addClass('bar').addClass('bar-warning').css('width',
                                Math.round(warning_rate) + '%'));
                    if (error_rate > 0)
                        div.append($("<div></div>").addClass('bar').addClass('bar-danger').css('width',
                                Math.round(error_rate) + '%').css('background-color', '#dd514c'));
                });
                reservation_stats = stats;
            },
            error : function(a, b, c) {
                reservation_stats_loading = false;
                sln.showAjaxError(a, b, c);
            }
        });
    };

    var updateReservationDisplay = function(tr, reservation) {

        if ((reservation.status & STATUS_CANCELLED) == STATUS_CANCELLED) {
            tr.addClass('error').css('text-decoration', 'line-through');
            $("button.edit-reservation, button.check-arrived, button.tables-reservation", tr).attr('disabled', true);
        } else if ((reservation.status & STATUS_ARRIVED) == STATUS_ARRIVED) {
            tr.addClass('success');
            $("button.edit-reservation, button.trash-reservation, button.tables-reservation", tr)
                    .attr('disabled', true);
        } else {
            tr.removeClass('success').removeClass('error').css('text-decoration', '');
            $("button.check-arrived, button.edit-reservation, button.trash-reservation, button.tables-reservation", tr)
                    .removeAttr('disabled');
        }
    };

    var replyReservation = function() {
        var button = $(this);
        var user_name = button.attr("user_name");
        var user_email = button.attr("user_email");
        var user_app_id = button.attr("user_app_id");

        var tr = button.closest('tr');
        var reservation_key = tr.attr('key');
        var full_time = tr.attr('full_time');

        sln.inputBox(function(message) {
            sln.call({
                url : "/common/restaurant/reservation/reply",
                type : "POST",
                data : {
                    data : JSON.stringify({
                        email : user_email,
                        app_id : user_app_id,
                        message : message,
                        reservation_key : reservation_key
                    })
                },
                success : function(data) {
                    if (!data.success) {
                        return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    }
                },
                error : sln.showAjaxError
            });
        }, CommonTranslations.REPLY, null, CommonTranslations.RESERVATION_REPLY_ON
            .replace("%(username)s", user_name), CommonTranslations.RESERVATION_IN_CONNECTION_WITH.replace("%(date)s", full_time));
    };

    var toggleArrived = function() {
        var button = $(this);
        var tr = button.closest('tr');
        var reservation_key = tr.attr('key');
        sln.call({
            url : '/common/restaurant/reservation/arrived',
            type : 'POST',
            data : {
                data : JSON.stringify({
                    reservation_key : reservation_key
                })
            },
            success : function(data) {
                tr.data('reservation', data);
                updateReservationDisplay(tr, data);
            },
            error : sln.showAjaxError
        });
    };

    var toggleCancelled = function() {
        var button = $(this);
        var tr = button.closest('tr');
        var reservation_key = tr.attr('key');
        sln.call({
            url : '/common/restaurant/reservation/cancelled',
            type : 'POST',
            data : {
                data : JSON.stringify({
                    reservation_key : reservation_key
                })
            },
            success : function(data) {
                tr.data('reservation', data);
                updateReservationDisplay(tr, data);
            },
            error : sln.showAjaxError
        });
    };

    var editReservation = function() {
        var button = $(this);
        var tr = button.closest('tr');
        var reservation = tr.data('reservation');

        var date = new Date(reservation.timestamp.year, reservation.timestamp.month - 1, reservation.timestamp.day,
                reservation.timestamp.hour, reservation.timestamp.minute, 0, 0);
        reservation.when = date.toLocaleDateString() + " " + date.toLocaleTimeString();

        var html = $.tmpl(templates.reservation_editreservation, {
            reservation : reservation
        });
        $("#reservation-people", html).keyup(reservation_people_keyup);
        $("#reservation-people-plus", html).click(reservation_people_plus_click($("#reservation-people", html)));
        $("#reservation-people-min", html).click(reservation_people_min_click($("#reservation-people", html)));

        $("#edit-reservation-date-control", html).datepicker({
            format : sln.getLocalDateFormat()
        }).on('changeDate', function(ev) {
            $("#edit-reservation-date-control", html).datepicker('hide');
        }).datepicker('setValue', sln.today());

        $('#edit-reservation-time', html).timepicker({
            showMeridian : false
        });

        var dateWithoutTime = new Date(reservation.timestamp.year, reservation.timestamp.month - 1,
                reservation.timestamp.day);
        $("#edit-reservation-date-control", html).datepicker('setValue', dateWithoutTime);
        var minutes = '' + date.getMinutes();
        if (minutes.length < 2)
            minutes = '0' + minutes;
        $("#edit-reservation-time", html).timepicker('setTime', date.getHours() + ':' + minutes);

        var modal = sln.createModal(html);

        var submit = function(force) {
            var new_people_count = parseInt($("#reservation-people", html).val());
            var new_comment = $("textarea", html).val();

            var new_date = $("#edit-reservation-date", html).parent().data('datepicker').date;
            var new_time = $("#edit-reservation-time", html).val().split(":");

            var new_day = new_date.getDate();
            var new_month = new_date.getMonth() + 1;
            var new_year = new_date.getFullYear();
            var new_hour = parseInt(new_time[0]);
            var new_minute = parseInt(new_time[1]);

            $
                    .ajax({
                        url : '/common/restaurant/reservation/edit',
                        type : 'POST',
                        data : {
                            data : JSON.stringify({
                                reservation_key : reservation.key,
                                people : new_people_count,
                                comment : new_comment,
                                force : force,
                                new_date : {
                                    year : new_year,
                                    month : new_month,
                                    day : new_day,
                                    hour : new_hour,
                                    minute : new_minute
                                }
                            })
                        },
                        success : function(status) {
                            if (status == STATUS_AVAILABLE) {
                                modal.modal('hide');
                                return;
                            }
                            $("div.server-validation-error", modal).hide();
                            $("div.server-validation-error." + status, modal).show();

                            if (status == STATUS_TO_MANY_PEOPLE || status == STATUS_NO_TABLES
                                    || status == STATUS_SHORT_NOTICE) {
                                $('button.save[action="submit"]', modal).hide();
                                $('button.force-save[action="submit"]', modal).show();
                            } else {
                                $('button.force-save[action="submit"]', modal).hide();
                                $('button.save[action="submit"]', modal).show();
                            }
                        },
                        error : sln.showAjaxError
                    });
        };
        $('button.save[action="submit"]', modal).click(function() {
            submit(false);
        });
        $('button.force-save[action="submit"]', modal).click(function() {
            submit(true);
        });
    };

    var editTableReservation = function() {
        var button = $(this);
        var tr = button.closest('tr');
        var reservation = tr.data('reservation');
        var shift = tr.data('shift');
        var html = $.tmpl(templates.reservation_edittables, {
            tables : restaurant_tables,
            tables_in_use : shift.reserved_tables,
            reservation : reservation
        });
        var modal = sln.createModal(html);
        $('button.save[action="submit"]', modal).click(function() {
            var tables = [];
            $('#table_reservations input:checkbox', modal).each(function() {
                if (this.checked) {
                    tables.push(parseInt($(this).attr("table_key")));
                }
            });
            sln.call({
                url : '/common/restaurant/reservation/edit_tables',
                type : 'POST',
                data : {
                    data : JSON.stringify({
                        reservation_key : reservation.key,
                        tables : tables
                    })
                },
                success : function(data) {
                    if (!data.success) {
                        return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    }
                    modal.modal('hide');
                },
                error : sln.showAjaxError
            });
        });
    };

    var enhanceReservation = function(reservation, fullDate) {
        var date = new Date(reservation.timestamp.year, reservation.timestamp.month - 1, reservation.timestamp.day,
                reservation.timestamp.hour, reservation.timestamp.minute, 0, 0);
        if (fullDate) {
            reservation.time = sln.format(date);
        } else {
            reservation.time = sln.padLeft(reservation.timestamp.hour, 2, '0') + ':'
                    + sln.padLeft(reservation.timestamp.minute, 2, '0');
        }
    };

    var enterShow = function() {
        if ($(this).data('state') === 'hover') {
            $(this).popover('show');
        }
    };
    var exitHide = function() {
        if ($(this).data('state') === 'hover') {
            $(this).popover('hide');
        }
    };

    var clickToggle = function() {
        if ($(this).data('state') === 'hover') {
            $(this).data('state', 'pinned');
        } else {
            $(this).data('state', 'hover');
            $(this).popover('hide');
        }
    };

    var loadReservations = function(date, isDetail) {
        if (reservation_loading)
            return;
        reservation_loading = true;
        return sln.call({
            url : "/common/restaurant/reservations",
            type : "GET",
            data : {
                year : date.getFullYear(),
                month : date.getMonth() + 1,
                day : date.getDate(),
                hour : date.getHours(),
                minute : date.getMinutes()
            },
            success : function(shifts) {
                reservation_loading = false;
                var shift_start_times = [];
                $.each(shifts, function(i, shift) {
                    var d = new Date(shift.start_time.year, shift.start_time.month - 1, shift.start_time.day,
                            shift.start_time.hour, shift.start_time.minute, 0, 0);
                    shift_start_times.push(shift.start_time);
                    shift.date = d.toLocaleDateString();
                    shift.time = d.toLocaleTimeString();
                    d = new Date(d.getTime() + 1000 * (shift.shift.end - shift.shift.start));
                    shift.end_time = d.toLocaleTimeString();
                    var total = 0;

                    shift.reservations.sort(function(b, a) {
                        if (a.timestamp.year == b.timestamp.year)
                            if (a.timestamp.month == b.timestamp.month)
                                if (a.timestamp.day == b.timestamp.day)
                                    if (a.timestamp.hour == b.timestamp.hour)
                                        if (a.timestamp.minute == b.timestamp.minute)
                                            return 0;
                                        else
                                            return b.timestamp.minute - a.timestamp.minute;
                                    else
                                        return b.timestamp.hour - a.timestamp.hour;
                                else
                                    return b.timestamp.day - a.timestamp.day;
                            else
                                return b.timestamp.month - a.timestamp.month;
                        return b.timestamp.year - a.timestamp.year;
                    });

                    var reserved_tables = [];
                    $.each(shift.reservations, function(j, reservation) {
                        var backupReservation = reservation;
                        enhanceReservation(backupReservation, true);
                        reservation.full_time = backupReservation.time;
                        enhanceReservation(reservation);
                        if ((reservation.status & STATUS_CANCELLED) == STATUS_CANCELLED)
                            return true;
                        total += reservation.people;
                        reservation.table_names = [];
                        $.each(reservation.tables, function(j, table) {
                            var rt = restaurant_tables[table];
                            if (rt != undefined) {
                                reservation.table_names.push(rt.name);
                                reserved_tables.push(table);
                            } else {
                                console.log("Table with key '" + table + "' not found in restaurant tables.");
                            }
                        });
                        reservation.table_names = reservation.table_names.join(", ");
                    });
                    shift.reserved_tables = reserved_tables;
                    shift.fill = Math.round(100 * total / shift.shift.capacity);
                });
                var showShifts = true;
                if (isDetail) {
                    var backupShifts = shifts;
                    shifts = [];
                    if (backupShifts.length > 0) {
                        if (currentShiftStartTime != null) {
                            var newShiftStartTime = backupShifts[0].start_time;
                            if (currentShiftStartTime.year != newShiftStartTime.year
                                    || currentShiftStartTime.month != newShiftStartTime.month
                                    || currentShiftStartTime.day != newShiftStartTime.day
                                    || currentShiftStartTime.hour != newShiftStartTime.hour
                                    || currentShiftStartTime.minute != newShiftStartTime.minute) {
                                hideForceAddFromMakingReservation = true;
                            }
                        }

                        var shiftStart = backupShifts[0].shift.start;
                        var shiftEnd = backupShifts[0].shift.end;
                        var timePicker = date.getHours() * 3600 + date.getMinutes() * 60;
                        if (shiftStart <= timePicker && timePicker <= shiftEnd)
                            shifts.push(backupShifts[0]);
                        else {
                            showShifts = false;
                            hideForceAddFromMakingReservation = true;
                        }
                        currentShiftStartTime = backupShifts[0].start_time;
                    } else {
                        showShifts = false;
                        hideForceAddFromMakingReservation = true;
                    }
                }
                if (showShifts) {
                    var html = $.tmpl(templates.reservations, {
                        shifts : shifts
                    });
                    $("button.btn.reply-reservation", html).click(replyReservation);
                    $("button.btn.tables-reservation", html).click(editTableReservation);
                    $("button.btn.check-arrived", html).click(toggleArrived);
                    $("button.btn.trash-reservation", html).click(toggleCancelled);
                    $("button.btn.edit-reservation", html).click(editReservation);
                    $(reservation_details).empty().append(html).data('shift_start_times', shift_start_times).data(
                            'date', date);
                    $.each(shifts, function(i, shift) {
                        $.each(shift.reservations, function(j, reservation) {
                            var tr = $("tr[key='" + reservation.key + "']");
                            tr.data('reservation', reservation);
                            tr.data('shift', shift);
                            updateReservationDisplay(tr, reservation);
                        });
                    });
                } else {
                    var html = $.tmpl(templates.reservation_no_shift_found, {
                        CommonTranslations : CommonTranslations
                    });
                    $(reservation_details).empty().append(html);
                }
                if (hideForceAddFromMakingReservation) {
                    hideForceAddFromMakingReservation = false;
                    $(".server-validation-error").hide();
                    reservation_force_add.detach();
                    reservation_cancel.after(reservation_add);
                    $("#make_reservation").hide();
                    $("#make_reservation_forced").show();
                }

                if (!making_reservation) {
                    clearReservationForm(true);
                }

                $(".broadcastUserImage").data('state', 'hover');
                $(".broadcastUserImage").popover({
                    trigger : 'manual',
                    placement : 'bottom'
                }).on('mouseenter', enterShow).on('mouseleave', exitHide).on('click', clickToggle);
            },
            error : function(a, b, c) {
                reservation_loading = false;
                sln.showAjaxError(a, b, c);
            }
        });
    };

    var cancelReservationForm = function() {
        clearReservationForm();
        $("button.hidden").hide();
        $("#make_reservation").show();
    };

    var clearReservationForm = function(do_not_reload_reservations) {
        var now = new Date();
        $("#reservation-name").val("").tooltip('hide');
        $("#reservation-people").val(2);

        var sst = $("#reservation_details").data('shift_start_times');
        var set = false;
        if (sst) {
            $.each(sst, function(i, time) {
                var date = new Date(time.year, time.month - 1, time.day, time.hour, time.minute);
                if (date > now) {
                    var dateWithoutTime = new Date(time.year, time.month - 1, time.day);
                    $("#reservation-date-control").datepicker('setValue', dateWithoutTime);
                    var minutes = '' + date.getMinutes();
                    if (minutes.length < 2)
                        minutes = '0' + minutes;
                    setReservationTime(date.getHours() + ':' + minutes);
                    set = true;
                    return false; // break loop
                }
            });
        }
        if (!set) {
            $("#reservation-date-control").datepicker('setValue', sln.today());
            setReservationTime((now.getHours() + 1) + ':00');
        }
        $("#reservation-phone").val("");
        $("#reservation-comment").val("");
        $(".server-validation-error").hide();
        $("#make_reservation").show();
        $("#make_reservation_forced").hide();
        making_reservation = false;
        if (!do_not_reload_reservations || do_not_reload_reservations == undefined)
            loadReservations(now, false);
    };

    var setReservationTime = function(time) {
        setting_time = true;
        try {
            $("#reservation-time").timepicker('setTime', time);
        } finally {
            setting_time = false;
        }
    };

    var beginEditingReservations = function(date) {
        loadReservations(date, true);
    };

    var getCurrentDisplayedReservationTime = function() {
        var time = $("#reservation-time").val().split(":");
        var hour = parseInt(time[0]);
        var minute = parseInt(time[1]);
        return {
            hour : hour,
            minute : minute
        };
    };

    var getCurrentDisplayedReservationDate = function() {
        return $("#reservation-date").parent().data('datepicker').date;
    };

    var sumDateAndTime = function(date, time) {
        return new Date(date.getTime() + time.hour * 3600 * 1000 + time.minute * 60 * 1000);
    };

    var reserveTable = function(force) {
        var name = $.trim($("#reservation-name").val());
        if (!name) {
            $("#reservation-name").tooltip('show').focus();
            return;
        }
        var phone = $.trim($("#reservation-phone").val());
        var people = parseInt($("#reservation-people").val());
        var date = getCurrentDisplayedReservationDate();
        var day = date.getDate();
        var month = date.getMonth() + 1;
        var year = date.getFullYear();
        var time = getCurrentDisplayedReservationTime();
        var comment = $("#reservation-comment").val();
        sln.call({
            url : "/common/restaurant/reservations",
            type : "POST",
            data : {
                data : JSON.stringify({
                    year : year,
                    month : month,
                    day : day,
                    hour : time.hour,
                    minute : time.minute,
                    name : name,
                    people : people,
                    comment : comment,
                    phone : phone,
                    force : force
                })
            },
            success : function(data) {
                if (data == STATUS_AVAILABLE) {
                    $(".reservation-successful").show();
                    setTimeout(function() {
                        $(".reservation-successful").fadeOut();
                    }, 1000);
                    clearReservationForm();
                    return;
                }
                $(".server-validation-error").hide();
                $(".server-validation-error." + data).show();
                $("#make_reservation").hide();
                $("#make_reservation_forced").show();
                reservation_add.detach();
                reservation_force_add.detach();
                if (data == STATUS_TO_MANY_PEOPLE || data == STATUS_NO_TABLES || data == STATUS_SHORT_NOTICE) {
                    reservation_cancel.after(reservation_force_add);
                } else {
                    reservation_cancel.after(reservation_add);
                }
                $("button.hidden").show();
            },
            error : sln.showAjaxError
        });
    };

    var renderShift = function() {
        var shiftHtmlElement = $("#shift_rendering");
        shiftHtmlElement.empty();
        $.each(restaurant_settings.shifts, function(i, shift) {
            shift.startStr = sln.intToTime(shift.start);
            shift.endStr = sln.intToTime(shift.end);
            var weekDaysStrs = [];
            $.each(shift.days, function(i, o) {
                weekDaysStrs.push(DAYS_STR[o - 1]);
            });
            shift.weekDaysStr = weekDaysStrs.join(", ");
            shift.detailStr = T('from-x-to-y-on-z', {
                start: shift.startStr,
                end: shift.endStr,
                date: shift.weekDaysStr
            });
        });
        var html = $.tmpl(templates.reservation_shiftcontents, {
            shifts : restaurant_settings.shifts
        });
        $.each(restaurant_settings.shifts, function(i, shift) {
            $($("tr", html).get(i)).data('shift', shift);
        });
        shiftHtmlElement.append(html);
        $('#shift_rendering').find('button[action="deleteShift"]').click(deleteShift);
        $('#shift_rendering').find('button[action="editShift"]').click(editShift);
    };

    /* Tables */

    var showEditTable = function(table) {
        var html = $.tmpl(templates.reservation_addtable, {
            header : table ? CommonTranslations.EDIT_TABLE : CommonTranslations.ADD_TABLE,
            cancelBtn : CommonTranslations.CANCEL,
            submitBtn : CommonTranslations.SAVE,
            CommonTranslations: CommonTranslations
        });
        var modal = sln.createModal(html);
        if (table) {
            $("#name", modal).val(table.name);
            $("#capacity", modal).val(table.capacity);
        }
        $('button[action="submit"]', modal).click(
                function() {
                    var nameValid = sln.validate($("#nameerror", modal), $("#name", modal), CommonTranslations.NAME_IS_REQUIRED);
                    var capacityValid = sln.validate($("#capacityerror", modal), $("#capacity", modal),
                            CommonTranslations.CAPACITY_IS_REQUIRED, function(val) {
                                return sln.isNumber(val) && Number(val) > 0;
                            });

                    if (!(nameValid && capacityValid))
                        return;

                    var name = $("#name", modal).val();
                    var capacity = parseInt($("#capacity", modal).val());

                    var key = table ? table.key : -1;
                    var url = table ? "/common/restaurant/settings/tables/update" : "/common/restaurant/settings/tables/add";

                    sln.call({
                        url : url,
                        type : "POST",
                        data : {
                            data : JSON.stringify({
                                table : {
                                    key : key,
                                    name : name,
                                    capacity : capacity
                                }
                            })
                        },
                        success : function(data) {
                            if (!data.success) {
                                sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                                return;
                            }
                            modal.modal('hide');
                        },
                        error : sln.showAjaxError
                    });
                });
    };

    var deleteTable = function(table) {
        sln.confirm(CommonTranslations.TABLE_REMOVE_CONFIRMATION, function() {

            var renderReservations = function(modal, reservations) {

                $.each(reservations, function(i, reservation) {
                    var reserved_tables = [];
                    $.each(reservation.shift.reservations, function(j, shift_reservations) {
                        var backupReservation = shift_reservations;
                        enhanceReservation(backupReservation, true);
                        shift_reservations.full_time = backupReservation.time;
                        enhanceReservation(shift_reservations);
                        if ((shift_reservations.status & STATUS_CANCELLED) == STATUS_CANCELLED)
                            return true;
                        $.each(shift_reservations.tables, function(j, table) {
                            var rt = restaurant_tables[table];
                            if (rt != undefined) {
                                reserved_tables.push(table);
                            } else {
                                console.log("Table with key '" + table + "' not found in restaurant tables.");
                            }
                        });
                    });
                    reservation.shift.reserved_tables = reserved_tables;

                    var backupReservation = reservation.reservation;
                    enhanceReservation(backupReservation, true);
                    reservation.reservation.full_time = backupReservation.time;
                    enhanceReservation(reservation.reservation);

                    reservation.reservation.table_names = [];
                    $.each(reservation.reservation.tables, function(j, table) {
                        var rt = restaurant_tables[table];
                        if (rt != undefined) {
                            reservation.reservation.table_names.push(rt.name);
                        } else {
                            console.log("Table with key '" + table + "' not found in restaurant tables.");
                        }
                    });
                    reservation.reservation.table_names = reservation.reservation.table_names.join(", ");
                });
                var reservationsCount = reservations.length;

                var html = $.tmpl(templates.reservation_update_reservation_tables, {
                    remove_table_key : table.key,
                    tables : restaurant_tables,
                    reservations : reservations
                });

                var tbody = $("tbody", modal).empty().append(html);
                $.each(reservations, function(j, reservation) {
                    var tr = $("tr[key='" + reservation.reservation.key + "']", tbody);
                    tr.data('reservation', reservation.reservation);
                    tr.data('shift', reservation.shift);
                });

                $("button.btn.edit-reservation", html).click(function() {
                    var button = $(this);
                    var tr = button.closest('tr');

                    $(".delete_table_not_editing", tr).hide();
                    $(".delete_table_editing", tr).show();
                });

                $("button.btn.discard-reservation", html).click(function() {
                    var button = $(this);
                    var tr = button.closest('tr');

                    $(".delete_table_not_editing", tr).show();
                    $(".delete_table_editing", tr).hide();
                });

                $("button.btn.save-reservation", html).click(
                        function() {
                            var button = $(this);
                            var tr = button.closest('tr');
                            var reservation = tr.data('reservation');

                            var tables = [];
                            $('.table_reservations input:checkbox', tr).each(function() {
                                if (this.checked) {
                                    tables.push(parseInt($(this).attr("table_key")));
                                }
                            });

                            if ($.inArray(table.key, tables) != -1) {
                                sln.alert(CommonTranslations.TABLE_REMOVE_REPLACE_BY_OTHER, null, CommonTranslations.ERROR);
                                return;
                            }
                            tr.hide();
                            reservationsCount -= 1;

                            sln.call({
                                url : '/common/restaurant/reservation/edit_tables',
                                type : 'POST',
                                data : {
                                    data : JSON.stringify({
                                        reservation_key : reservation.key,
                                        tables : tables
                                    })
                                },
                                success : function(data) {
                                    if (!data.success) {
                                        return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                                    }
                                    if (reservationsCount == 0) {
                                        sln.call({
                                            url : "/common/restaurant/settings/tables/delete",
                                            type : "POST",
                                            data : {
                                                data : JSON.stringify({
                                                    table_id : table.key,
                                                    force : true
                                                })
                                            },
                                            success : function(data) {
                                                if (data.success) {
                                                    modal.modal('hide');
                                                } else {
                                                    sln.showAjaxError();

                                                }
                                            },
                                            error : sln.showAjaxError
                                        });
                                    }
                                },
                                error : sln.showAjaxError
                            });
                        });

            };

            sln.call({
                url : "/common/restaurant/settings/tables/delete",
                type : "POST",
                data : {
                    data : JSON.stringify({
                        table_id : table.key,
                        force : false
                    })
                },
                success : function(data) {
                    if (!data.success) {
                        var html = $.tmpl(templates.reservation_delete_table_confirmation, {
                            table_name : table.name,
                            CommonTranslations : CommonTranslations
                        });
                        var modal = sln.createModal(html);
                        $('button.force-remove-table[action="submit"]', modal).click(function() {
                            sln.call({
                                url : "/common/restaurant/settings/tables/delete",
                                type : "POST",
                                data : {
                                    data : JSON.stringify({
                                        table_id : table.key,
                                        force : true
                                    })
                                },
                                success : function(data) {
                                    if (data.success) {
                                        modal.modal('hide');
                                    } else {
                                        sln.showAjaxError();

                                    }
                                },
                                error : sln.showAjaxError
                            });
                        });
                        renderReservations(modal, data.reservations);
                    }
                },
                error : sln.showAjaxError
            });

        }, null, CommonTranslations.YES);
    };

    var renderTables = function() {
        var tableHtmlElement = $("#tables");
        tableHtmlElement.empty();
        var html = $.tmpl(templates.reservation_tablecontents, {
            tables : restaurant_tables,
            CommonTranslations : CommonTranslations
        });

        var count = 1; // skip table header row
        $.each(restaurant_tables, function(i, table) {
            $($("tr", html).get(count)).data('table', table);
            count += 1;
        });

        tableHtmlElement.append(html);
        $('#tables button[action="deleteTable"]').click(function() {
            var table = $(this).parents('tr').data('table');
            console.log(table);
            deleteTable(table);
        });
        $('#tables button[action="editTable"]').click(function() {
            var table = $(this).parents('tr').data('table');
            console.log(table);
            showEditTable(table);
        });
    };

    var beginEditingReservationFunction = function() {
        loadReservations(sumDateAndTime(getCurrentDisplayedReservationDate(), getCurrentDisplayedReservationTime()),
                true);
        making_reservation = true;
        reservation_force_add.detach();
        reservation_cancel.after(reservation_add);
        $("#make_reservation").hide();
        $("#make_reservation_forced").show();
    };

    $("#reservation-date-control").datepicker({
        format : sln.getLocalDateFormat()
    }).on('changeDate', function(ev) {
        $("#reservation-date-control").datepicker('hide');
        beginEditingReservationFunction();
    }).datepicker('setValue', sln.today());

    $('#reservation-time').timepicker({
        showMeridian : false
    }).on('changeTime.timepicker', function(e) {
        if (!setting_time) {
            loadReservations(sumDateAndTime(getCurrentDisplayedReservationDate(), {
                hour : e.time.hours,
                minute : e.time.minutes
            }), true);
            making_reservation = true;
        }
    });
    $("#addshiftbutton").click(addShift);

    $("#addtable").click(function() {
        showEditTable();
    });
    $("#make_reservation, button.reservation-add").click(function() {
        reserveTable(false);
    });
    reservation_add = $("button.reservation-add");
    reservation_force_add = $("button.reservation-force-add").click(function() {
        reserveTable(true);
    });
    reservation_cancel = $("button.reservation-cancel");
    $("button.reservation-cancel").click(cancelReservationForm);
    $("#reservation-name").tooltip({}).keydown(function() {
        $(this).tooltip('hide');
    });
    $("#reservation-date").keydown(function(e) {
        if (e.which == 40 || e.which == 39 || e.which == 38 || e.which == 37) { // down
            // right
            // up
            // left
            // arrow
            making_reservation = true;
            var date = getCurrentDisplayedReservationDate();
            var toAdd = e.which == 40 || e.which == 39 ? 1 : -1;
            var tomorrow = new Date(date.getTime() + toAdd * 3600 * 24 * 1000);
            $("#reservation-date-control").datepicker('setValue', tomorrow);
            loadReservations(sumDateAndTime(tomorrow, getCurrentDisplayedReservationTime()), true);
            return false;
        }
    });

    $("#reservation-people").keyup(reservation_people_keyup);
    $("#reservation-people-plus").click(reservation_people_plus_click($("#reservation-people")));
    $("#reservation-people-min").click(reservation_people_min_click($("#reservation-people")));

    $("#reservations_menu").click(function() {
        $("#reservation-name").focus();
    });

    var changeBeginReservationHandler = function() {
        if (!making_reservation) {
            beginEditingReservationFunction();
        }
    };

    sln.configureDelayedInput($('#reservation-name'), changeBeginReservationHandler);
    sln.configureDelayedInput($('#reservation-people'), changeBeginReservationHandler);
    sln.configureDelayedInput($('#reservation-phone'), changeBeginReservationHandler);
    sln.configureDelayedInput($('#reservation-comment'), changeBeginReservationHandler);
    $("#reservation-people-plus, #reservation-people-min").click(changeBeginReservationHandler);

    $('#reservation_form a, #reservation_form button').nodoubletapzoom();

    $(reservation_details).data('date', new Date());

    sln.registerMsgCallback(channelUpdates);
});
