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

var tabletFunctions = 0;
var FUNCTION_SCAN = 1;
var FUNCTION_SLIDESHOW = 2;
var FUNCTION_ADD_REDEEM_LOYALTY_POINTS = 4;

var setTabletFunctions = function() {
    if(rogerthat.user.data.loyalty == undefined) {
        rogerthat.user.data.loyalty = {};
    }
    
    if (rogerthat.user.data.loyalty.functions == undefined) {
        tabletFunctions = 0;
        showErrorPopupOverlay(Translations.ERROR_OCCURED_UNKNOWN);
    } else {
        tabletFunctions = rogerthat.user.data.loyalty.functions;
    }
    
    console.log("tabletFunctions: " + tabletFunctions);
    
    if (!isFlagSet(FUNCTION_SCAN, tabletFunctions)) {
        console.log("FUNCTION_SCAN is not enabled");
        stopScanningForQRCode();
    }
    
    if (!isFlagSet(FUNCTION_SLIDESHOW, tabletFunctions)) {
        console.log("FUNCTION_SLIDESHOW is not enabled");
        $("#blueimp-gallery").hide();
        $("#osa-overlay").hide();
        return;
    }
    
    if (!isFlagSet(FUNCTION_ADD_REDEEM_LOYALTY_POINTS, tabletFunctions)) {
        console.log("FUNCTION_ADD_REDEEM_LOYALTY_POINTS is not enabled");
        $("#open_dashboard").hide();
    } else {
        $("#open_dashboard").show();
    }
};
