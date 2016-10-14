/*
 * Copyright 2016 Mobicage NV
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
 * @@license_version:1.1@@
 */

var userClickedBeforeNewsLoaded = false;
$(function() {

    var videoid = null;
    var player = null;
    $("ul.nav li a").click(function() {
        if ($(this).hasClass("help_menu_item")) {
            var menu_id = $(this).closest("li").attr("menu");
            videoid = $("#" + menu_id + " ul li.active a").attr("help");
        } else {
            videoid = $(this).attr("help");
        }
        if (videoid)
            $("#help").prop("disabled", false);
        else
            $("#help").prop("disabled", true);
    });
    $("#help").click(function() {
        $("#help-video").modal('show');
    });
    $("#help-video").on('shown', function() {
        player = new YT.Player('ytplayer', {
            height : '390',
            width : '640',
            videoId : videoid,
            autoplay : 1,
            modestbranding : 1,
            rel : 0,
            showinfo : 0
        });
        player.addEventListener("onReady", function(event) {
            event.target.playVideo();
        });
    });
    $("#help-video").on('hidden', function() {
        player.destroy();
    });
    var menuPress = function(event) {
        var li = $(this).parent();
        if (li.hasClass('disabled'))
            return;
        var menu = li.attr("menu");
        userClickedBeforeNewsLoaded = true;
        $("#topmenu li").removeClass("active");
        $("div.page, #newspage").hide();
        li.addClass("active");
        $("div#" + menu).show();
        if (event.target.id === "shoplink") {
            $('#shoplink').addClass('active');
        } else if (!event.target.id) {
            $('#shoplink').removeClass('active');
        }
    };

    $("#topmenu li a, #shoplink").click(menuPress);
    $("#topmenu").find("li:first-child a").click();
    userClickedBeforeNewsLoaded = false;

    // Disable certain links in docs
    $('section [href^=#]').click(function(e) {
        e.preventDefault();
    });

});

// Load the IFrame Player API code asynchronously.
var tag = document.createElement('script');
tag.src = "https://www.youtube.com/player_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

// Replace the 'ytplayer' element with an <iframe> and
// YouTube player after the API code downloads.
var player;
var yt_player_ready = false;
function onYouTubePlayerAPIReady() {
    yt_player_ready = true;
    // player = new YT.Player('ytplayer', {
    // height: '390',
    // width: '640',
    // videoId: 'M7lc1UVf-VE'
    // });
}
