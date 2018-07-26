/*
 * Copyright 2018 Mobicage NV
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
 * @@license_version:1.3@@
 */

$(function() {
    $('#app-container').find('button').click(function() {
        var btn = $(this);
        if (btn.is(':disabled')) {
            console.log('Btn is disabled');
            return;
        }

        var appId = btn.attr('data-app');
        var enabled = btn.attr('data-enabled').toLowerCase() != 'true';

        var enableBtn = btn.parent().find('button[data-action="enable"]');
        var disableBtn = btn.parent().find('button[data-action="disable"]');
        enableBtn.prop('disabled', true);
        disableBtn.prop('disabled', true);

        sln.call({
            showProcessing : true,
            url : '/internal/shop/rest/apps/signup_enabled',
            method : 'POST',
            data : {
                data : JSON.stringify({
                    app_id : appId,
                    enabled : enabled
                })
            },
            success : function(data) {
                enableBtn.prop('disabled', false);
                disableBtn.prop('disabled', false);

                if (!data.success) {
                    return sln.alert(data.errormsg);
                }

                enableBtn.toggleClass('btn-success', enabled);
                enableBtn.attr('data-enabled', "" + enabled);
                enableBtn.html(enabled ? 'Enabled' : '&nbsp;');

                disableBtn.attr('data-enabled', "" + enabled);
                disableBtn.html(enabled ? '&nbsp;' : 'Disabled');
            },
            error : function() {
                enableBtn.prop('disabled', false);
                disableBtn.prop('disabled', false);
                sln.showAjaxError();
            }
        });
    });
});
