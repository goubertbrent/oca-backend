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

var brandingScript = function() {
    'use strict';
    var container = "#brandingContainer";
    var brandings = [];
    var lj = mctracker.getLocaljQuery(container);

    var branding_list_template = "<br>"
            + "  <ul>{{each brandings}}"
            + "    <li><b>${$value.description}</b><br>"
            + "        &nbsp;&nbsp;&nbsp;This branding can be used for {{if $value.type == 1}}messages, menu, description and {{/if}}static content<br>"
            + "        &nbsp;&nbsp;&nbsp;key: ${$value.id}<br>"
            + "        &nbsp;&nbsp;&nbsp;created on: ${$value.timestamp} <a class=\"action-link\" name=\"delete\" key=\"${$value.id}\">Delete</a> | <a class=\"action-link\" href=\"/unauthenticated/mobi/branding/${$value.id}\">Download</a> | <a class=\"action-link\" name=\"preview\" key=\"${$value.id}\" description=\"${$value.description}\">Preview</a><br><br>"
            + "    </li>{{/each}}</ul>";

    function applyJQueryInUI() {
        lj("#uploadContainer").panel({
            collapsible : false
        });
        lj("#brandingListContainer").panel({
            collapsible : false
        });
        lj("#upload_button").button().click(upload);
        lj("#branding_designer").click(openBrandingDesigner);
    }

    var upload = function() {
        if (!lj("#description").val()) {
            lj("#description_error").fadeIn('slow');
            return;
        }
        if (!lj("#file").val()) {
            lj("#file_error").fadeIn('slow');
            return;
        }
        mctracker.showProcessing();
        lj("#upload").submit();
        lj("#file_error, #description_error").fadeOut('slow');
    };

    var previewLoaded = function(iframeContents) {
        $('<span id="nuntiuz_identity_name"></span>').text(loggedOnUserName).insertBefore(
                $("nuntiuz_identity_name", iframeContents));

        $('<span id="nuntiuz_timestamp"></span>').text(mctracker.formatDate(new Date().getTime() / 1000)).insertBefore(
                $("nuntiuz_timestamp", iframeContents));
        $(
                '<span id="nuntiuz_message">This is a test message sent to Rogerthat.<br><br>This message includes a custom look and feel, also known as the "branding".</span>')
                .insertBefore($("nuntiuz_message", iframeContents));

    };

    var previewClicked = function() {
        var d = lj("#preview_dialog").clone();
        $("#preview_frame", d).attr('src', '/branding/' + $(this).attr('key') + '/branding.html').load(function() {
            previewLoaded($(this).contents());
        });

        d.dialog({
            width : 445,
            height : 780,
            resizable : false,
            title : $(this).attr('description')
        });
    };

    var loadBrandingList = function() {
        mctracker.call({
            url : '/mobi/rest/branding/list',
            data : {
                filtered_type : -1
            },
            type : 'GET',
            success : function(data) {
                brandings = data;
                $.each(data, function(i, branding) {
                    branding.timestamp = mctracker.formatDate(branding.timestamp, true, false);
                });
                var html = $.tmpl(branding_list_template, {
                    brandings : data
                });
                $("a[name='delete']", html).click(deleteBranding);
                $("a[name='preview']", html).click(previewClicked);
                lj("#branding_list").empty().append(html);
            },
            error : mctracker.showAjaxError
        });
    };

    var deleteBranding = function() {
        var hash = $(this).attr('key');
        mctracker.confirm("Are you sure you want to delete this branding package ?", function() {
            mctracker.call({
                url : '/mobi/rest/branding/delete',
                type : 'POST',
                data : {
                    data : JSON.stringify({
                        key : hash
                    })
                },
                success : function(data, textStatus, XMLHttpRequest) {
                    if (!data) {
                        loadBrandingList();
                    } else {
                        mctracker.alert(data);
                    }
                    mctracker.broadcast({
                        type : "rogerthat.service.branding.refresh"
                    });
                },
                error : function(data, textStatus, XMLHttpRequest) {
                    mctracker.showAjaxError(XMLHttpRequest, textStatus, data);
                }
            });
        });
    };

    var openBrandingDesigner = function() {
        var colorTest = /^([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})$/;
        var staticContentMode = 'disabled';
        var staticContent = '';
        var newLogoBase64 = null;

        var brandingDesignerDialog = lj("#branding_designer_popup").clone().dialog({
            title: 'Branding designer',
            width: 900,
            height: window.innerHeight - 50,
            modal: true,
            buttons: {
                Save: function () {
                    var cfg = getConfiguration();

                    if ((cfg.background_color && !colorTest.test(cfg.background_color))
                        || (cfg.text_color && !colorTest.test(cfg.text_color))
                        || (cfg.menu_item_color && !colorTest.test(cfg.menu_item_color))) {
                        mctracker.alert("Invalid color specified", null, "ERROR");
                        return;
                    }

                    if (!cfg.description) {
                        mctracker.alert("Please enter a description", function () {
                            elemDescription.focus();
                        }, "ERROR");
                        return;
                    }

                    mctracker.call({
                        url: '/mobi/service/branding/editor/save',
                        type: 'POST',
                        data: {
                            data: JSON.stringify(cfg)
                        },
                        success: function (data) {
                            if (data.errormsg) {
                                mctracker.alert(data.errormsg);
                            } else {
                                loadBrandingList();
                                brandingDesignerDialog.dialog('close');
                                mctracker.broadcast({
                                    type: "rogerthat.service.branding.refresh"
                                });
                            }
                        },
                        error: mctracker.showAjaxError
                    });
                },
                Cancel: function () {
                    brandingDesignerDialog.dialog('close');
                }
            }
        }).dialog('open');

        var elemBrandings = $("#brandings", brandingDesignerDialog);
        var elemPreview = $("#preview", brandingDesignerDialog);
        var elemDescription = $("#branding_description", brandingDesignerDialog);
        var elemColorScheme = $("#color_scheme", brandingDesignerDialog);
        var elemBackgroundColor = $("#background_color", brandingDesignerDialog);
        var elemTextColor = $("#text_color", brandingDesignerDialog);
        var elemMenuItemColor = $("#menu_item_color", brandingDesignerDialog);
        var elemStaticContentMode = $("#static_content_mode", brandingDesignerDialog);
        var elemStaticContent = $("#static_content", brandingDesignerDialog);
        var elemLogoPreviewDiv = $('#logo_div', brandingDesignerDialog);

        var configurableElems = [ elemDescription, elemColorScheme, elemBackgroundColor, elemTextColor,
                elemMenuItemColor, elemStaticContentMode, elemStaticContent ];

        function getConfiguration() {
            return {
                description : elemDescription.val(),
                color_scheme : elemColorScheme.val(),
                background_color : elemBackgroundColor.val(),
                text_color : elemTextColor.val(),
                menu_item_color : elemMenuItemColor.val(),
                static_content_mode : staticContentMode,
                static_content: staticContentMode === 'disabled' ? '' : staticContent,
                show_header : false,
                logo: newLogoBase64
            };
        }

        function uploadLogo() {
            var popupHeader = "Change logo";
            var width = 640;
            var height = 240;
            var uploadLogoCompleted = function (logo) {
                newLogoBase64 = logo;
                renderBranding();
            };

            mctracker.uploadImage(popupHeader, width, height, uploadLogoCompleted);
        }

        var getPreviewColor = function(elem) {
            return elem.val() || elem.attr('placeholder');
        };

        var renderPreviewColors = function() {
            var isLight = elemColorScheme.val() == "light";
            elemBackgroundColor.attr('placeholder', isLight ? 'FFFFFF' : '000000');
            elemTextColor.attr('placeholder', isLight ? '000000' : 'FFFFFF');
            elemMenuItemColor.attr('placeholder', isLight ? '000000' : 'FFFFFF');

            $('#background_color_preview', brandingDesignerDialog).css('background-color',
                    '#' + getPreviewColor(elemBackgroundColor));
            $('#text_color_preview', brandingDesignerDialog).css('background-color',
                    '#' + getPreviewColor(elemTextColor));
            $('#menu_item_color_preview', brandingDesignerDialog).css('background-color',
                    '#' + getPreviewColor(elemMenuItemColor));
        };

        var renderBranding = function() {
            var iframeContents = $("iframe", brandingDesignerDialog).contents();
            var body = $("body", iframeContents).css('background-color', '#' + getPreviewColor(elemBackgroundColor))
                    .css('color', '#' + getPreviewColor(elemTextColor));
            var frameImg = $("img#frame", body);
            frameImg.attr('src', frameImg.attr('orig_src') + '?color=' + getPreviewColor(elemBackgroundColor));

            if (elemPreview.val() == "message") {
                $("nuntiuz_identity_name, #nuntiuz_message, #nuntiuz_timestamp", iframeContents).show();
            } else if (elemPreview.val() == "description") {
                $("#nuntiuz_identity_name, #nuntiuz_message", iframeContents).show();
                $("#nuntiuz_timestamp", iframeContents).hide();
            } else { // menu
                $("#nuntiuz_identity_name", iframeContents).show();
                $("#nuntiuz_timestamp, #nuntiuz_message", iframeContents).hide();
            }

            var logo = newLogoBase64 || 'logo.jpg';
            frameImg.css('background-image', "url('" + logo + "')");
            $('img', elemLogoPreviewDiv).attr('src', newLogoBase64 || '/mobi/service/branding/editor/1/logo.jpg');
        };

        elemColorScheme.change(function() {
            renderPreviewColors();
            renderBranding();
        });
        elemPreview.change(renderBranding);
        elemLogoPreviewDiv.click(uploadLogo);

        $("input.color", brandingDesignerDialog).keyup(function() {
            var elem = $(this);
            var elemId = elem.attr('id');
            var color = elem.val();
            var colorPreview = $('#' + elemId + '_preview', brandingDesignerDialog);
            var colorError = $('#' + elemId + '_error', brandingDesignerDialog);
            if (color && !colorTest.test(color)) {
                colorPreview.hide();
                colorError.show();
            } else {
                colorPreview.show();
                colorError.hide();
                renderPreviewColors();
                renderBranding();
            }
        });

        $("iframe", brandingDesignerDialog).load(function() {
            var iframeContents = $(this).contents();
            previewLoaded(iframeContents);
            var frameImg = $("img#frame", iframeContents);
            frameImg.attr('orig_src', frameImg.attr('src'));
            renderBranding();
        });

        var updateStaticContent = function() {
            var iframeContents = $("iframe", brandingDesignerDialog).contents();
            var placeholder = $("#static_content_placeholder", iframeContents);
            if (staticContentMode == "disabled") {
                placeholder.empty();
                staticContent = "";
            } else {
                if (staticContentMode == "plain-text") {
                    placeholder.text(elemStaticContent.val());
                    var html = placeholder.html();
                    placeholder.html(html.replace(/\n/g, '<br>'));
                } else {
                    $("#static_content_placeholder", iframeContents).html(elemStaticContent.val());
                }
                staticContent = placeholder.html();
            }
        };

        elemStaticContentMode.change(function() {
            staticContentMode = elemStaticContentMode.val();
            var iframeContents = $("iframe", brandingDesignerDialog).contents();
            if (staticContentMode != "disabled") {
                elemStaticContent.closest('tr').fadeIn();
                $("#message", iframeContents).hide();
            } else {
                elemStaticContent.closest('tr').fadeOut();
                $("#message", iframeContents).show();
            }
            updateStaticContent();
        });

        elemStaticContent.keyup(updateStaticContent);

        elemBrandings.change(function() {
            var brandingHash = $(this).val();
            if (brandingHash) {
                mctracker.call({
                    url : '/mobi/service/branding/editor/cfg',
                    data : {
                        branding_hash : brandingHash
                    },
                    type : 'GET',
                    success : function(data) {
                        elemColorScheme.val(data.color_scheme);
                        elemBackgroundColor.val(data.background_color);
                        elemTextColor.val(data.text_color);
                        elemMenuItemColor.val(data.menu_item_color);
                        elemStaticContent.val(data.static_content);
                        elemStaticContentMode.val(data.static_content_mode).change();

                        // reload logo with new tmp logo
                        $('img', elemLogoPreviewDiv).attr('src', newLogoBase64);

                        renderPreviewColors();
                        renderBranding();
                    },
                    error : mctracker.showAjaxError
                });
            } else {
                // set initial data on configuration
                $.each(configurableElems, function(i, elem) {
                    elem.val(elem.attr('orig_val'));
                });
                elemStaticContentMode.change();

                renderPreviewColors();
                renderBranding();
            }
        });

        renderPreviewColors();
        $.each(brandings, function(i, b) {
            if (b.created_by_editor) {
                elemBrandings.append($('<option value="' + b.id + '">' + b.description + ' [' + b.timestamp
                        + ']</option>'));
            }
        });
        $.each(configurableElems, function(i, elem) {
            elem.attr('orig_val', elem.val());
        });
    };

    var processMessage = function(data) {
        if (data.type == "rogerthat.branding.post_result") {
            if (data.error) {
                mctracker.hideProcessing();
                lj("#upload_error").empty().append($("<br>"));
                lj("#upload_error").append("There was an error while posting your branding!").append($("<br>"));
                if (data.error_code) {
                    lj("#upload_error").append("Error code: " + data.error_code).append($("<br>"));
                }
                if (data.reason) {
                    data.error += ' (' + data.reason + ')';
                }
                lj("#upload_error").append("Error description: " + data.error).fadeIn('slow');
                if (data.solution) {
                    lj("#upload_error").append($("<br>")).append($("<br>")).append(data.solution);
                }
            } else {
                lj("#upload_error").fadeOut('slow');
                loadBrandingList();
                mctracker.alert("Branding uploaded successfully!");
            }
            mctracker.broadcast({
                type : "rogerthat.service.branding.refresh"
            });
        }
    };

    return function() {
        mctracker.registerMsgCallback(processMessage);

        applyJQueryInUI();

        loadBrandingList();
    };
};

mctracker.registerLoadCallback("brandingContainer", brandingScript());
