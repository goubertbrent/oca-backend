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
    'use strict';
    init();

    function init() {
        render();
    }

    function render() {
        getApps(function (apps) {
            var brandings = [{
                kind: 'DefaultBirthdayMessageBranding',
                name: 'Birthday message branding'
            }];
            var html = $.tmpl($('#edit-template').html(), {
                apps: apps,
                defaultBrandings: brandings
            });
            $('#container').html(html);
            $('#set_default_branding').click(defaultBrandingClicked);
            $('.save_branding').click(saveBranding);
            $('.delete_branding_for_app').click(deleteBrandingClicked);
        });
    }

    function deleteBrandingClicked() {
        var kind = $(this).attr('branding_kind');
        var appId = $(`#selected_app_${kind}`).val();
        deleteBrandingForApp(kind, appId);
    }

    function deleteBrandingForApp(kind, appId) {
        $.ajax({
            url: `/mobiadmin/apps/branding/delete?kind=${kind}&app_id=${appId}`,
            success: function (response) {
                alert(response);
            }
        });
    }

    function defaultBrandingClicked() {
        var checked = $(this).prop('checked');
        $('#apps_container').toggle(!checked).find('input[type=checkbox]').prop('disabled', checked);
    }

    function getApps(callback) {
        $.ajax({
            url: '/mobiadmin/apps/list',
            method: 'get',
            success: function (apps) {
                callback(apps);
            }
        });
    }

    function saveBranding() {
        var kind = $(this).attr('branding_kind');
        var appIds = [];
        $('#apps_container').find('input:checked').each(function () {
            appIds.push($(this).val());
        });
        var isDefault = $('#set_default_branding').prop('checked');

        var file = $('#form_' + kind).find('input[name=branding]').get(0).files[0];
        if (!file) {
            alert('please select a file');
            return;
        }
        var reader = new FileReader();
        reader.addEventListener('load', function () {
            $.ajax({
                url: '/mobiadmin/apps/branding/put',
                type: 'post',
                data: {
                    data: JSON.stringify({
                        kind: kind,
                        zip_file_content: reader.result.split(',')[1],
                        default: isDefault,
                        app_ids: appIds
                    })
                },
                success: function (data) {
                    alert(data);
                },
                error: function () {
                    alert('Something went wrong, try again later');
                }
            }, false);
        });
        reader.readAsDataURL(file);
    }

})();
