(function () {
    'use strict';
    init();

    function init() {
        mctracker.runChannel(CHANNEL_TOKEN);
        mctracker.registerMsgCallback(channelListeners);
        render();
    }

    function render() {
        getApps(function (apps) {
            var assets = [{
                id: 'ChatBackgroundImage',
                name: 'Chat background image',
            }];
            var html = $.tmpl($('#edit-template').html(), {
                apps: apps,
                assets: assets
            });
            $('#container').html(html);
            $('#set_default_asset').click(defaultAssetClicked);
            $('.save_asset').click(saveAsset);
            $('.delete_asset_for_app').click(deleteAssetClicked);
        });
    }

    function deleteAssetClicked() {
        var kind = $(this).attr('asset_id');
        var appId = $(`#selected_app_${kind}`).val();
        deleteAssetForApp(kind, appId);
    }

    function deleteAssetForApp(kind, appId) {
        $.ajax({
            url: `/mobiadmin/apps/asset/delete?kind=${kind}&app_id=${appId}`,
            success: function (response) {
                alert(response);
            }
        });
    }

    function defaultAssetClicked() {
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

    function saveAsset() {
        var assetId = $(this).attr('asset_id');
        getUploadUrl(function (uploadUrl) {
            uploadAsset(uploadUrl, assetId);
        });
    }

    function getUploadUrl(callback) {
        $.ajax({
            url: '/mobiadmin/apps/assets/upload_url',
            success: callback
        });
    }

    function uploadAsset(uploadUrl, assetId) {
        var appIds = [];
        $('#apps_container').find('input:checked').each(function () {
            appIds.push($(this).val());
        });
        var form = $('#form_' + assetId).attr('action', uploadUrl);
        form.find('input[name=default]').val($('#set_default_asset').prop('checked'));
        form.find('input[name=app_ids]').val(appIds);
        form.submit();
    }

    function channelListeners(data) {
        if (data.type === 'rogerthat.apps.assets.upload_failed') {
            alert(data.message);
        } else if (data.type === 'rogerthat.apps.assets.upload_success') {
            alert('Successfully uploaded asset.');
            window.location.reload();
        }
    }
})();