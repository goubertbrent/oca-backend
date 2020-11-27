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

$(function () {
    checkForIE();

    var menuPress = function (event) {
        var li = $(this).parent();
        if (li.hasClass('disabled') || li.hasClass('active'))
            return;
        var menu = li.attr("menu");
        $("#topmenu li").removeClass("active");
        $("#content-container>.page").hide();
        li.addClass("active");
        $("#" + menu).show();
        if (event.target.id === "shoplink") {
            $('#shoplink').parent().addClass('active');
        } else if (!event.target.id) {
            $('#shoplink').parent().removeClass('active');
        }
    };

    $("#topmenu li a, #shoplink").click(menuPress);
    $("#topmenu").find("li:first-child a").click();

    // Disable certain links in docs
    $('section [href^=#]').click(function (e) {
        e.preventDefault();
    });

    // prevent triggering the logout more than once
    $('#logout_link').click(function (e) {
        $(this).addClass('disabled');
    });

    // Check version and show popup in case of IE
    function checkForIE() {
        /* MSIE used to detect old browsers and Trident used to newer ones*/
        var isIE = navigator.userAgent.indexOf('MSIE ') > -1
            || navigator.userAgent.indexOf('Trident/') > -1;
        if (isIE) {
            var msg = CommonTranslations.please_use_proper_browser
                .replace('%(url)s', '<a href="https://browsehappy.com/" target="_blank">'
                    + CommonTranslations.overview_browsers + '</a>');
            sln.alert(msg);
        }
    }
});
