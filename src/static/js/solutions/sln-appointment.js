/*
 * Copyright 2017 GIG Technology NV
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
    var channelUpdates = function(data) {
        if (data.type == "rogerthat.system.channel_connected") {
            loadAppointmentSettings();
            loadAppointmentTimeframes();
        }
        else if (data.type == 'solutions.common.appointment.settings.update') {
            loadAppointmentSettings();
        }
        else if (data.type == 'solutions.common.appointment.settings.timeframe.update') {
            loadAppointmentTimeframes();
        }
    };
    var settingsSection = $('#section_settings_appointment');

    var loadAppointmentSettings = function() {
        sln.call({
            url : "/common/appointment/settings/load",
            type : "GET",
            success : function(data) {
                $("#appointment_settings_text1").val(data.text_1);
            }
        });
    };
    
    var putAppointmentSettings = function() {
        sln.call({
            url : "/common/appointment/settings/put",
            type : "POST",
            data : {
                data : JSON.stringify({
                    text_1: $("#appointment_settings_text1").val()
                })
            },
            success : function(data) {
                if (!data.success) {
                    return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
            }
        });
    };
    
    var initAppointmentTimeframeModal = function(day, time_from, time_until) {
        settingsSection.find('#dates').val(day);
        settingsSection.find('#timepickerEnabledFrom').timepicker('setTime', sln.intToTime(time_from));
        settingsSection.find('#timepickerEnabledUntil').timepicker('setTime', sln.intToTime(time_until));
    };
    
    var loadAppointmentTimeframes = function() {
        sln.call({
            url : "/common/appointment/settings/timeframe/load",
            type : "GET",
            success : function(data) {
                var timeframes = $("#appointment_timeframes tbody");

                data.sort(function(tf1, tf2) {
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

                $.each(data, function(i, d) {
                    d.time_from_str = sln.intToTime(d.time_from, false);
                    d.time_until_str = sln.intToTime(d.time_until, false);
                });

                var html = $.tmpl(templates.timeframe_template, {
                    timeframes: data,
                    type: 'appointment'
                });
                timeframes.empty().append(html);
                $.each(data, function(i, d) {
                    $("#" + d.id).data("timeframe", d);
                });

                $('#appointment_timeframes').find('button[action="edit"]').click(function () {
                    var appointmentId = $(this).attr("timeframe_id");
                    $("#save_appointment_timeframe").attr("timeframe_id", appointmentId);
                    $("#appointmentTimeframeModalLabel").text(CommonTranslations.TIMEFRAME_UPDATE);
                    var timeframe = $("#" + appointmentId).data("timeframe");
                    initAppointmentTimeframeModal(timeframe.day, timeframe.time_from, timeframe.time_until);
                });
                $('#appointment_timeframes').find('button[action=delete]').click(function () {
                    var appointmentId = $(this).attr("timeframe_id");
                    sln.call({
                        url : "/common/appointment/settings/timeframe/delete",
                        type : "POST",
                        data : {
                            data : JSON.stringify({
                                appointment_id: parseInt(appointmentId)
                            })
                        },
                        success : function(data) {
                            if (!data.success) {
                                return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                            }
                        }
                    });
                });
            }
        });
    };
    
    $("#create_appointment_timeframe").click(function() {
        $("#save_appointment_timeframe").attr("timeframe_id", null);
        $("#appointmentTimeframeModalLabel").text(CommonTranslations.TIMEFRAME_CREATE);
        initAppointmentTimeframeModal(0, 9 * 3600, 21 * 3600);
    });

    $("#save_appointment_timeframe").click(function() {
        var old_appointment_id = $(this).attr("timeframe_id");
        var day = parseInt($("#dates").val());
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
            url : "/common/appointment/settings/timeframe/put",
            type : "POST",
            data : {
                data : JSON.stringify({
                    appointment_id: old_appointment_id ? parseInt(old_appointment_id) : null,
                    day : day,
                    time_from : timeFrom,
                    time_until: timeUntil
                })
            },
            success : function(data) {
                if (!data.success) {
                    return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
                $("#appointmentTimeframeModal").modal('hide');
            }
        });
    });

    settingsSection.find('#timepickerEnabledFrom').timepicker({
        defaultTime : "09:00",
        showMeridian : false,
        minuteStep : 5,
        disableFocus : true
    });
    settingsSection.find('#timepickerEnabledUntil').timepicker({
        defaultTime : "21:00",
        showMeridian : false,
        minuteStep : 5,
        disableFocus : true
    });
    
    sln.registerMsgCallback(channelUpdates);
    sln.configureDelayedInput($("#appointment_settings_text1"), putAppointmentSettings);
});
