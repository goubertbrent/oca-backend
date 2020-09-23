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
$(function() {
    'use strict';

    var saveUitdatabankSettings = function() {
        var allOK = true;
        var version = "3";
        var params = {};

        if ($('#section_agenda .sln-uit-events-3-key input').val() === "") {
            $('#section_agenda .sln-uit-events-3-key input').addClass("error");
            allOK = false;
        }
        if ($('#section_agenda .sln-uit-events-3-postal-codes').data('postal_codes') === null) {
            $('#section_agenda .sln-uit-events-3-postal-codes').addClass("error");
            allOK = false;
        } else {
            $('#section_agenda .sln-uit-events-3-postal-codes').removeClass("error");
        }

        params = {
            'key': $('#section_agenda .sln-uit-events-3-key input').val(),
            'postal_codes': $('#section_agenda .sln-uit-events-3-postal-codes').data('postal_codes')
        };

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
                    	checkUitdatabankSettings();
                    }
                },
                error: sln.showAjaxError
            });
        }
    };

    var checkUitdatabankSettings = function() {
    	sln.call({
            url: "/common/cityapp/uitdatabank/check",
            type: "GET",
            success: function(data) {
                $('#uitdatabankStatus').toggleClass('alert-danger', !data.enabled).toggleClass('alert-success', data.enabled);
                var text = CommonTranslations.STATUS_ENABLED;
                if (data.enabled) {
                    text = CommonTranslations.STATUS_ENABLED + " (" + data.count + " events found)";
                } else {
                	text = CommonTranslations.STATUS_DISABLED + (data.errormsg === undefined ? "" : (": " + data.errormsg));
                }
                $('#uitdatabankStatusText').text(text);
            },
            error: sln.showAjaxError
        });
    };

    var loadUitdatabankSettings = function() {
        sln.call({
            url: "/common/cityapp/uitdatabank/settings",
            type: "GET",
            success: function(data) {
            	checkUitdatabankSettings();

                $("#section_agenda .sln-uit-events-3").hide();

              	var postal_codes = data.params ? data.params.postal_codes : [];
                $("#section_agenda .sln-uit-events-3").show();
                $("#section_agenda .sln-uit-events-3-key input").val(data.params ? data.params.key : "");
                $("#section_agenda .sln-uit-events-3-postal-codes").data('postal_codes', postal_codes);
                renderPostalCodes(postal_codes);
            },
            error: sln.showAjaxError
        });
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

    loadUitdatabankSettings();
});
