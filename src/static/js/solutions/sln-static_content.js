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
    var staticContentData = {};
    var default_text_color = "#000000";
    var default_menu_item_color = "000000";
    var default_menu_item_background = "#ffffff";
    var designerPreviewFrameElem = $("#designer_preview_frame");
    var staticContentElem = $('#static_content');
    var staticContentModalElem = $('#staticContentModal');
    var ICONS;

    var updateBackgroundColor = function(color) {
        designerPreviewFrameElem.contents().find('body').css("background", color);
    };

    $("li[menu=static_content] a").click(function() {
        sln.call({
            url: "/common/settings/branding",
            type: "GET",
            success: function(data) {
                var brandingSettings = data;
                if(brandingSettings) {
                    default_text_color = "#" + brandingSettings.text_color;
                    default_menu_item_color = brandingSettings.menu_item_color || default_menu_item_color;
                    default_menu_item_background = "#" + brandingSettings.background_color;
                    renderStaticContent();
                }
            }
        });
    });

    var getPageString = function(x, y, z) {
        return CommonTranslations.page + ": " + (z + 1) + " | " + CommonTranslations.row + ": " + (y + 1) + " | "
            + CommonTranslations.column + ": " + (x + 1);
    };

    var initSaveStaticContentModal = function(staticContentId, html_content, label, icon_name, text_color, background_color, visible, position) {
        $(document).on('focusin', function(e) {
            if($(e.target).closest(".mce-window").length) {
                e.stopImmediatePropagation();
            }
            if($(e.target).closest(".select-icon-modal").length) {
                e.stopImmediatePropagation();
            }
        });
        var iconDivElem = $("#icon_div");

        tinymce.init({
            selector: "#static_content_container",
            convert_urls: false,
            relative_urls: false,
            remove_script_host: false,
            plugins: [
                "advlist autolink lists link image charmap print anchor searchreplace insertdatetime table paste code"
            ],
            toolbar: "insertfile undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image",
            setup: function(editor) {
                editor.on('keyup change', function(e) {
                    designerPreviewFrameElem.contents().find('body')
                        .html(tinyMCE.get('static_content_container').getContent())
                        .prepend('<style>img { max-width: 100%; height: auto; }</style>');
                });
                editor.on('init', function(args) {
                    tinyMCE.get('static_content_container').setContent(html_content);
                });
            },
            language: LANGUAGE.split('_')[0],
            file_browser_callback: function(field_name, url, type, win) {
                var CROP_OPTIONS = {
                    viewMode: 1,
                    dragMode: 'move',
                    rotatable: true,
                    autoCropArea: 0.95
                };
                if(type === "image") {
                    $('#image-input-element').unbind('change').click().change(function() {
                        var popupWindow = $('.mce-container.mce-panel.mce-floatpanel.mce-window.mce-in, .mce-reset.mce-fade.mce-in').hide();
                        var modal = $('#modal-edit-static-content-image')
                            .modal('show')
                            .on('shown', function () {
                                $(window).resize(); // else the cropper window is very small for some reason.
                            });
                        var imagePreview = modal.find('#static-content-image-upload');
                        sln.showProcessing();
                        readFile(this, imagePreview, function () {
                            imagePreview.cropper('destroy');
                            imagePreview.cropper(CROP_OPTIONS);
                            sln.hideProcessing();
                            modal.find('#save-static-content-image').unbind('click').click(function () {
                                if ($('#image-input-element')[0].files.length !== 0) {
                                    var croppedImageCanvas = imagePreview.cropper('getCroppedCanvas', {
                                        width: 720
                                    });
                                    var resizedImageDataUrl = croppedImageCanvas.toDataURL('image/jpeg', 0.8);
                                    $('#' + field_name).val(resizedImageDataUrl).attr('disabled', true);
                                }
                                modal.modal('hide');
                                popupWindow.show();
                                imagePreview.cropper('destroy');
                                //immediately close the first popup from tinymce
                                $('.mce-widget.mce-btn.mce-primary.mce-abs-layout-item.mce-first.mce-btn-has-text').click();
                            });
                        });
                        function readFile (input, targetElement, callback) {
                            if (input.files && input.files[0]) {
                                var reader = new FileReader();

                                reader.onload = function (e) {
                                    targetElement.attr('src', reader.result);
                                    callback();
                                };
                                reader.readAsDataURL(input.files[0]);
                            } else {
                                sln.showBrowserNotSupported();
                            }
                        }
                    });
                }
            }
        });

        if(tinyMCE.get('static_content_container') && tinyMCE.get('static_content_container').initialized) {
            tinyMCE.get('static_content_container').setContent(html_content);
        }

        sln.call({
            url: "/common/service_menu/get_free_spots",
            type: "GET",
            success: function(data) {
                var select = $('#free_spots').empty();
                if(position && visible) {
                    var x = position.x;
                    var y = position.y;
                    var z = position.z;
                    select.append($('<option selected></option>').attr('value', x + "," + y + "," + z).text(getPageString(x, y, z)));
                }
                $.each(data.spots, function(i, d) {
                    select.append($('<option></option>').attr('value', d.x + "," + d.y + "," + d.z).text(getPageString(d.x, d.y, d.z)));
                });
            }
        });

        $("#textIcon").val(label);
        iconDivElem.attr("name", icon_name).empty();

        if(icon_name) {
            if (icon_name.indexOf('fa-') === 0) {
                var iconElem = $('<i class="fa rounded_icon"></i>').addClass(icon_name).css({
                    color: default_menu_item_background,
                    'background-color': '#' + default_menu_item_color
                });
                iconDivElem.append(iconElem);
                iconDivElem.css('background-color', '#' + default_menu_item_color);
            } else {
                iconDivElem.append('<img src="/mobi/service/menu/icons/lib/' + icon_name + '?color=' + default_menu_item_color + '">');
                iconDivElem.css("background-color", default_menu_item_background);
            }
        }
        $("#textColor").val(text_color);
        $("#textColorPicker").val(text_color);
        designerPreviewFrameElem.contents().find('body').css("color", text_color);
        $("#backgroundColor").val(background_color);
        $("#backgroundColorPicker").val(background_color);
        $('#staticContentVisible').prop('checked', visible).change(function() {
            $('#free_spots').attr('disabled', !$(this).prop('checked'));
        });
        $('#free_spots').attr('disabled', !visible);
        //noinspection JSJQueryEfficiency
        sln.fixColorPicker($("#textColor"), $("#textColorPicker"), textColorChanged);
        //noinspection JSJQueryEfficiency
        sln.fixColorPicker($("#backgroundColor"), $("#backgroundColorPicker"), backgroundColorChanged);
        designerPreviewFrameElem.contents().find('body')
            .css("background-color", background_color)
            .css("max-width", "100%")
            .html(html_content)
            .prepend('<style>img { max-width: 100%; height: auto; }</style>');

        setTimeout(function() {
            staticContentModalElem.find(".modal-body").scrollTop(0);
        }, 300);
    };

    var initSaveStaticContentPdfModal = function(staticContentId, label, icon_name, visible, position) {
        sln.call({
            url: "/common/service_menu/get_free_spots",
            type: "GET",
            success: function(data) {
                var select = $('#free_spots_pdf').empty();
                if(position && visible) {
                    var x = position.x;
                    var y = position.y;
                    var z = position.z;
                    select.append($('<option selected></option>').attr('value', x + "," + y + "," + z).text(getPageString(x, y, z)));
                }
                $.each(data.spots, function(i, d) {
                    select.append($('<option></option>')
                        .attr('value', d.x + ',' + d.y + ',' + d.z)
                        .text(getPageString(d.x, d.y, d.z)));
                });

            }
        });
        $('#save_static_content_2_form').find('[name="static_content_id"]').val(staticContentId);
        $("#textIconPdf").val(label);
        $("#icon_div_pdf").attr("name", icon_name).empty();
        $('#staticContentVisiblePdf').prop('checked', visible).change(function() {
            $('#free_spots_pdf').toggleClass('disabled', !$(this).prop('checked'));
        });
        $('#free_spots_pdf').toggleClass('disabled', !visible);
        if(icon_name) {
            var iconDivElem = $('#icon_div_pdf');
            if (icon_name.indexOf('fa-') === 0) {
                var iconElem = $('<i class="fa"></i>').addClass(icon_name).css({
                    color: '#' + default_menu_item_color,
                    'background-color': default_menu_item_background,
                    'font-size': '56px',
                    padding: '5px'
                });
                iconDivElem.append(iconElem);
            } else {
                iconDivElem.append('<img src="/mobi/service/menu/icons/lib/' + icon_name + '?color=' + default_menu_item_color + '">');
                iconDivElem.css("background-color", default_menu_item_background);
            }
        }

        var pdfUploadElement = $('#pdf_upload');
        pdfUploadElement.replaceWith(pdfUploadElement.val('').clone(true));
    };

    var getStaticContent = function() {
        sln.call({
            url: "/common/static_content/load",
            type: "GET",
            success: function(data) {
                $.each(data, function(i, d) {
                    d.position_str = getPageString(d.position.x, d.position.y, d.position.z);
                });
                staticContentData = data;
                renderStaticContent();
            }
        });
    };

    var renderStaticContent = function() {
        var sc_table = $("#static_content").find("table tbody");
        var html = $.tmpl(templates['static_content/static_content'], {
            sc: staticContentData,
            menu_background_color: default_menu_item_background,
            menu_item_color: default_menu_item_color,
            t : CommonTranslations
        });

        sc_table.empty().append(html);
        $.each(staticContentData, function(i, d) {
            $("#static-content-" + d.id).data("sc", d);
        });

        staticContentElem.find('table tbody button[action="edit"]').click(function() {
            var staticContentId = $(this).attr("static_content_id");
            var sc = $("#static-content-" + staticContentId).closest("tr").data("sc");
            if(sc.sc_type == 1) {
                staticContentModalElem.modal("show");
                $("#save_static_content").attr("static_content_id", staticContentId);
                $("#staticContentModalLabel").text(CommonTranslations.STATIC_CONTENT_UPDATE);
                staticContentModalElem.find(".modal-body").css('height', staticContentModalElem.height() - 138 + "px");
                initSaveStaticContentModal(staticContentId, sc.html_content, sc.icon_label, sc.icon_name, sc.text_color,
                    sc.background_color, sc.visible, sc.position);
            } else {
                $("#staticContentPdfModal").modal("show");
                $("#save_static_content_2").attr("static_content_id", staticContentId);
                $("#staticContent2ModalLabel").text(CommonTranslations.STATIC_CONTENT_UPDATE);
                initSaveStaticContentPdfModal(staticContentId, sc.icon_label, sc.icon_name, sc.visible, sc.position);
            }
        });
        staticContentElem.find('table tbody button[action="delete"]').click(function() {
            var staticContentId = $(this).attr("static_content_id");
            sln.confirm(CommonTranslations.CONFIRM_DELETE_STATIC_CONTENT, function() {
                sln.call({
                    url: "/common/static_content/delete",
                    type: "POST",
                    data: {
                        data: JSON.stringify({
                            static_content_id: parseInt(staticContentId)
                        })
                    },
                    success: function(data) {
                        if(!data.success) {
                            return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                        }
                    }
                });
            });
        });
    };

    $("#create_static_content_choice_2").click(function() {
        $("#staticContentChoice").modal("hide");
        $("#save_static_content_2").attr("static_content_id", null);
        $("#staticContent2ModalLabel").text(CommonTranslations.STATIC_CONTENT_CREATE);
        initSaveStaticContentPdfModal(null, "", "", true);
    });

    $("#save_static_content_2").click(function(e) {
        e.preventDefault();
        var staticContentId = $(this).attr('static_content_id');
        var position = $("#free_spots_pdf").val();
        var label = $("#textIconPdf").val();
        var iconName = $("#icon_div_pdf").attr("name");

        var errorlist = [];
        if(!position) {
            errorlist.push("<li>" + CommonTranslations.POSITION_IS_REQUIRED + "</li>");
        }
        if(!label) {
            errorlist.push("<li>" + CommonTranslations.LABEL_IS_REQUIRED + "</li>");
        }
        if(!iconName) {
            errorlist.push("<li>" + CommonTranslations.ICON_IS_REQUIRED + "</li>");
        }
        var pdfUploadElement = document.getElementById('pdf_upload');
        if(!staticContentId && pdfUploadElement.files.length === 0) {
            errorlist.push("<li>" + CommonTranslations.PDF_IS_REQUIRED + "</li>");
        }

        if(errorlist.length > 0) {
            errorlist.splice(0, 0, "<ul>");
            errorlist.push("</ul>");
            sln.alert(errorlist.join(""), null, CommonTranslations.ERROR);
            return;
        }

        $('[name="icon_name"]').val(iconName);
        sln.showProcessing(CommonTranslations.SAVING_DOT_DOT_DOT);
        $("#save_static_content_2_form").submit();
    });

    $("#create_static_content_choice_1").click(function() {
        $("#staticContentChoice").modal("hide");
        $("#save_static_content").attr("static_content_id", null);
        $("#staticContentModalLabel").text(CommonTranslations.STATIC_CONTENT_CREATE);
        staticContentModalElem.find(".modal-body").css('height', staticContentModalElem.height() - 138 + "px");

        initSaveStaticContentModal(null, "", "", null, default_text_color, default_menu_item_background, true);
    });

    $("#save_static_content").click(function() {
        var staticContentId = parseInt($("#save_static_content").attr("static_content_id"));
        var position = $("#free_spots").val(); // z|x|y seperator: x
        var label = $("#textIcon").val();
        var iconName = $("#icon_div").attr("name");
        var textColor = $("#textColor").val();
        var backgroundColor = $("#backgroundColor").val();
        var htmlContent = tinyMCE.get('static_content_container').getContent();
        var visible = $('#staticContentVisible').prop('checked');

        var errorlist = [];
        if(!position) {
            errorlist.push("<li>" + CommonTranslations.POSITION_IS_REQUIRED + "</li>");
        }
        if(!label) {
            errorlist.push("<li>" + CommonTranslations.LABEL_IS_REQUIRED + "</li>");
        }
        if(!iconName) {
            errorlist.push("<li>" + CommonTranslations.ICON_IS_REQUIRED + "</li>");
        }
        if(!textColor) {
            errorlist.push("<li>" + CommonTranslations.TEXT_COLOR_IS_REQUIRED + "</li>");
        }
        if(!backgroundColor) {
            errorlist.push("<li>" + CommonTranslations.BACKGROUND_COLOR_IS_REQUIRED + "</li>");
        }
        if(!htmlContent) {
            errorlist.push("<li>" + CommonTranslations.CONTENT_IS_REQUIRED + "</li>");
        }

        if(errorlist.length > 0) {
            errorlist.splice(0, 0, "<ul>");
            errorlist.push("</ul>");
            sln.alert(errorlist.join(""), null, CommonTranslations.ERROR);
            return;
        }

        var positionList = position.split(',');

        sln.call({
            url: "/common/static_content/put",
            type: "POST",
            data: {
                data: JSON.stringify({
                    static_content: {
                        position: {
                            x: parseInt(positionList[0]), // Column
                            y: parseInt(positionList[1]), // Row
                            z: parseInt(positionList[2]) // Page
                        },
                        icon_label: label,
                        icon_name: iconName,
                        text_color: textColor,
                        background_color: backgroundColor,
                        html_content: htmlContent,
                        visible: visible,
                        id: staticContentId || null
                    }
                })
            },
            success: function(data) {
                if(!data.success) {
                    return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
                staticContentModalElem.modal('hide');
            }
        });
    });

    function getIconList (callback) {
        "use strict";
        if (ICONS) {
            callback(ICONS);
        } else {
            sln.call({
                url: "/mobi/rest/service/icon-library/list",
                type: "GET",
                success: function (data) {
                    ICONS = data;
                    callback(ICONS);
                }
            });
        }
    }

    $(".selectIcon").click(function () {
        "use strict";
        getIconList(function (icons) {
            var html = $.tmpl(templates['static_content/static_content_select_icon'], {
                header: CommonTranslations.SELECT_ICON,
                CommonTranslations: CommonTranslations,
                icons: icons
            });
            var modal = sln.createModal(html);

            $('div[data-name]', html).click(function () {
                var iconName = $(this).attr('data-name');
                var iconDivElem = $("#icon_div_pdf, #icon_div");
                if (iconName.indexOf('fa-') === 0) {
                    var iconElem = $('<i class="fa rounded_icon"></i>').addClass(iconName).css({
                        color: default_menu_item_background,
                        'background-color': '#' + default_menu_item_color
                    });
                    iconDivElem
                        .attr('name', iconName)
                        .css('background-color', '#' + default_menu_item_color)
                        .html(iconElem);
                } else {
                    iconDivElem
                        .attr('name', iconName)
                        .css("background-color", default_menu_item_background)
                        .html('<img src="/mobi/service/menu/icons/lib/' + iconName + '?color=' + default_menu_item_color + '">');
                }
                modal.modal('hide');
            });

            sln.configureDelayedInput($("#search_icon", html), function (txt) {
                var iconsContainer = $("#icons");
                txt = txt.replace(/[`~!@#$%^&*()_|+\-=?;:'",.<>\{\}\[\]\\\/]/gi, '');
                if (txt) {
                    iconsContainer.find('div[data-name]:not([data-name*="' + txt + '"])').addClass('hide');
                    iconsContainer.find('div[data-name*="' + txt + '"]').removeClass('hide');
                } else {
                    iconsContainer.find('div[data-name]').removeClass('hide');
                }
            }, null, null, 200);
        });
    });


    var textColorElem = $("#textColor");
    var backgroundColorElem = $("#backgroundColor");

    function textColorChanged() {
        var val = $("#textColor").val();
        var isOk = /(^#[0-9A-F]{6}$)|(^#[0-9A-F]{3}$)/i.test(val);
        if(isOk) {
            $("#textColorError").hide().parents('.control-group').removeClass('error');
            designerPreviewFrameElem.contents().find('body').css("color", val);
        } else {
            $("#textColorError").show().parents('.control-group').addClass('error');
        }
        $("#textColorPicker").val(val);
    }

    textColorElem.on('input', textColorChanged);

    $("#textColorPicker").on('input', function() {
        $("#textColor").val($(this).val());
        designerPreviewFrameElem.contents().find('body').css("color", $(this).val());
    });

    function backgroundColorChanged() {
        var val = $("#backgroundColor").val();
        var isOk = /(^#[0-9A-F]{6}$)|(^#[0-9A-F]{3}$)/i.test(val);
        if(isOk) {
            $("#backgroundColorError").addClass('hide').parents('.control-group').removeClass('error');
            updateBackgroundColor(val);
        } else {
            $("#backgroundColorError").removeClass('hide').parents('.control-group').addClass('error');
        }
        $("#backgroundColorPicker").val(val);
    }

    backgroundColorElem.on("keyup change", backgroundColorChanged);

    $("#backgroundColorPicker").change(function() {
        $("#backgroundColor").val($(this).val());
        updateBackgroundColor($(this).val());
    });

    var staticContentTabPress = function() {
        staticContentElem.find("li").removeClass("active");
        var li = $(this).parent().addClass("active");
        staticContentElem.find("section").hide();
        staticContentElem.find("section#" + li.attr("section")).show();
    };

    staticContentElem.find("li a").click(staticContentTabPress);

    var channelUpdates = function(data) {
        if(data.type == "rogerthat.system.channel_connected") {
            getStaticContent();
        } else if(data.type == "solutions.common.service_menu.updated") {
            getStaticContent();
        } else if(data.type == "solutions.common.static_content.pdf.post_result") {
            sln.hideProcessing();
            if(data.error) {
                sln.alert(data.error);
            } else {
                $("#staticContentPdfModal").modal("hide");
                getStaticContent();
            }
        }
    };

    sln.registerMsgCallback(channelUpdates);
});
