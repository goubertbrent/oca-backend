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
    'use strict';

    $.getJSON('/unauthenticated/osa/apps/flanders').done(function (apps) {
        $.getJSON('/static/js/shop/libraries/flanders.json').done(function (maps) {
            createMap(apps, maps);
        });
    });

    function createMap(apps, data) {
        function tooltip(city) {
            if (apps[city]) {
                return '<b>' + city + '</b>';
            } else {
                return city;
            }
        }

        function areaClicked(city) {
            window.open('/install/' + apps[city], '_blank');
        }

        var enabledCities = Object.keys(apps);
        var flandersMap = new VectorMap('cities', data.cities, enabledCities, $('#flanders'), {
            tooltip: tooltip,
            areaClicked: areaClicked,
            width: data.width,
            height: data.height
        });

        flandersMap.colors.default = '#f4f4e8';
        flandersMap.colors.unselected = flandersMap.colors.selected;
        flandersMap.render();
    }

});
