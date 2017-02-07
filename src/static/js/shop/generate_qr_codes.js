/*
 * Copyright 2017 Mobicage NV
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

$(document).ready(function () {
    "use strict";
    var typeAheadOptions = {
            source: function (query, resultHandler) {
                var appslist = [];
                $.each(allApps, function (i, o) {
                    appslist.push([o.name, o.id].join(', '));
                });
                resultHandler(appslist);
            },
            items: 20
        },
        allApps;

    getApps(function (data) {
        allApps = data;
        allApps.map(function (app) {
            app.matchString = [app.name, app.id].join(', ');
        });
        $('#app-search').typeahead(typeAheadOptions).focus().select();
    });

    $('#qr-code-amount').on('input', validateQRCodeAmount);
    $('#start-generating').click(startGenerating);

    function startGenerating () {
        var appName = $('#app-search').val();
        var app = getApp(appName);
        var amount = $('#qr-code-amount').val();
        var mode = $('#qr-code-mode').val();
        if (!appName) {
            sln.alert('Please enter an app');
            return;
        }
        if (!app) {
            sln.alert('App with name ' + appName + ' does not exist');
            return;
        }
        if (!validateQRCodeAmount()) {
            return;
        }
        doGenerateQRCodes(app.id, amount, mode, function (data) {
            if (data.errormsg) {
                sln.alert(data.errormsg);
            } else {
                sln.alert('You will receive an email soon containing the requested QR codes.');
            }
        });
    }

    function getApps (callback) {
        sln.call({
            url: '/internal/shop/rest/apps/all',
            success: callback
        });
    }

    function getApp (appName) {
        var name = appName.toLowerCase().trim();
        return allApps.filter(function (a) {
            return a.name.toLowerCase() === name || name === a.matchString.toLowerCase();
        })[0];
    }


    function validateQRCodeAmount () {
        var field = $('#qr-code-amount');
        var mode = $('#qr-code-mode').val();
        var controlGroup = $('#qr-code-amount-group');
        var errorMessage = 'Should be higher or equal to 500';

        if (mode !== 'excel') {
            return true;
        }

        function validate () {
            return parseInt(field.val()) >= 500;
        }

        return sln.validate(controlGroup, field, errorMessage, validate);
    }

    function doGenerateQRCodes(appId, amount, mode, successHandler) {
        sln.call({
            url: '/internal/shop/rest/customers/generate_qr_codes',
            data: {
                app_id: appId,
                amount: amount,
                mode: mode
            },
            success: successHandler
        });
    }

});
