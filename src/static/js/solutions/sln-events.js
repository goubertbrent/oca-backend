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
    var DEFAULT_START_EPOCH = 20 * 3600;
    var DEFAULT_UNTIL_EPOCH = 4 * 3600;

    var currentCalendarId = null;
    var currentSettingsCalendarId = null;
    var currentSettingsCalendarModal = null;
    var currentGoogleAuthenticateWindow = null;
    var calendarsIds = null;
    var calendarsMap = null;
    var calendarsArray = null;

    var to_epoch = function (textField) {
        return Math.floor(textField.data('datepicker').date.valueOf() / 1000);
    };

    var eventStartChanged = function (e) {
        var div = $(this).parent().parent();
        var d = div.data("date");
        d.start = e.time.hours * 3600 + e.time.minutes * 60;
        div.data("date", d);
    };

    var eventUntilChanged = function (e) {
        var div = $(this).parent().parent();
        var d = div.data("date");
        d.end = e.time.hours * 3600 + e.time.minutes * 60;
        div.data("date", d);
    };

    var loadCalendars = function () {
        sln.call({
            url: "/common/calendar/load",
            type: "GET",
            success: function (data) {
                calendarsArray = data;
                calendarsMap = {};
                calendarsIds = [];

                calendarsArray.sort(function (calendar1, calendar2) {
                    return sln.smartSort(calendar1.name, calendar2.name);
                });

                $.each(data, function (i, calendar) {
                    calendar.loading = false;
                    calendarsMap[calendar.id] = calendar;
                    calendarsIds.push(calendar.id);
                });
                renderEvents();
                renderCalendarSettings();
            },
            error: sln.showAjaxError
        });
    };

    var loadUitId = function () {
        sln.call({
            url: "/common/events/uit/actor/load",
            type: "GET",
            success: function (data) {
                if (data) {
                    $('.sln-set-events-uit-actor input').val(data);
                }
            },
            error: sln.showAjaxError
        });
    };

    var putUitId = function () {
        sln.showProcessing(CommonTranslations.SAVING_DOT_DOT_DOT);
        sln.call({
            url: "/common/events/uit/actor/put",
            type: "POST",
            data: {
                data: JSON.stringify({
                    uit_id: $('.sln-set-events-uit-actor input').val()
                })
            },
            success: function (data) {
                sln.hideProcessing();
            },
            error: sln.showAjaxError
        });
    };

    var addEvent = function () {
        var calendarId = parseInt($(this).attr("calendar_id"));

        var html = $.tmpl(templates.events_add, {
            header: T('events-add'),
            cancelBtn: CommonTranslations.CANCEL,
            submitBtn: CommonTranslations.SAVE,
            CommonTranslations: CommonTranslations
        });

        var dates = [{
            key: sln.uuid(),
            date: sln.today(),
            start: DEFAULT_START_EPOCH,
            end: DEFAULT_UNTIL_EPOCH
        }];

        var dates_html = $.tmpl(templates.events_add_dates, {
            dates: dates,
            CommonTranslations: CommonTranslations
        });

        $(".dates", html).html(dates_html);
        $('div[date_key="' + dates[0].key + '"] .eventStartDate', html).datepicker({
            format: sln.getLocalDateFormat()
        }).datepicker('setValue', dates[0].date);

        $('div[date_key="' + dates[0].key + '"] .eventTimeStart', html).timepicker({
            defaultTime: "18:00",
            showMeridian: false
        });

        $('div[date_key="' + dates[0].key + '"] .eventTimeEnd', html).timepicker({
            defaultTime: "20:00",
            showMeridian: false
        });

        $('div[date_key="' + dates[0].key + '"]', html).data("date", dates[0]);

        $('.eventTimeStart', html).on('changeTime.timepicker', eventStartChanged);
        $('.eventTimeEnd', html).on('changeTime.timepicker', eventUntilChanged);

        $('#existingEventPicture', html).hide();

        var modal = sln.createModal(html);

        $('button[action="date_add"]', modal).click(function () {
            addNewEventDate(html);
        });

        $('button[action="delete"]', modal).click(function () {
            var dateKey = $(this).attr("date_key");
            $('div[date_key="' + dateKey + '"]').remove();
        });

        $('button[action="submit"]', modal).click(function () {
            var event = {
                calendar_id: calendarId,
                media: [],
            };
            saveEvent(event, modal);
        });
    };

    var addNewEventDate = function (html) {
        var d = sln.today();
        d.setDate(d.getDate() + $(".dates > div", html).length);
        var dates = [{
            "key": sln.uuid(),
            "date": d,
            "start": DEFAULT_START_EPOCH,
            "end": DEFAULT_UNTIL_EPOCH
        }];

        var dates_html = $.tmpl(templates.events_add_dates, {
            dates: dates,
            CommonTranslations: CommonTranslations
        });

        $('button[action="delete"]', dates_html).click(function () {
            var dateKey = $(this).attr("date_key");
            $('div[date_key="' + dateKey + '"]').remove();
        });

        $('.eventStartDate', html)
            .datepicker({format: sln.getLocalDateFormat()})
            .datepicker('setValue', dates[0].date);

        $('.eventTimeStart', html).timepicker({
            defaultTime: "18:00",
            showMeridian: false
        });

        $('.eventTimeEnd', html).timepicker({
            defaultTime: "20:00",
            showMeridian: false
        });

        $('.eventTimeStart', dates_html).on('changeTime.timepicker', eventStartChanged);
        $('.eventTimeEnd', dates_html).on('changeTime.timepicker', eventUntilChanged);

        $(".dates", html).append(dates_html);
        $('div[date_key="' + dates[0].key + '"]', html).data("date", dates[0]);
    };

    var saveEvent = function (event, modal) {
        sln.showProcessing(CommonTranslations.SAVING_DOT_DOT_DOT);
        var periods = [];

        $('.dates > div', modal).each(function () {
            var d = $(this).data("date");
            var dateEpoch = to_epoch($(".eventStartDate", $(this)));
            var selectDate = new Date((dateEpoch + d.start) * 1000);
            var endDate = new Date((dateEpoch + d.end) * 1000);
            periods.push({
                start: {datetime: selectDate},
                end: {datetime: endDate},
            });
        });

        periods.sort(function (a, b) {
            return a.start.datetime - b.start.datetime;
        });

        function submitEvent(picture) {
            event = Object.assign(event, {
                title: $("#eventTitle").val(),
                place: $("#eventPlace").val(),
                organizer: $("#eventOrganizer").val(),
                description: $("#eventDescription").val(),
                external_link: $("#eventUrl").val(),
                start_date: periods[0].start.datetime,
                end_date: periods[periods.length - 1].end.datetime,
                periods: periods,
                picture: picture,
            });
            return Requests.createEvent(event, {showError: false}).then(function () {
                sln.hideProcessing();
                loadCalendars();
                modal.modal('hide');
            }).catch(function (err) {
                sln.hideProcessing();
                sln.alert(err.responseJSON.error);
            });
        }

        // Resize image on the client
        var eventPictureElement = document.getElementById('eventPicture');
        if (eventPictureElement.files.length > 0) {
            var file = eventPictureElement.files[0];

            var canvas = document.createElement("canvas");
            var ctx = canvas.getContext("2d");
            var reader = new FileReader();
            reader.onload = function (e) {
                var img = new Image();
                img.onload = function () {
                    var MAX_WIDTH = 1920;
                    var width = img.width;
                    var height = img.height;

                    if (width > MAX_WIDTH) {
                        height *= MAX_WIDTH / width;
                        width = MAX_WIDTH;
                    }

                    canvas.width = width;
                    canvas.height = height;

                    ctx.drawImage(img, 0, 0, width, height);
                    var picture = canvas.toDataURL("image/png");
                    submitEvent(picture);
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        } else {
            submitEvent();
        }
    };

    var editEvent = function () {
        var eventId = parseInt($(this).attr("event_id"));
        var calendarId = parseInt($(this).attr("calendar_id"));
        var event = getEventById(calendarId, eventId);

        var picture = $('img.event-picture', $(this).closest('tr'));
        var html = $.tmpl(templates.events_add, {
            header: T('event-edit'),
            cancelBtn: CommonTranslations.CANCEL,
            submitBtn: CommonTranslations.SAVE,
            CommonTranslations: CommonTranslations
        });

        var dates = [];
        if (event.periods.length === 0) {
            event.periods = [{
                start: {datetime: event.start_date},
                end: {datetime: event.end_date}
            }];
        }
        for (const period of event.periods) {
            var startDate = new Date(period.start.datetime);
            var endDate = new Date(period.end.datetime);
            var startDateOnly = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate());
            dates.push({
                "key": sln.uuid(),
                "date": startDateOnly,
                "start": startDate.getHours() * 3600 + startDate.getMinutes() * 60,
                "end": endDate.getHours() * 3600 + endDate.getMinutes() * 60
            });
        }

        var dates_html = $.tmpl(templates.events_add_dates, {
            dates: dates,
            CommonTranslations: CommonTranslations
        });

        $(".dates", html).html(dates_html);

        if (picture.length > 0) {
            $("#existingEventPicture img", html).attr('src', picture.attr('src'));
            $("#existingEventPicture button", html).click(function () {
                var url = $("#existingEventPicture img", html).attr('src');
                event.media = event.media.filter(function (m) {
                    return m.url !== url;
                });
                $("#existingEventPicture img", html).attr('src', '');
                $("#existingEventPicture", html).hide();
            });
            $('#eventPicture', html).change(function () {
                $('#existingEventPicture img', html).attr('src', '');
                $('#existingEventPicture', html).hide();
            });
        } else {
            $("#existingEventPicture", html).hide();
        }

        $('#eventTitle', html).val(event.title);
        $('#eventPlace', html).val(event.place);
        $('#eventOrganizer', html).val(event.organizer);
        $('#eventDescription', html).val(event.description);
        $('#eventUrl', html).val(event.external_link);

        $('.eventTimeStart', html).timepicker({
            defaultTime: "18:00",
            showMeridian: false
        });

        $('.eventTimeEnd', html).timepicker({
            defaultTime: "20:00",
            showMeridian: false
        });

        $.each(dates, function (i, d) {
            $('div[date_key="' + d.key + '"]', html).data("date", d);
            $('div[date_key="' + d.key + '"] .eventStartDate', html).datepicker({
                format: sln.getLocalDateFormat()
            }).datepicker('setValue', d.date);

            $('div[date_key="' + d.key + '"] .eventTimeStart', html).timepicker('setTime', sln.intToTime(d.start));
            $('div[date_key="' + d.key + '"] .eventTimeEnd', html).timepicker('setTime', sln.intToTime(d.end));
        });

        $('.eventTimeStart', html).on('changeTime.timepicker', eventStartChanged);
        $('.eventTimeEnd', html).on('changeTime.timepicker', eventUntilChanged);

        var modal = sln.createModal(html, function () {
            $("#itemName", modal).focus();
        });

        $('button[action="date_add"]', modal).click(function () {
            addNewEventDate(html);
        });

        $('button[action="delete"]', modal).click(function () {
            var dateKey = $(this).attr("date_key");
            $('div[date_key="' + dateKey + '"]').remove();
        });

        $('button[action="submit"]', modal).click(function () {
            saveEvent(event, modal);
        });
    };

    var deleteEvent = function () {
        var eventId = $(this).attr("event_id");
        sln.call({
            url: "/common/events/delete",
            type: "POST",
            data: {
                data: JSON.stringify({
                    event_id: parseInt(eventId)
                })
            },
            success: function (data) {
                if (!data.success) {
                    sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    return;
                }
                loadCalendars();
            },
            error: sln.showAjaxError
        });
    };

    var renderEvents = function () {
        var html = $.tmpl(templates.events, {
            calendars: calendarsArray,
            user_email: service_user_email,
            T: T
        });
        $("#events #calendars").empty().append(html);

        $.each(calendarsArray, function (i, calendar) {
            renderEventsForCalendar(calendar.id);
        });

        if (currentCalendarId !== null && ($("#" + currentCalendarId).length > 0)) {
            var activeSection = "section_calendar_" + calendarsIds[0];
            $("#events #calendars li[section=" + activeSection + "]").removeClass("active");
            $("#" + activeSection).css("display", 'none');

            $("#events #calendars li[section=" + currentCalendarId + "]").addClass("active");
            $("#" + currentCalendarId).css("display", 'block');
        } else {
            var activeSection = "section_calendar_" + calendarsIds[0];
            $("#events #calendars li[section=" + activeSection + "]").addClass("active");
            $("#" + activeSection).css("display", 'block');
            currentCalendarId = activeSection;
        }

        $("#calendars .addevent").click(addEvent);
        $("#events li a").click(calendarsTabPress);
    };

    function getEventById(calendarId, id) {
        return calendarsMap[calendarId].events.find(function (e) {
            return e.id === id;
        });
    }

    var renderEventsForCalendar = function (calendarId) {
        var calendar = calendarsMap[calendarId];
        calendar.events.sort(function (a, b) {
            return new Date(a.start_date) - new Date(b.start_date);
        });
        calendar.events = calendar.events.map(function (event) {
            var startDate = new Date(event.start_date);
            var endDate = new Date(event.end_date);
            event.startEpoch = startDate.getTime();
            event.end = new Date(event.end_date);
            if (event.periods.length === 0) {
                event.date = sln.parseDateToEventDateTime(startDate) + ' - ' + sln.parseDateToEventDateTime(endDate);
            } else {
                event.date = '';
                for (const period of event.periods) {
                    var start = new Date(period.start.date || period.start.datetime);
                    var end = new Date(period.end.date || period.end.datetime);
                    event.date += sln.parseDateToEventDateTime(start) + ' - ' + sln.parseDateToEventDateTime(end) + '<br>';
                }
            }
            event.htmlDescription = sln.htmlize(event.description);
            return event;
        });

        var html = $.tmpl(templates.events_events, {
            events: calendar.events,
            user_email: service_user_email,
            CommonTranslations: CommonTranslations
        });

        $("#events #calendars #section_calendar_" + calendarId + " table tbody").empty().append(html);
        $("#events #calendars #section_calendar_" + calendarId + " .load-more").toggle(calendar.has_more);

        $('#calendars #section_calendar_' + calendarId + ' button[action="editEvent"]').click(editEvent);
        $('#calendars #section_calendar_' + calendarId + ' button[action="deleteEvent"]').click(deleteEvent);
    };

    var renderCalendarSettings = function () {
        var menuHtmlElement = $("#section_agenda_calendars tbody");
        menuHtmlElement.empty();

        var html = $.tmpl(templates.events_settings, {
            calendars: calendarsArray,
            user_email: service_user_email,
            CommonTranslations: CommonTranslations
        });

        menuHtmlElement.append(html);
        $('#section_agenda_calendars tbody button[action="editCalendar"]').click(editCalendar);
        $('#section_agenda_calendars tbody button[action="adminCalendar"]').click(function () {
            renderCalendarSettingsDetail(parseInt($(this).attr("calendar_id")));
        });
        $('#section_agenda_calendars tbody button[action="deleteCalendar"]').click(deleteCalendar);

        if (currentSettingsCalendarId) {
            loadGoogleCalendarStatus();
        }
    };

    var addCalendar = function () {
        var calendarId = null;
        sln.input(function (value) {
            saveCalendar(calendarId, value);
        }, T('create-new-calendar'), CommonTranslations.ADD, CommonTranslations.ENTER_DOT_DOT_DOT);
    };

    var editCalendar = function () {
        var calendarId = parseInt($(this).attr("calendar_id"));
        var calendar = calendarsMap[calendarId];
        sln.input(function (value) {
            saveCalendar(calendarId, value);
        }, CommonTranslations.EDIT, CommonTranslations.SAVE, CommonTranslations.ENTER_DOT_DOT_DOT, calendar.name);
    };

    var renderCalendarSettingsDetail = function (calendarId) {
        currentSettingsCalendarId = calendarId;
        var calendar = calendarsMap[calendarId];

        var html = $.tmpl(templates.events_calendar_settings, {
            header: CommonTranslations.SETTINGS,
            cancelBtn: CommonTranslations.CLOSE,
            CommonTranslations: CommonTranslations,
            calendar: calendar
        });

        var modal = sln.createModal(html);

        modal.on('hidden', function () {
            currentSettingsCalendarId = null;
            currentSettingsCalendarModal = null;
        });

        currentSettingsCalendarModal = modal;

        $("#authorize-google-calendar", currentSettingsCalendarModal).click(function () {
            handleAuthClick();
        });

        $("#save-google-calendar", currentSettingsCalendarModal).click(function () {
            if ($(this).prop("disabled")) {
                return;
            }
            $(this).prop("disabled", true);
            var googleCalendars = [];
            $('#google-calendars input:checked[type="checkbox"]', currentSettingsCalendarModal).each(function () {
                var googleCalendar = $(this).data("calendar");
                googleCalendars.push({
                    key: googleCalendar.key,
                    label: googleCalendar.label
                });
            });
            sln.call({
                url: "/common/calendar/import/google/put",
                type: "POST",
                data: {
                    calendar_id: currentSettingsCalendarId,
                    google_calendars: googleCalendars
                },
                success: function (data) {
                    if (!data.success) {
                        return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    }
                    currentSettingsCalendarModal.modal('hide');
                    loadCalendars();
                },
                error: sln.showAjaxError
            });
        });

        loadGoogleCalendarStatus();
    };

    var deleteCalendar = function () {
        var calendarId = parseInt($(this).attr("calendar_id"));
        var calendar = calendarsMap[calendarId];
        if (calendar.events.length > 0) {
            sln.alert(sln.htmlize(T('calendar-remove-failed-has-events')), null, T('remove-failed'));

        } else {
            sln.call({
                url: "/common/calendar/delete",
                type: "POST",
                data: {
                    data: JSON.stringify({
                        calendar_id: calendarId
                    })
                },
                success: function (data) {
                    if (!data.success) {
                        sln.alert(sln.htmlize(data.errormsg), null, CommonTranslations.ERROR);
                        return;
                    }
                    loadCalendars();
                },
                error: sln.showAjaxError
            });
        }

    };

    var saveCalendar = function (calendarId, calendarName) {
        sln.call({
            url: "/common/calendar/save",
            type: "POST",
            data: {
                calendar: {
                    id: calendarId,
                    name: calendarName,
                    events: [],
                }
            },
            success: function (data) {
                if (!data.success) {
                    sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    return;
                }
                loadCalendars();
            },
            error: sln.showAjaxError
        });
    };

    var channelUpdates = function (data) {
        if (data.type === 'solutions.common.calendar.update') {
            loadCalendars();
        } else if (data.type === 'solutions.common.calendar.google.callback') {
            if (currentSettingsCalendarId === data.calendar_id) {
                currentGoogleAuthenticateWindow.close();
                loadGoogleCalendarStatus();
            }
        }
    };

    sln.registerMsgCallback(channelUpdates);

    loadCalendars();

    $('.sln-set-events-uit-actor p').html(T('event-uit-actor'));
    $('.sln-set-events-uit-actor').show();
    loadUitId();
    $('.sln-set-events-uit-actor input').change(putUitId);

    var calendarsTabPress = function () {
        $("#events li").removeClass("active");
        var li = $(this).parent().addClass("active");
        currentCalendarId = li.attr("section");
        $("#events section").hide();
        $("#events section#" + currentCalendarId).show();
    };

    $("#section_agenda .add-calendar").click(addCalendar);

    function handleAuthClick() {
        sln.call({
            url: "/common/calendar/google/authenticate/url",
            type: "GET",
            data: {
                calendar_id: currentSettingsCalendarId
            },
            success: function (data) {
                currentGoogleAuthenticateWindow = window.open(data, "", "width=600, height=400");
            },
            error: sln.showAjaxError
        });
    }

    function loadGoogleCalendarStatus() {
        $("#google-calendars-loading", currentSettingsCalendarModal).show();
        $("#authorize-google-calendar", currentSettingsCalendarModal).hide();
        $("#save-google-calendar", currentSettingsCalendarModal).hide();
        $("#google-calendars-none", currentSettingsCalendarModal).hide();
        sln.call({
            url: "/common/calendar/google/load",
            type: "get",
            data: {
                calendar_id: currentSettingsCalendarId
            },
            success: function (data) {
                $("#google-calendars-loading", currentSettingsCalendarModal).hide();
                if (data.enabled) {
                    $("#authorize-google-calendar", currentSettingsCalendarModal).hide();
                    if (data.calendars.length > 0) {
                        $("#save-google-calendar", currentSettingsCalendarModal).show();
                        $("#google-calendars", currentSettingsCalendarModal).show();
                        data.calendars.sort(function (calendar1, calendar2) {
                            return sln.smartSort(calendar1.label, calendar2.label);
                        });
                        var table = $("#google-calendars", currentSettingsCalendarModal);
                        table.empty();

                        for (var i = 0; i < data.calendars.length; i++) {
                            var googleCalendar = data.calendars[i];
                            var tr = $('<tr></tr>');
                            var td_1 = $('<td class="google_calendar"></td>');
                            td_1.text(googleCalendar.label);
                            tr.append(td_1);
                            var td_2 = $('<td style="width: 15px;"></td>');
                            var checkbox = $('<input type="checkbox">');
                            checkbox.val(googleCalendar.key);
                            checkbox.data("calendar", googleCalendar);
                            checkbox.prop('checked', googleCalendar.enabled);
                            td_2.append(checkbox);
                            tr.append(td_2);
                            table.append(tr);
                        }

                        $(".google_calendar", table).click(function (event) {
                            event.stopPropagation();
                            event.preventDefault();
                            var cb = $(this).parent().find("input");
                            cb.prop("checked", !cb.prop("checked"));
                        });
                    } else {
                        $("#google-calendars-none", currentSettingsCalendarModal).show();
                    }
                } else {
                    $("#authorize-google-calendar", currentSettingsCalendarModal).show();
                }
            }
        });
    }

    var eventsMenuItem = $('#topmenu').find('li[menu=events]');
    var calendarsOverview = $("#calendars");

    var validateLoadMore = function () {
        var id_ = calendarsOverview.find(".nav li.active").attr("section");
        if (id_ === undefined) {
            return;
        }
        var calendarId = parseInt(id_.replace("section_calendar_", ""));
        if (calendarsMap[calendarId] === undefined) {
            return;
        }
        var calendarIsOpen = eventsMenuItem.hasClass('active');

        if (calendarIsOpen && sln.isOnScreen($("#" + id_).find("table tr:last"))) {
            if (calendarsMap[calendarId].has_more && calendarsMap[calendarId].loading === false) {
                calendarsMap[calendarId].loading = true;
                sln.call({
                    url: "/common/calendar/load/more",
                    type: "get",
                    data: {
                        calendar_id: calendarId,
                        cursor: calendarsMap[calendarId].cursor
                    },
                    success: function (data) {
                        calendarsMap[calendarId].cursor = data.cursor;
                        calendarsMap[calendarId].has_more = data.has_more;
                        calendarsMap[calendarId].loading = false;
                        for (i = 0; i < data.events.length; i++) {
                            calendarsMap[calendarId].events.push(data.events[i]);
                        }
                        renderEventsForCalendar(calendarId);
                        validateLoadMore();
                    }
                });
            }
        }
    };

    document.getElementById('content-container').addEventListener('scroll', function () {
        validateLoadMore();
    }, {passive: true});
});
