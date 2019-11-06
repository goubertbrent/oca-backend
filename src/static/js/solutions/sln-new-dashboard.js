/*
 * Copyright 2019 Green Valley Belgium NV
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
 * @@license_version:1.5@@
 */

(function () {
    ROUTES.forms = router;
    ROUTES.participation = router;
    ROUTES.news = router;
    ROUTES.reports = router;
    var element = document.getElementById('dashboard');
    var baseUrl = DEBUG ? 'http://localhost:4300/' : '/static/client/index.html#/';
    var topMenu = $('#topmenu');
    window.addEventListener('message', function (e) {
        if (e.data && e.data.type === 'oca.set_navigation') {
            window.history.pushState(null, null, '#' + e.data.path);
            setNavigation(e.data.path);
        }
    });

    function router(paths) {
        // Only load the iframe once user visits this page to speed up initial page load
        var origin =  DEBUG ? 'http://localhost:4300' : window.location.origin;
        if (element.src) {
            element.contentWindow.postMessage({
                'type': 'oca.load_page',
                'paths': paths
            }, origin);
        } else {
            element.src = baseUrl + paths[0];
            element.onload = function () {
                element.contentWindow.postMessage({
                    'type': 'oca.set_language',
                    'language': LANGUAGE
                }, origin);
            };
        }
        element.style.display = 'block';
    }

    function setNavigation(menu) {
        topMenu.find('li[menu]').removeClass('active');
        topMenu.find('li[menu=' + menu + ']').addClass('active');
    }
})();
