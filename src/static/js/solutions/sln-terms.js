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

(function () {
    var acceptCheckbox = $('#accept-checkbox');
    var checkboxContainer = $('#checkbox-container');
    $('#terms-form').on('submit', function (e) {
        if (!acceptCheckbox.prop('checked')) {
            e.preventDefault();
            showError();
        }
    });

    function showError() {
        checkboxContainer.addClass('has-error');
        checkboxContainer.find('.help-block').show();
    }
})();
