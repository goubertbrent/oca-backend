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

var isNestedPage = false;
var settingsTabs = $('#settings-tabs');
var dashboardContainer = document.getElementById('dashboard-container');

function newDashboardRouter(paths) {
    // Only load the iframe once user visits this page to speed up initial page load
    var baseUrl = DEBUG ? 'http://localhost:4300/' : '/static/client/index.html#/';
    var origin = DEBUG ? 'http://localhost:4300' : window.location.origin;
    var element = document.getElementById('dashboard');
    isNestedPage = paths[0] === 'settings';
    element.style.display = 'block';
    if (element.src) {
        element.contentWindow.postMessage({
            'type': 'oca.load_page',
            'paths': paths
        }, origin);
    } else {
        element.src = baseUrl + paths.join('/');
        element.addEventListener('load', function () {
            sln.registerMsgCallback(function (data) {
                element.contentWindow.postMessage({'type': 'channel', 'data': data}, origin);
            });
            element.contentWindow.postMessage({
                'type': 'oca.set_language',
                'language': LANGUAGE
            }, origin);
            resizeDashboard();
        }, {passive: true});
    }
    dashboardContainer.style.display = 'block';
    resizeDashboard();
    setTimeout(resizeDashboard, 200);
}

function resizeDashboard() {
    var style = dashboardContainer.style;
    if (isNestedPage) {
        // css to show the new dashboard under the tabs from the 'settings' page
        style.position = 'absolute';
        var offset = settingsTabs.offset();
        var topPosition = offset.top + settingsTabs.height() + 8;
        style.top = topPosition + 'px';
        style.height = window.innerHeight - topPosition + 'px';
        style.width = '940px';
    } else {
        // Full width/height of the dashboard
        style.position = null;
        style.height = '100%';
        style.width = '100%';
    }
}

function debounce(func, wait, immediate) {
    var timeout;
    return function () {
        var context = this, args = arguments;
        var later = function () {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        var callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

(function () {
    ROUTES.forms = newDashboardRouter;
    ROUTES.participation = newDashboardRouter;
    ROUTES.news = newDashboardRouter;
    ROUTES.reports = newDashboardRouter;
    var topMenu = $('#topmenu');
    window.addEventListener('message', function (e) {
        if (e.data && e.data.type === 'oca.set_navigation') {
            window.history.pushState(null, null, '#' + e.data.path);
            setNavigation(e.data.path);
        }
    });
    var delayedResize = debounce(resizeDashboard, 150);
    window.addEventListener('resize', delayedResize, {passive: true});
    window.addEventListener('load', delayedResize, {passive: true});

    function setNavigation(menu) {
        topMenu.find('li[menu]').removeClass('active');
        topMenu.find('li[menu=' + menu + ']').addClass('active');
    }
})();
