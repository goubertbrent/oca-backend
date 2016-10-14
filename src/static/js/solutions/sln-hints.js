/*
 * Copyright 2016 Mobicage NV
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
 * @@license_version:1.1@@
 */

$(function() {
    var loadHints = function() {
        sln.call({
            url : "/common/hints/load_next",
            type : "GET",
            success : function(data) {
                if (data != null) {
                    showHints(data);
                }
            },
            error : sln.showAjaxError
        });
    };

    var showHints = function(hint) {
        var html = $.tmpl(templates.hints_modal, {
            header : CommonTranslations.HINT,
            cancelBtn : CommonTranslations.CLOSE,
            submitBtn : CommonTranslations.OKAY_I_GOT_IT,
            CommonTranslations : CommonTranslations,
            hint : hint
        });
        var modal = sln.createModal(html);
        
        $('button[action="submit"]', html).click(function() {
            sln.call({
                url : "/common/hints/mark_read",
                type : "POST",
                data: {
                    data: JSON.stringify({
                            hint_id: hint.id
                    })
                },
                success : function(data) {
                    if (!data.success) {
                        sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                        return;
                    }
                },
                error : sln.showAjaxError
            });
        });
    };
    
    loadHints();
});
