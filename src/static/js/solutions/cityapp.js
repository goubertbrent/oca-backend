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
$(function() {
    'use strict';
    var uitdatabankStatusEnabled = true;
    var gatherEvents = true;

    var TMPL_SET_GATHER_EVENTS = '<div class="btn-group">' +
        '      <button class="btn btn-success" id="gatherEventsEnabled">' + CommonTranslations.GATHER_EVENTS_DISABLED + '</button>' +
        '      <button class="btn" id="gatherEventsDisabled">&nbsp;</button>' + '</div>';

    var gatherEventsEnabled = function() {
        setGatherEvents(!gatherEvents);
        saveCityAppSettings();
    };

    var gatherEventsDisabled = function() {
        setGatherEvents(!gatherEvents);
        saveCityAppSettings();
    };

    var setGatherEvents = function(newGatherEvents) {
        gatherEvents = newGatherEvents;
        if (newGatherEvents) {
            $('#gatherEventsEnabled').addClass("btn-success").text(CommonTranslations.GATHER_EVENTS_ENABLED);
            $('#gatherEventsDisabled').removeClass("btn-danger").html('&nbsp;');
        } else {
            $('#gatherEventsEnabled').removeClass("btn-success").html('&nbsp;');
            $('#gatherEventsDisabled').addClass("btn-danger").text(CommonTranslations.GATHER_EVENTS_DISABLED);
        }
    };

    $(".sln-set-gather-events").html(TMPL_SET_GATHER_EVENTS);
    $('#gatherEventsEnabled').click(gatherEventsEnabled);
    $('#gatherEventsDisabled').click(gatherEventsDisabled);

    $("#topmenu li a").click(menuPress);

    var saveCityAppSettings = function() {
        var data = JSON.stringify({
            gather_events: gatherEvents,
        });
        sln.call({
            url: "/common/cityapp/settings/save",
            type: "POST",
            data: {
                data: data
            },
            success: function(data) {
                if (!data.success) {
                    sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
            },
            error: sln.showAjaxError
        });
    };

    var loadCityAppSettings = function() {
        sln.call({
            url: "/common/cityapp/settings/load",
            type: "GET",
            success: function(data) {
                setGatherEvents(data.gather_events);
            },
            error: sln.showAjaxError
        });
    };

    var saveUitdatabankSettings = function() {
        var allOK = true;
        var version = $("#sln-uit-events-version").val();
        var params = {};
        if (version == "1") {
            if ($('#section_settings_agenda .sln-uit-events-1-key input').val() === "") {
                $('#section_settings_agenda .sln-uit-events-1-key input').addClass("error");
                allOK = false;
            }
            if ($('#section_settings_agenda .sln-uit-events-1-region input').val() === "") {
                $('#section_settings_agenda .sln-uit-events-1-region input').addClass("error");
                allOK = false;
            }
            params = {
                'key': $('#section_settings_agenda .sln-uit-events-1-key input').val(),
                'region': $('#section_settings_agenda .sln-uit-events-1-region input').val()
            };
        } else if (version == "2") {
            if ($('#section_settings_agenda .sln-uit-events-2-key input').val() === "") {
                $('#section_settings_agenda .sln-uit-events-2-key input').addClass("error");
                allOK = false;
            }
            if ($('#section_settings_agenda .sln-uit-events-2-secret input').val() === "") {
                $('#section_settings_agenda .sln-uit-events-2-secret input').addClass("error");
                allOK = false;
            }
            if ($('#section_settings_agenda .sln-uit-events-2-regions').data('regions') === null) {
                $('#section_settings_agenda .sln-uit-events-2-regions').addClass("error");
                allOK = false;
            } else {
                $('#section_settings_agenda .sln-uit-events-2-regions').removeClass("error");
            }

            params = {
                'key': $('#section_settings_agenda .sln-uit-events-2-key input').val(),
                'secret': $('#section_settings_agenda .sln-uit-events-2-secret input').val(),
                'regions': $('#section_settings_agenda .sln-uit-events-2-regions').data('regions')
            };

        } else if (version == "3") {
            if ($('#section_settings_agenda .sln-uit-events-3-key input').val() === "") {
                $('#section_settings_agenda .sln-uit-events-3-key input').addClass("error");
                allOK = false;
            }
            if ($('#section_settings_agenda .sln-uit-events-3-postal-codes').data('postal_codes') === null) {
                $('#section_settings_agenda .sln-uit-events-3-postal-codes').addClass("error");
                allOK = false;
            } else {
                $('#section_settings_agenda .sln-uit-events-3-postal-codes').removeClass("error");
            }

            params = {
                'key': $('#section_settings_agenda .sln-uit-events-3-key input').val(),
                'postal_codes': $('#section_settings_agenda .sln-uit-events-3-postal-codes').data('postal_codes')
            };
        } else {
            allOk = false;
        }
        if (allOK) {
            var data = JSON.stringify({
                version: version,
                params: params,
            });
            sln.call({
                url: "/common/cityapp/uitdatabank/settings",
                type: "POST",
                data: {
                    data: data
                },
                success: function(data) {
                    if (!data.success) {
                        sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    } else {
                        sln.call({
                            url: "/common/cityapp/uitdatabank/check",
                            type: "GET",
                            success: function(data) {
                                if (data.success) {
                                    setUitdatabankStatus(true);
                                } else {
                                    setUitdatabankStatus(false, data.errormsg);
                                }
                            },
                            error: sln.showAjaxError
                        });
                    }
                },
                error: sln.showAjaxError
            });
        }
    };

    var loadUitdatabankSettings = function() {
        sln.call({
            url: "/common/cityapp/uitdatabank/settings",
            type: "GET",
            success: function(data) {
                if ($("#section_settings_agenda #sln-uit-events-version").length === 0) {
                    return;
                }
                setUitdatabankStatus(data.enabled);

                $("#section_settings_agenda .sln-uit-events-1").hide();
                $("#section_settings_agenda .sln-uit-events-2").hide();
                $("#section_settings_agenda .sln-uit-events-3").hide();

                $("#sln-uit-events-version").val(data.version);
                if (data.version == "1") {
                    $("#section_settings_agenda .sln-uit-events-1").show();
                    $("#section_settings_agenda .sln-uit-events-1-key input").val(data.params ? data.params.key : "");
                    $("#section_settings_agenda .sln-uit-events-1-region input").val(data.params ? data.params.region : "");

                } else if (data.version == "2") {
                	var regions = data.params ? data.params.regions : [];
                    $("#section_settings_agenda .sln-uit-events-2").show();
                    $("#section_settings_agenda .sln-uit-events-2-key input").val(data.params ? data.params.key : "");
                    $("#section_settings_agenda .sln-uit-events-2-secret input").val(data.params ? data.params.secret : "");
                    $("#section_settings_agenda .sln-uit-events-2-regions").data('regions', regions);
                    renderRegions(regions);

                } else if (data.version == "3") {
                	var postal_codes = data.params ? data.params.postal_codes : [];
                    $("#section_settings_agenda .sln-uit-events-3").show();
                    $("#section_settings_agenda .sln-uit-events-3-key input").val(data.params ? data.params.key : "");
                    $("#section_settings_agenda .sln-uit-events-3-postal-codes").data('postal_codes', postal_codes);
                    renderPostalCodes(postal_codes);
                }
            },
            error: sln.showAjaxError
        });
    };

    var setUitdatabankStatus = function(enabled, reason) {
        uitdatabankStatusEnabled = enabled;
        $('#uitdatabankStatus').toggleClass('alert-danger', !enabled).toggleClass('alert-success', enabled);
        var text = CommonTranslations.STATUS_ENABLED;
        if (!enabled) {
            text = CommonTranslations.STATUS_DISABLED + (reason === undefined ? "" : (": " + reason));
        }
        $('#uitdatabankStatusText').text(text);
    };

    var deleteRegion = function() {
        var region = $(this).attr('region');
        var htmlElement = $('.sln-uit-events-2-regions');
        var index = htmlElement.data('regions').indexOf(region);
        if (index >= 0) {
            htmlElement.data('regions').splice(index, 1);
            renderRegions(htmlElement.data('regions'));
            saveUitdatabankSettings();
        }
    };

    var renderRegions = function(regions) {
        var htmlElement = $('.sln-uit-events-2-regions table tbody');
        htmlElement.empty();
        var html = $.tmpl(templates.events_uitcalendar_settings, {
            regions: regions
        });
        htmlElement.append(html);
        htmlElement.find('button[action="deleteRegion"]').click(deleteRegion);
    };

    var deletePostalCode = function() {
        var region = $(this).attr('region');
        var htmlElement = $('.sln-uit-events-3-postal-codes');
        var index = htmlElement.data('postal_codes').indexOf(region);
        if (index >= 0) {
            htmlElement.data('postal_codes').splice(index, 1);
            renderPostalCodes(htmlElement.data('postal_codes'));
            saveUitdatabankSettings();
        }
    };

    var renderPostalCodes = function(postalCodes) {
        var htmlElement = $('.sln-uit-events-3-postal-codes table tbody');
        htmlElement.empty();
        var html = $.tmpl(templates.events_uitcalendar_settings, {
            regions: postalCodes
        });
        htmlElement.append(html);
        htmlElement.find('button[action="deleteRegion"]').click(deletePostalCode);
    };

    $(".sln-set-events-uit-settings").show();

    $("#sln-uit-events-version").change(function() {
        var version = $("#sln-uit-events-version").val();
        setUitdatabankStatus(false);

        $("#section_settings_agenda .sln-uit-events-1").hide();
        $("#section_settings_agenda .sln-uit-events-2").hide();
        $("#section_settings_agenda .sln-uit-events-3").hide();

        if (version == "1") {
            $("#section_settings_agenda .sln-uit-events-1").show();
            $("#section_settings_agenda .sln-uit-events-1-key input").val("");
            $("#section_settings_agenda .sln-uit-events-1-region input").val("");

        } else if (version == "2") {
            $("#section_settings_agenda .sln-uit-events-2").show();
            $("#section_settings_agenda .sln-uit-events-2-key input").val("");
            $("#section_settings_agenda .sln-uit-events-2-secret input").val("");
            $("#section_settings_agenda .sln-uit-events-2-regions").data('regions', []);
            renderRegions([]);

        } else if (version == "3") {
            $("#section_settings_agenda .sln-uit-events-3").show();
            $("#section_settings_agenda .sln-uit-events-3-key input").val("");
            $("#section_settings_agenda .sln-uit-events-3-postal-codes").data('postal_codes', []);
            renderPostalCodes([]);
        }
    });

    sln.configureDelayedInput($('.sln-uit-events-1-key input'), saveUitdatabankSettings);
    sln.configureDelayedInput($('.sln-uit-events-1-region input'), saveUitdatabankSettings);

    sln.configureDelayedInput($('.sln-uit-events-2-key input'), saveUitdatabankSettings);
    sln.configureDelayedInput($('.sln-uit-events-2-secret input'), saveUitdatabankSettings);
    $('#sln-uit-events-2-add-region').click(function() {
        sln.input(function(value) {
            if (!value.trim())
                return false;

            var elem = $('.sln-uit-events-2-regions');
            elem.data('regions').push(value);
            renderRegions(elem.data('regions'));
            saveUitdatabankSettings();

        }, CommonTranslations.ADD, CommonTranslations.SAVE, CommonTranslations.ENTER_DOT_DOT_DOT, null, null, CommonTranslations.uit_region_format_info);
    });

    sln.configureDelayedInput($('.sln-uit-events-3-key input'), saveUitdatabankSettings);
    $('#sln-uit-events-3-add-postal-code').click(function() {
        sln.input(function(value) {
            if (!value.trim())
                return false;

            var elem = $('.sln-uit-events-3-postal-codes');
            elem.data('postal_codes').push(value);
            renderPostalCodes(elem.data('postal_codes'));
            saveUitdatabankSettings();

        }, CommonTranslations.ADD, CommonTranslations.SAVE, CommonTranslations.ENTER_DOT_DOT_DOT, null, null, null);
    });


    loadCityAppSettings();
    loadUitdatabankSettings();

    function menuPress() {
        $("#topmenu li").removeClass("active");
        var li = $(this).parent().addClass("active");
        $("div.page").hide();
        $("div#" + li.attr("menu")).show();
    }
});