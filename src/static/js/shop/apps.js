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
    $('#app-container').find('input[type=checkbox]').change(function () {
        var checkbox = $(this);
        var appId = checkbox.closest('tr').data('appId');
        var signupCheckbox = $(`#checkbox_signup_${appId}`);
        var paidFeaturesCheckbox = $(`#checkbox_paid_features_${appId}`);
        var jobsCheckbox = $(`#checkbox_jobs_${appId}`);
        var signupEnabled = signupCheckbox.prop('checked');
        var isPaying = paidFeaturesCheckbox.prop('checked');
        var jobsEnabled = jobsCheckbox.prop('checked');
        sln.call({
            showProcessing : true,
            url: `/internal/shop/rest/shop-apps/${appId}`,
            method: 'PUT',
            data : {
                signup_enabled: signupEnabled,
                paid_features_enabled: isPaying,
                jobs_enabled: jobsEnabled
            },
            success : function(data) {
                signupCheckbox.prop('enabled', data.signup_enabled);
                paidFeaturesCheckbox.prop('enabled', data.paid_features_enabled);
                jobsCheckbox.prop('enabled', data.jobs_enabled);
            }
        });
    });
});
