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

var allApps = [];
$(document).ready(function () {
    var typeAheadOptions = {
        source: function (query, resultHandler) {
            var appMap = {};
            var appslist = [];
            $.each(allApps, function (i, o) {
                var item = [o.name, o.id].join(', ');
                appMap[item] = o;
                appslist.push(item);
                o.matchString = item;
            });
            resultHandler(appslist);
        },
        items: 20,
        updater: function (item) {
            var result = allApps.filter(function (a) {
                return a.matchString === item;
            });
            render(result[0]);
            return item;
        }
    };
    getApps(function (data) {
        allApps = data;
        $('#app-search').typeahead(typeAheadOptions).val(allApps[0].name).focus().select();
        render(allApps[0]);
    });

});

function getApps(callback) {
    sln.call({
        url: '/internal/shop/rest/apps/all',
        success: function (data) {
            callback(data);
        }
    });
}

function setApps(app) {
    var appId = app.id;
    var statusText = $('#saving-status');
    render(app[0], 'saving');
    sln.call({
        url: '/internal/shop/rest/apps/set',
        method: 'POST',
        data: {
            data: JSON.stringify({
                app: app
            })
        },
        success:function (data) {
            var app;
            if (data.success) {
                app = allApps.filter(function (a) {
                    return a.id === appId;
                });
                render(app[0], 'saved');
            }
        }
    });
}

function render(app, status) {
    if(!status) {
        var html = $.tmpl(JS_TEMPLATES.apps, {
            allApps: allApps,
            selectedApp: app
        });

        $('#app-circles-container').html(html).find('button').not('#save-apps').click(function () {
            var $this = $(this);
            var action = $this.attr('data-action');
            var appId = $this.attr('data-app-id');
            if (action === "1") {
                app.orderable_app_ids.push(appId);
            } else {
                app.orderable_app_ids.splice(app.orderable_app_ids.indexOf(appId), 1);
            }
            render(app);
        });
    }
    var saveBtn = $('#save-apps');
    switch (status){
        case "saved":
            saveBtn.html('Saved!');
            setTimeout(function(){
                saveBtn.html('<i class="fa fa-save"></i> Save').attr('disabled', false);
            }, 3000);
            break;
        case "saving":
            saveBtn.html('<i class="fa fa-spinner spin"></i> Saving...').attr('disabled', true);
            break;
        default:
            saveBtn.html('<i class="fa fa-save"></i> Save');
    }
    if(!status){
        saveBtn.unbind('click').click(function () {
            setApps(app);
        });
    }
}
