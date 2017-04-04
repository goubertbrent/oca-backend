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

"use strict";
var settingsBranding,
    COLOR_REGEX = /^(([A-F0-9]{2}){3})$/i;

function showSettingsBranding () {
    // Only render when it's not cached in the DOM yet
    if (!settingsBranding) {
        renderSettingsBranding();
    }
}

function renderSettingsBranding () {
    $('#branding_settings').html(TMPL_LOADING_SPINNER);
    getSettingsBranding(function (settings) {
        var elemBrandingSettings = $('#branding_settings');
        settingsBranding = settings;
        var html = $.tmpl(templates['settings/settings_branding'], {
            t: CommonTranslations,
            brandingSettings: settingsBranding.branding_settings
        });
        elemBrandingSettings.html(html);
        renderSettingsBrandingPreview();

        //bind events

        var elemColorScheme = $("#color_scheme"),
            elemShowName = $('#show_name');

        elemColorScheme.change(function () {
            settingsBranding.branding_settings.color_scheme = elemColorScheme.val();
            recolorPreviewFrame();
        });

        elemShowName.change(function () {
            settingsBranding.branding_settings.show_identity_name = $(this).prop('checked');
            $('#nuntiuz_identity_name_holder', $("#preview_frame").contents())
                .toggle(settingsBranding.branding_settings.show_identity_name);
            resizeBranding();
        });

        $('#logo_div').click(function () {
            // uploadLogo is globally defined in sln-settings.js
            uploadLogo(renderSettingsBranding);
        });

        $('#save_button', elemBrandingSettings).click(function () {
            var $this = $(this);
            $this.text(CommonTranslations.SAVING_DOT_DOT_DOT);
            sln.call({
                url: "/common/settings/branding",
                type: "POST",
                data: {
                    branding_settings: settingsBranding.branding_settings
                },
                success: function (data) {
                    $this.text(CommonTranslations.SAVE);
                    if (!data.success) {
                        return sln.alert(data.errormsg);
                    }
                },
                error: function () {
                    $this.text(CommonTranslations.ERROR);
                    setTimeout(function () {
                        $this.text(CommonTranslations.SAVE);
                    }, 10000);
                    sln.showAjaxError();
                }
            });
        });

        $('.color-picker', elemBrandingSettings).on('input', colorPickerChanged);
        $('.color', elemBrandingSettings).on('input', colorChanged);
        sln.fixColorPicker($('#text_color'), $("#text_color_picker"), fixedColourPickerChanged);
        sln.fixColorPicker($('#background_color'), $("#background_color_picker"), fixedColourPickerChanged);
        sln.fixColorPicker($('#menu_item_color'), $("#menu_item_color_picker"), fixedColourPickerChanged);

        function colorPickerChanged () {
            var pickerInput = $(this);
            var pickerId = pickerInput.attr('id').replace('_picker', '');
            var colour = pickerInput.val().substring(1);
            var colourValid = colour && COLOR_REGEX.test(colour);
            var colourPicker = $('#' + pickerId);
            colourPicker.parent().parent().toggleClass('error', !colourValid);
            if (colourValid) {
                settingsBranding.branding_settings[pickerId] = colour;
                colourPicker.val(colour);
                recolorPreviewFrame();
            }
        }

        function colorChanged () {
            var colorInput = $(this);
            var colour = colorInput.val().replace('#', '');
            var colorInputId = colorInput.attr('id');
            var colourValid = colour && COLOR_REGEX.test(colour);
            colorInput.parent().parent().toggleClass('error', !colourValid);
            if (colourValid) {
                settingsBranding.branding_settings[colorInputId] = colour;
                $('#' + colorInputId + '_picker').val('#' + colour);
                recolorPreviewFrame();
            }
        }

        function fixedColourPickerChanged () {
            var colorInput = $(this);
            var colorInputText = colorInput.find('input[type=text]');
            var colour = colorInputText.val().replace('#', '');
            var colourValid = colour && COLOR_REGEX.test(colour);
            colorInput.parent().parent().toggleClass('error', !colourValid);
            if (colourValid) {
                settingsBranding.branding_settings[colorInputText.attr('id')] = colour;
                recolorPreviewFrame();
            }
        }
    });
}

function getSettingsBranding (callback) {
    if (!settingsBranding) {
        loadSettingsBranding(callback);
    } else {
        callback(settingsBranding);
    }
}

function loadSettingsBranding (callback) {
    sln.call({
        url: "/common/settings/branding_and_menu",
        type: "GET",
        success: callback
    });
}

var previewRenderingTimeout;

function recolorPreviewFrame () {
    var css = {
        'background-color': '#' + settingsBranding.branding_settings.background_color,
        'color': '#' + settingsBranding.branding_settings.text_color,
        'overflow': 'hidden'
        };
    var canvas = $('#canvas').css('background-color', '#' + settingsBranding.branding_settings.background_color);
    $('#preview_frame').contents().find('body').css(css);

    if (previewRenderingTimeout) {
        clearTimeout(previewRenderingTimeout);
    }
    previewRenderingTimeout = setTimeout(function () {
        $('.service-menu-preview').find('td')
            .removeClass().addClass('rt-cs-' + settingsBranding.branding_settings.color_scheme)
            .find('i.fa').css('color', '#' + settingsBranding.branding_settings.menu_item_color);
        canvas.find('td').find('img').each(function () {
            var $this = $(this);
            var src = $this.attr('src');
            $this.attr('src', src.split('=')[0] + '=' + settingsBranding.branding_settings.menu_item_color);
        });
    }, 300);
}

function renderSettingsBrandingPreview () {
    var html = $.tmpl(templates['settings/settings_branding_preview'], {
        t: CommonTranslations,
        brandingSettings: settingsBranding.branding_settings,
        menuItems: settingsBranding.menu_item_rows
    });
    $('#branding_settings_preview').html(html);

    recolorPreviewFrame();

    //bind events
    var elemIframe = $('#preview_frame').load(function () {
        $('#nuntiuz_identity_name_holder', elemIframe.contents())
            .toggle(settingsBranding.branding_settings.show_identity_name);
        resizeBranding();
    });
}

function resizeBranding () {
    var elemIFrame = $("#preview_frame").height(50);
    var iframeDocument = elemIFrame.contents().first();
    if (iframeDocument && iframeDocument.length) {
        var height = 120;
        try {
            height = iframeDocument.height() + 5;
        } catch (ex) {
        }
        elemIFrame.height(height + 5);
    }
}
