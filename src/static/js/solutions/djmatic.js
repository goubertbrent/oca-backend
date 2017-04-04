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
 * @@license_version:1.3@@
 */

var DJMATIC_PROFILE_STATUS_LIMITED = 4;
var jukeboxEnabled = true;
// Connect event handlers after load
$(function() {
    $("#topmenu li a").click(menuPress);
    $('#jukebox_cfg #jukeboxOn').click(jukeboxOn);
    $('#jukebox_cfg #jukeboxOff').click(jukeboxOff);
    $('#jukebox_cfg #timepickerEnabledFrom').timepicker({
        defaultTime : "20:00",
        showMeridian : false
    });
    $('#jukebox_cfg #timepickerEnabledUntil').timepicker({
        defaultTime : "04:00",
        showMeridian : false
    });
    $('#jukebox_days label input').click(dateChanged);
    $('#jukebox_cfg #timepickerEnabledFrom').on('changeTime.timepicker', startTimeChanged);
    $('#jukebox_cfg #timepickerEnabledUntil').on('changeTime.timepicker', stopTimeChanged);
    
    loadPlayerSettings();
});

var menuPress = function() {
    if (DJMATIC_PROFILE_STATUS == DJMATIC_PROFILE_STATUS_LIMITED) {
        var clickedMenu = $(this).parent().attr("menu") ;
        if (clickedMenu === "inbox" || clickedMenu ===  "menu" || clickedMenu ===  "events" || clickedMenu ===  "broadcast" || clickedMenu ===  "statistics") {
            sln.alert(CommonTranslations.FEATURE_NOT_ENABLED_ACCOUNT + "<br>" +
                    CommonTranslations.CONTACT_YOUR_X_FOR_MORE_INFO.replace("%(x)s", "DJ-Matic"), undefined, CommonTranslations.FEATURE_DISABLED);
            return;
        }
    }

    $("#topmenu li").removeClass("active");
    var li = $(this).parent().addClass("active");
    $("div.page").hide();
    $("div#" + li.attr("menu")).show();
};

var mainGenreChanged = function() {
    var genre = $(this).attr("genre");
    var enabled = $(this).is(":checked");
    var tbody = $('#jukebox_genres table[main_genre="' + genre + '"] tbody');
    if (enabled) {
        tbody.show(250);
        if ($(this).attr("genre_size") < 2) {
            var json = JSON.stringify({
                genre_id : $(this).attr("first_sub_genre"),
                genre_status : 'insert'
            });
            savePlayerSettings(json);
        } else {
            var json = JSON.stringify({
                genre_id : $(this).attr("genre_id"),
                genre_status : 'insert_main_genre'
            });
            savePlayerSettings(json);
            $('input', tbody).attr('checked', true);
        }
    } else {
        tbody.hide(250);
        var json = JSON.stringify({
            genre_id : $(this).attr("genre_id"),
            genre_status : 'delete_main'
        });
        savePlayerSettings(json);
        $('input', tbody).attr('checked', false);
    }
};

var genreChanged = function() {
    var enabled = $(this).is(":checked");
    var genreId = $(this).attr("genre_id");
    var json = JSON.stringify({
        genre_id : genreId,
        genre_status : enabled ? 'insert' : 'delete'
    });
    savePlayerSettings(json);
};

// LOAD //
var loadPlayerSettings = function() {
    $.ajax({
        url : DJMATIC_JUKEBOX_SERVER_API,
        type : "POST",
        data : {
            method : "player.loadSettings",
            player_id : DJMATIC_PLAYER_ID,
            secret : DJMATIC_SECRET
        },
        success : function(data, textStatus, XMLHttpRequest) {
            var jdata = JSON.parse(data);
            if (jdata.error != null) {
                sln.logError("Error occurred while getting settings\n" + jdata.error);
                sln.showAjaxError(data, textStatus, XMLHttpRequest);
            } else {
                updatePlayerLayout(jdata.result);
            }
        },
        error : sln.showAjaxError
    });
};

var updatePlayerLayout = function(settings) {
    // Status
    if (settings.status_player == "1") {
        $('#jukebox_cfg #jukeboxOn').addClass("btn-success").text(DJMaticTranslations.JUKEBOX_ENABLED);
        $('#jukebox_cfg #jukeboxOff').removeClass("btn-danger").html('&nbsp;');
        jukeboxEnabled = true;
    } else {
        $('#jukebox_cfg #jukeboxOn').removeClass("btn-success").html('&nbsp;');
        $('#jukebox_cfg #jukeboxOff').addClass("btn-danger").text(DJMaticTranslations.JUKEBOX_DISABLED);
        jukeboxEnabled = false;
    }
    // Days
    $('#jukebox_days label input').each(function(index) {
        var value = $(this).val();
        $(this)[0].checked = (settings.status_days & value) == value;
    });

    // Starttime
    $('#jukebox_cfg #timepickerEnabledFrom').timepicker('setTime', sln.intToTime(settings.time_from));

    // Endtime
    $('#jukebox_cfg #timepickerEnabledUntil').timepicker('setTime', sln.intToTime(settings.time_until));

    // Genres djmatic
    if (settings.type == "djmatic"){
        $("#djmatic_genres").html('<iframe src="https://download.dj-matic.com/apis/rt/config.php?p=' +  DJMATIC_PLAYER_ID + '"></iframe>');
    }
    else {
        $("li[menu=jukebox_cfg]").css("display", 'none');
        $("#jukebox_cfg").css("display", 'none');
        $("li[menu=inbox]").addClass("active")
        $("#inbox").css("display", 'block');
        
        $("#max_songs_in_request_container").css("display", 'block');
        $('#max_songs_in_request_list').val(settings.max_songs_in_queue),
        sln.configureDelayedInput($('#max_songs_in_request_list'), maxSongsInQueueChanged, null, false);
    }
    
    if (DJMATIC_PROFILE_STATUS == DJMATIC_PROFILE_STATUS_LIMITED) {
        if (settings.type != "djmatic") {
            $("li[menu=inbox]").removeClass("active")
            $("#inbox").css("display", 'none');
            $("li[menu=settings]").addClass("active")
            $("#settings").css("display", 'block');
        }
    }

    // Genres
    var genreHtmlElement = $("#jukebox_genres");
    genreHtmlElement.empty();
    var html = $.tmpl(genres_template, {
        genres : settings.genres
    });
    genreHtmlElement.append(html);
    $('#jukebox_genres table thead input[type="checkbox"]').change(mainGenreChanged);
    $('#jukebox_genres tbody input[type="checkbox"]').change(genreChanged);
};

// SAVE //
var savePlayerSettings = function(json) {
    console.log(json);
    $.ajax({
        url : DJMATIC_JUKEBOX_SERVER_API,
        type : "POST",
        data : {
            method : "player.saveSettings",
            player_id : DJMATIC_PLAYER_ID,
            secret : DJMATIC_SECRET,
            settings : json
        },
        success : function(data, textStatus, XMLHttpRequest) {
            var jdata = JSON.parse(data);
            if (jdata.error != null) {
                sln.logError("Error occurred while saving settings\n" + jdata.error);
                sln.showAjaxError(data, textStatus, XMLHttpRequest);
            }
        },
        error : sln.showAjaxError
    });
};

var jukeboxOn = function() {
    updateJukeboxEnabled(!jukeboxEnabled);
};

var jukeboxOff = function() {
    updateJukeboxEnabled(!jukeboxEnabled);
};

var updateJukeboxEnabled = function (newJukeboxEnabled){
    jukeboxEnabled = newJukeboxEnabled;
    if(newJukeboxEnabled){
        $('#jukebox_cfg #jukeboxOn').addClass("btn-success").text(DJMaticTranslations.JUKEBOX_ENABLED);
        $('#jukebox_cfg #jukeboxOff').removeClass("btn-danger").html('&nbsp;');
        var json = JSON.stringify({
            status_player : 1
        });
        savePlayerSettings(json);
    }else{
        $('#jukebox_cfg #jukeboxOn').removeClass("btn-success").html('&nbsp;');
        $('#jukebox_cfg #jukeboxOff').addClass("btn-danger").text(DJMaticTranslations.JUKEBOX_DISABLED);
        var json = JSON.stringify({
            status_player : 0
        });
        savePlayerSettings(json);
    }
};

var dateChanged = function() {
    var val = 0;
    $('#jukebox_days label input').each(function(index) {
        if ($(this).is(":checked")) {
            val |= $(this).val();
        }
    });
    var json = JSON.stringify({
        status_days : val
    });
    savePlayerSettings(json);
};

var startTimeChanged = function(e) {
    var json = JSON.stringify({
        time_from : e.time.hours * 3600 + e.time.minutes * 60
    });
    savePlayerSettings(json);
};

var stopTimeChanged = function(e) {
    var json = JSON.stringify({
        time_until : e.time.hours * 3600 + e.time.minutes * 60
    });
    savePlayerSettings(json);
};

var maxSongsInQueueChanged = function(e) {
    var json = JSON.stringify({
        max_songs_in_queue : $('#max_songs_in_request_list').val(),
    });
    savePlayerSettings(json);
};

var genres_template = '{{if $genres}}'
        + '<hr>'
        + '<h3>Allowed Genres</h3>'
        + '{{/if}}'
        + '{{each(i, main_genre) genres}}'
        + '<table class="table table-striped table-hover table-bordered table-condensed" main_genre="${main_genre.name}">'
        + '     <thead>'
        + '         <tr>'
        + '             <th>'
        + '                <label class="checkbox">'
        + '                    <input type="checkbox" {{if main_genre.enabled == true}}checked{{/if}} genre_id="${main_genre.id}" genre="${main_genre.name}" genre_size="${main_genre.size}" {{if main_genre.size < 2 }}first_sub_genre="${genres[main_genre.name]["sub_genres"][0].id}"{{/if}}/>'
        + '                    ${main_genre.name}'
        + '                </label>'
        + '            </th>'
        + '        </tr>'
        + '     </thead>'
        + '{{if main_genre.size > 1}}'
        + '     <tbody {{if main_genre.enabled == false }}style="display: none"{{/if}}>'
        + '{{each(j, sub_genre) main_genre.sub_genres}}'
        + '         <tr>'
        + '            <td>'
        + '                <label class="checkbox" style="margin-left:50px">'
        + '                    <input type="checkbox" {{if sub_genre.enabled == true}}checked{{/if}} genre_id="${sub_genre.id}" genre="${sub_genre.name}" />'
        + '                     ${sub_genre.name}' //
        + '                </label>' //
        + '            </td>' //
        + '        </tr>' //
        + '{{/each}}' //
        + '     </tbody>'//
        + '{{/if}}' //
        + '</table>' //
        + '{{/each}}';
