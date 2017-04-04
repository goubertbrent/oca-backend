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

var BORDER_COLOR_GRAY = "#dddddd";
var BORDER_COLOR_GRAY_1 = "#f6f6f6";
var BORDER_COLOR_ORANGE = "#ff8800";
var BORDER_COLOR_ORANGE_1 = "#ffcc00";

var language = "en-US";
var lastAudioSound = 0;
var notificationsUUID = null;
var totalNotifications = 0;
var isBacklogConnected = true;


var htmlize = function(value) {
    return $("<div></div>").text(value).html().replace(/\n/g, "<br>");
};

var isFlagSet = function(flag, value) {
    return (value & flag) == flag;
};

var parseDateToEventDateTime = function(d) {
    var momentTrans = moment(d).format("LLLL");
    return momentTrans;
};

var parseDateToEventDate = function(d) {
    var momentTrans = moment(d).format("LL");
    return momentTrans;
};

var playSound = function (url) {
    var tmp_time = new Date().getTime();
    if (lastAudioSound + 1000 < tmp_time) {
        lastAudioSound = tmp_time;
        console.log('Playing sound: ' + url);
        rogerthat.util.playAudio(url, function() {
            console.log("Sound success");
        }, function () {
            console.log("Sound failure");
        });
    } else {
        console.log('NOT Playing sound: ' + url);
    }
};

var getUserText = function() {
    if (currentScannedUser != null && currentScannedUser.name != undefined) {
        return Translations.WELCOME + " " + currentScannedUser.name;
    }
    return Translations.WELCOME;
};

var setPendingNotifications = function() {
    if(rogerthat.user.data.loyalty == undefined) {
        rogerthat.user.data.loyalty = {};
    }
    if(rogerthat.user.data.loyalty.inbox_unread_count == undefined) {
        rogerthat.user.data.loyalty.inbox_unread_count = 0;
    }
    console.log("inbox_unread_count: " + rogerthat.user.data.loyalty.inbox_unread_count);
    
    if (totalNotifications < rogerthat.user.data.loyalty.inbox_unread_count) {
        playSound('sound/notification.mp3');
    }
    totalNotifications = rogerthat.user.data.loyalty.inbox_unread_count;
    notificationsUUID = rogerthat.util.uuid();
    if (totalNotifications > 0) {
        $(".unread-inbox-count").show();
        $(".unread-inbox-count").text(totalNotifications);
        $("#open_dashboard a").css("border-color", BORDER_COLOR_ORANGE);
        $("#open_dashboard a").css("background-color", BORDER_COLOR_ORANGE_1);
        $("#open_dashboard a").css("font-size", "1.5em");
        if ($("#open_website").length) {
            $("#open_website").css("top", "180px");
            $("#no_internet").css("top", "280px");
        } else {
            $("#no_internet").css("top", "180px");
        }
        updateDashboardColor(notificationsUUID, false);
    } else {
        $(".unread-inbox-count").hide();
        $(".unread-inbox-count").text("");
        $("#open_dashboard a").css("border-color", BORDER_COLOR_GRAY);
        $("#open_dashboard a").css("background-color", BORDER_COLOR_GRAY_1);
        $("#open_dashboard a").css("font-size", "0.75em");
        if ($("#open_website").length) {
            $("#open_website").css("top", "100px");
            $("#no_internet").css("top", "180px");
        } else {
            $("#no_internet").css("top", "100px");
        }
    }
};

var updateDashboardColor = function(tag, color_enabled) {
    setTimeout(function(){
        if (tag == notificationsUUID) {
            if (color_enabled) {
                $("#open_dashboard a").css("border-color", BORDER_COLOR_ORANGE);
                $("#open_dashboard a").css("background-color", BORDER_COLOR_ORANGE_1);
            } else {
                $("#open_dashboard a").css("border-color", BORDER_COLOR_GRAY);
                $("#open_dashboard a").css("background-color", BORDER_COLOR_GRAY_1);
            }
            
            updateDashboardColor(tag, !color_enabled)
        }
    }, 2000);  
};

var startValidateBacklogConnected = function() {
    rogerthat.system.onBackendConnectivityChanged(function(r) {
        console.log("system.onBackendConnectivityChanged success");
        console.log("connected: " + r.connected);
        if (r.connected) {
            isBacklogConnected = true;
        } else {
            isBacklogConnected = false;
        }
        updateBacklogConnectedVisibility();
    }, function(r) {
        console.log("system.onBackendConnectivityChanged error");
    });
};

var updateBacklogConnectedVisibility = function() {
    if (isBacklogConnected) {
        $("#no_internet").hide();
    } else {
        $("#no_internet").show();
        $("#no_internet a").css("border-color", BORDER_COLOR_ORANGE);
        $("#no_internet a").css("background-color", BORDER_COLOR_ORANGE_1);
        $("#no_internet a").css("font-size", "1.5em");
        if (totalNotifications > 0) {
            if ($("#open_website").length) {
                $("#no_internet").css("top", "280px");
            } else {
                $("#no_internet").css("top", "180px");
            }
        } else {
            if ($("#open_website").length) {
                $("#no_internet").css("top", "180px");
            } else {
                $("#no_internet").css("top", "100px");
            }
        }
        updateBacklogConnectedColor(false);
    }
};

var updateBacklogConnectedColor = function(color_enabled) {
    setTimeout(function(){
        if (!isBacklogConnected) {
            if (color_enabled) {
                $("#no_internet a").css("border-color", BORDER_COLOR_ORANGE);
                $("#no_internet a").css("background-color", BORDER_COLOR_ORANGE_1);
            } else {
                $("#no_internet a").css("border-color", BORDER_COLOR_GRAY);
                $("#no_internet a").css("background-color", BORDER_COLOR_GRAY_1);
            }
            
            updateBacklogConnectedColor(!color_enabled)
        }
    }, 2000); 
};

var startScanningForQRCode = function() {
    if (!isFlagSet(FUNCTION_SCAN, tabletFunctions)) {
        console.log("FUNCTION_SCAN is not enabled");
        return;
    }

    rogerthat.camera.startScanningQrCode(cameraType, function(r) {
        console.log("camera.startScanningQrCode success");
    }, function(r) {
        console.log("camera.startScanningQrCode error");
    });
};

var stopScanningForQRCode = function() {
    rogerthat.camera.stopScanningQrCode(cameraType, function(r) {
        console.log("camera.stopScanningQrCode success");
    }, function(r) {
        console.log("camera.stopScanningQrCode error");
    });
};

language = window.navigator.languages ? window.navigator.languages[0] : null;
language = language || window.navigator.language || window.navigator.browserLanguage || window.navigator.userLanguage;
moment.locale(language);
