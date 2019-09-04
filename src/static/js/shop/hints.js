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

$(document).ready(function(){
    var hints = {};
    var channelUpdates = function(data) {
        console.log(data);
        if (data.type == "shop.hints.updated") {
            loadHints();
        }
    };
    
    var loadHints = function() {
        sln.call({
            url : '/internal/shop/rest/hints/load',
            success : function(data) {
                sln.hideProcessing();
                $.each(data, function(i, hint) {
                    hints[hint.id] = hint;
                });
                var html = $.tmpl(JS_TEMPLATES.hints, {
                    hints : data
                });
                $('#hints tbody').html(html);
                
                $('#hints tbody button[action="update"]').click(function() {
                    var hintId = parseInt($(this).attr("hint_id"));
                    updateHint(hintId);
                });
                
                $('#hints tbody button[action="delete"]').click(function() {
                    var hintId = parseInt($(this).attr("hint_id"));
                    sln.showProcessing("Deleting...");
                    sln.call({
                        url: '/internal/shop/rest/hints/delete',
                        type: 'POST',
                        data: {
                            data: JSON.stringify({
                                    hint_id: hintId
                            })
                        },
                        success: function () {
                            loadHints();
                        },
                        error: function () {
                            sln.hideProcessing();
                            alert("An error occured, please check this with your administrator.");
                        }
                    });
                });
            },
            error : function() {
                sln.hideProcessing();
                alert("An unknown error occurred, please report this to the administrators.");
            }
        });
    
    };
    
    var updateHint = function(hintId) {
        var html = $('#modal_add_hint').modal('show');
        html.attr('mode', 'new');
        
        if (hintId == null) {
            $("#myModalLabel").text("Add hint");
            $("#hint_tag").val("");
            $("#hint_language").val("nl");
            $("#hint_text").val("");
            $("#select_modules input:checked").each(function () {
                $(this).attr('checked', false);
            });
        } else {
            $("#myModalLabel").text("Update hint");
            var hint = hints[hintId];
            $("#hint_tag").val(hint.tag);
            $("#hint_language").val(hint.language);
            $("#hint_text").val(hint.text);
            $("#select_modules input").each(function () {
                if (hint.modules.indexOf($(this).val()) >= 0) {
                    $(this).attr('checked', true);
                } else {
                    $(this).attr('checked', false);
                }
            });
        }
        $('button[action="submit"]', html).unbind();
        $('button[action="submit"]', html).click(function() {
            sln.showProcessing("Loading...");
            
            var modules = [];
            $("#select_modules input:checked").each(function () {
                modules.push($(this).val());
            });
            
            sln.call({
                url: '/internal/shop/rest/hints/put',
                type: 'POST',
                data: {
                    data: JSON.stringify({
                            hint_id: hintId,
                            tag : $('#hint_tag').val(),
                            language : $('#hint_language').val(),
                            text : $("#hint_text").val(),
                            modules: modules
                    })
                },
                success: function () {
                    $('#modal_add_hint').modal('hide');
                    loadHints();
                },
                error: function () {
                    sln.hideProcessing();
                    $('#modal_add_hint').modal('hide');
                    alert("An error occured, please check this with your administrator.");
                }
            });
        });
    };
    
    $('.add-hint').click(function() {
        updateHint(null);
    });
    
    sln.registerMsgCallback(channelUpdates);
    loadHints();
});
