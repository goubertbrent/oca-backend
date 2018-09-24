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

$(document).ready(function(){
    var importingId;
    var total, success, failed;

    $('form').submit(function(event){
        event.preventDefault();

        var fileInput = $('#customers_sheet')[0];
        sln.readFileData(fileInput, importCustomers);
    });

    function updateProgressInfo() {
        var finished = success + failed;
        var allDone = finished === total && (total > 0);
        $('.loading-spinner').toggle(!allDone);
        var progress = `
            <br>Importing <b>${finished} / ${ total }<b>...`;

        if (failed) {
            progress += ` (<span style="color: red;">${failed} Failed</span>)`;
        }
        if (allDone) {
            $('#app').val('');
            $('#customers_sheet').val('');
            $('#import_customers').attr('disabled', false);
        } else {
            progress = '<p>Please wait, it might take awhile...</p>' + progress;
        }
        $('.progress-info').html(progress);
    }

    function importCustomers(fileData) {
        total = success = failed = 0;
        importingId = Math.floor(Math.random() * 100000);
        $('#import_customers').attr('disabled', true);

        sln.call({
            url: '/internal/shop/customers/import/sheet',
            type: 'post',
            data: {
                import_id: importingId,
                app_id: $('#app').val(),
                file_data: fileData,
            },
            success: function(result) {
                $('.info').show();

                if (!result.success) {
                    $('.progress-info').html(
                        `<br/><span style="color: red;">${result.errormsg}</span>`
                    );
                    $('#import_customers').attr('disabled', false);
                    return;
                }

                $('.loading-spinner').html(TMPL_LOADING_SPINNER);
                total = result.customer_count;
                updateProgressInfo();
            },
            error: sln.showAjaxError
        });
    }


    sln.registerMsgCallback(channelUpdates);
    function channelUpdates(data) {
        if (!data.import_id || (data.import_id !== importingId)) {
            return;
        }
        switch(data.type) {
            case 'shop.customer.import.success':
                success++;
                updateProgressInfo();
                break;
            case 'shop.customer.import.failed':
                failed++;
                updateProgressInfo();
                break;
        }
    }

});
