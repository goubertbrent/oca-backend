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

var LOYALTY_TYPE_STAMPS = 3;

var STAMPS_TYPE_1_PER_SCAN = 1;
var STAMPS_TYPE_X_PER_SCAN = 2;

var x_stamps = 8;
var stamps_type = 1;
var stamps_auto_redeem = false;
var maxStampCardsToRedeem = 1;

var setLoyaltySettingsStamps = function() {
    if (rogerthat.service.data.loyalty_3 != undefined) {
        if (rogerthat.service.data.loyalty_3.settings != undefined) {
            x_stamps = rogerthat.service.data.loyalty_3.settings.x_stamps;
            stamps_type = rogerthat.service.data.loyalty_3.settings.stamps_type;
            
            if (rogerthat.service.data.loyalty_3.settings.stamps_auto_redeem != undefined) {
                stamps_auto_redeem = rogerthat.service.data.loyalty_3.settings.stamps_auto_redeem;
            }
        }
    }
    console.log("x_stamps: " + x_stamps);
    console.log("stamps_type: " + stamps_type);
    console.log("stamps_auto_redeem: "  + stamps_auto_redeem);
};

var qrCodeScannedStamps = function(now_, result) {
    if (isFlagSet(FUNCTION_ADD_REDEEM_LOYALTY_POINTS, tabletFunctions)) {
        currentScannedUser = result.userDetails;

        solutionsLoyaltyLoadGuid = rogerthat.util.uuid();
        var tag = solutionsLoyaltyLoadGuid;
        rogerthat.api.call("solutions.loyalty.load",
                JSON.stringify({
                    'loyalty_type' : LOYALTY_TYPE,
                    'timestamp': now_,
                    'user_details' : result.userDetails
                }),
                tag);

        setTimeout(function(){
            if (tag == solutionsLoyaltyLoadGuid) {
                console.log("solutions.loyalty.load timeout");
                solutionsLoyaltyLoadGuid = null;
                hideLoading();
                showErrorPopupOverlay(Translations.INTERNET_SLOW_RETRY);
            }
        }, 15000);
    } else {
        solutionsLoyaltyScanGuid = rogerthat.util.uuid();
        var tag = solutionsLoyaltyScanGuid;
        rogerthat.api.call("solutions.loyalty.scan",
                JSON.stringify({
                    'loyalty_type' : LOYALTY_TYPE,
                    'timestamp': now_,
                    'user_details' : result.userDetails
                }),
                tag);

        setTimeout(function(){
            if (tag == solutionsLoyaltyScanGuid) {
                console.log("solutions.loyalty.scan timeout");
                solutionsLoyaltyScanGuid = null;
                hideLoading();
                showErrorPopupOverlay(Translations.INTERNET_SLOW_CONTINUE);
            }
        }, 15000);
    }
};

var put1Stamp = function() {
    var params = {
        loyalty_type : LOYALTY_TYPE,
        timestamp : Math.floor(Date.now() / 1000),
        count : 1,
        user_details : currentScannedUser
    };
    
    rogerthat.api.call("solutions.loyalty.put", JSON.stringify(params), null);
    
    showLoading(Translations.SAVING_DOT_DOT_DOT);
    
    setTimeout(function() {
        hideLoading();
        startScanningForQRCode();
    }, 2000);
};

var redeemStampCard = function(count) {
    showLoading(Translations.REDEEMING_STAMPS);
    solutionsLoyaltyRedeemGuid = rogerthat.util.uuid();
    var tag = solutionsLoyaltyRedeemGuid;
    
    rogerthat.api.call("solutions.loyalty.redeem", 
                       JSON.stringify({
                                'loyalty_type': LOYALTY_TYPE,
                                'timestamp': Math.floor(Date.now() / 1000),
                                'count': count,
                                'user_details': currentScannedUser
                        }),
                        tag);
    
    setTimeout(function(){
        if (tag == solutionsLoyaltyRedeemGuid) {
            console.log("solutions.loyalty.redeem timeout");
            solutionsLoyaltyRedeemGuid = null;
            hideLoading();
            showErrorPopupOverlay(Translations.INTERNET_SLOW_CONTINUE);
        }
    }, 15000);
};

var shouldShowQRScannedSelectPopupOverlayStamps = function() {
    var count = 0;
    if (stamps_type == STAMPS_TYPE_1_PER_SCAN || stamps_auto_redeem) {
        if (currentScannedInfo != null) {
            $.each(currentScannedInfo.visits, function (i, visit) {
                count += visit.value_number;
            });
            
            console.log("should show got " + currentScannedInfo.visits.length + " visits");
        }
        console.log("should show got " + count + " stamps");
    }
    if (count >= x_stamps) {
        if (stamps_auto_redeem) {
            playSound('sound/trumpet.mp3');
            redeemStampCard(1);
            return false;
        }
    } else if (stamps_type == STAMPS_TYPE_1_PER_SCAN) {
        put1Stamp();
        return false;
    }
    return true;
};

var hideAdd3PopupOverlay = function(callback) {
    console.log("hideAdd3PopupOverlay");
    if (callback != undefined) {
        $("#main #add-3-popup").on( "popupafterclose", function() {
            $("#main #add-3-popup").off( "popupafterclose");
            setTimeout(callback, 10);
        });
    }
    $("#main #add-3-popup").popup("close");  // needs to be double for first close
    if (shouldDoubleClose)
        $("#main #add-3-popup").popup("close");
};

var showAdd3PopupOverlay = function() {
    console.log("showAdd3PopupOverlay");
    
    if (stamps_type == STAMPS_TYPE_1_PER_SCAN) {
        put1Stamp();
        
    } else {
        $("#main #add-3-popup .add-3-popup-enabled").hide();
        $("#main #add-3-popup .add-3-popup-disabled").hide();
        $("#main #add-3-popup .user_name").text(getUserText());
        var count = 0;
        if (currentScannedInfo != null) {
            $.each(currentScannedInfo.visits, function (i, visit) {
                count += visit.value_number;
            });
            
            console.log("Add got " + currentScannedInfo.visits.length + " visits");
        }
        console.log("Add got " + count + " stamps");
        
        var input = $('#main #add-3-popup .calculator .screen');
        input.text('1');
        $("#main #add-3-popup .add-3-popup-enabled").show();
        $("#main #add-3-popup .calculator .add-3-min-1").hide();
        $("#main #add-3-popup .calculator .add-3-min-5").hide();
        $("#main #add-3-popup .calculator .add-3-min-10").hide();
        $("#main #add-3-popup").popup("open", {positionTo: 'window'});
    }
};

var hideRedeem3PopupOverlay = function(callback) {
    console.log("hideRedeem3PopupOverlay");
    if (callback != undefined) {
        $("#main #redeem-3-popup").on( "popupafterclose", function() {
            $("#main #redeem-3-popup").off( "popupafterclose");
            setTimeout(callback, 10);
        });
    }
    $("#main #redeem-3-popup").popup("close");  // needs to be double for first close
    if (shouldDoubleClose)
        $("#main #redeem-3-popup").popup("close");
};

var showRedeem3PopupOverlay = function() {
    console.log("showRedeem3PopupOverlay");
    
    $("#main #redeem-3-popup .redeem-3-popup-enabled").hide();
    $("#main #redeem-3-popup .redeem-3-popup-disabled").hide();
    
    var count = 0;
    if (currentScannedInfo != null) {
        $.each(currentScannedInfo.visits, function (i, visit) {
            count += visit.value_number;
        });
        console.log("Redeem got " + currentScannedInfo.visits.length + " visits");
    }
    console.log("Redeem got " + count + " stamps");

    if (currentScannedInfo != null && count >= x_stamps) {
        maxStampCardsToRedeem = parseInt(count / x_stamps);  
        if (maxStampCardsToRedeem > 1) {
            $("#main #redeem-3-popup .redeem_text").text(Translations.REDEEM_TEXT_STAMPS_MORE.replace("%(count)s", maxStampCardsToRedeem));
        }  else {
            $("#main #redeem-3-popup .redeem_text").text(Translations.REDEEM_TEXT_STAMPS_ONE);
        }
        $("#main #redeem-3-popup .redeem_text").show();
        if (maxStampCardsToRedeem > 1) {
            var input = $('#main #redeem-3-popup .calculator .screen');
            input.text('1');
            $("#main #redeem-3-popup .calculator .redeem-3-plus-1").show();
            $("#main #redeem-3-popup .calculator .redeem-3-min-1").hide();
            $("#main #redeem-3-popup .calculator").show();
        } else {
            $("#main #redeem-3-popup .calculator").hide();
        }
        $("#main #redeem-3-popup .redeem-3-popup-enabled").show();
    } else {
        $("#main #redeem-3-popup .disabled_msg").text(Translations.REDEEM_STAMPS_DISABLED_ADD_FIRST);
        $("#main #redeem-3-popup .redeem-3-popup-disabled").show();
    }
    $("#main #redeem-3-popup .user_name").text(getUserText());
    $("#main #redeem-3-popup").popup("open", {positionTo: 'window'});
};

$(document).on("touchend click", ".closeAdd3Popup", function(event) {
    event.stopPropagation();
    event.preventDefault();

    var selected = $(this).attr("addAction");
    console.log("closeAdd3Popup selected: " + selected);
    if (LOYALTY_TYPE == LOYALTY_TYPE_STAMPS) {
        if (selected == "submit") {
            var count = parseInt($('#main #add-3-popup .calculator .screen').text());
            
            hideAdd();
            showLoading(Translations.ADDING_STAMPS);
            solutionsLoyaltyPutGuid = rogerthat.util.uuid();
            var tag = solutionsLoyaltyPutGuid;
            rogerthat.api.call("solutions.loyalty.put", 
                    JSON.stringify({
                            'loyalty_type': LOYALTY_TYPE,
                            'timestamp': Math.floor(Date.now() / 1000),
                            'count' : count,
                            'user_details' : currentScannedUser
                    }),
                    tag);
            
            setTimeout(function(){
                if (tag == solutionsLoyaltyPutGuid) {
                    console.log("solutions.loyalty.put timeout");
                    solutionsLoyaltyPutGuid = null;
                    hideLoading();
                    showErrorPopupOverlay(Translations.INTERNET_SLOW_CONTINUE);
                }
            }, 15000);
            
        } else if (selected == "close") {
            hideAdd(showQRScannedSelectPopupOverlay);
        } else {
            hideAdd(startScanningForQRCode);
        }
    } else {
        hideAdd(startScanningForQRCode);
    }
});

$(document).on("touchend click", ".closeRedeem3Popup", function(event) {
    event.stopPropagation();
    event.preventDefault();

    var selected = $(this).attr("redeemAction");
    console.log("closeRedeem3Popup selected: " + selected);
    if (LOYALTY_TYPE == LOYALTY_TYPE_STAMPS) {
        if (selected == "redeem") {
            var count = 1;
            if (maxStampCardsToRedeem > 1) {
                count = parseInt($('#main #redeem-3-popup .calculator .screen').text());
            }
            
            hideRedeem();
            redeemStampCard(count);
        } else if (selected == "close") {
            hideRedeem(showQRScannedSelectPopupOverlay);
        } else {
            hideRedeem(startScanningForQRCode);
        }
    } else {
        hideRedeem(startScanningForQRCode);
    }
});

$(document).on("touchend click", "#main #add-3-popup .calculator span", function(event) {
    event.stopPropagation();
    event.preventDefault();

    var btnVal = this.innerHTML;
    var input = $('#main #add-3-popup .calculator .screen');
    if(btnVal == 'C') {
        input.text('1');
        $("#main #add-3-popup .calculator .add-3-min-1").hide();
        $("#main #add-3-popup .calculator .add-3-min-5").hide();
        $("#main #add-3-popup .calculator .add-3-min-10").hide();
    } else {
        var newValue = parseInt(input.text()) + parseInt(btnVal);
        if (newValue <= 1) {
            newValue = 1;
            $("#main #add-3-popup .calculator .add-3-min-1").hide();
            $("#main #add-3-popup .calculator .add-3-min-5").hide();
            $("#main #add-3-popup .calculator .add-3-min-10").hide();
        } else if (newValue < 5) {
            $("#main #add-3-popup .calculator .add-3-min-1").show();
            $("#main #add-3-popup .calculator .add-3-min-5").hide();
            $("#main #add-3-popup .calculator .add-3-min-10").hide();
        } else if (newValue < 10) {
            $("#main #add-3-popup .calculator .add-3-min-1").show();
            $("#main #add-3-popup .calculator .add-3-min-5").show();
            $("#main #add-3-popup .calculator .add-3-min-10").hide();
        } else {
            $("#main #add-3-popup .calculator .add-3-min-1").show();
            $("#main #add-3-popup .calculator .add-3-min-5").show();
            $("#main #add-3-popup .calculator .add-3-min-10").show();
        }
        input.text(newValue);
    }
});

$(document).on("touchend click", "#main #redeem-3-popup .calculator span", function(event) {
    event.stopPropagation();
    event.preventDefault();

    var btnVal = this.innerHTML;
    var input = $('#main #redeem-3-popup .calculator .screen');
    if(btnVal == 'C') {
        input.text('1');
        $("#main #redeem-3-popup .calculator .redeem-3-min-1").hide();
        $("#main #redeem-3-popup .calculator .redeem-3-plus-1").show();
    } else {
        var newValue = parseInt(input.text()) + parseInt(btnVal);
        if (newValue <= 1) {
            newValue = 1;
            $("#main #redeem-3-popup .calculator .redeem-3-min-1").hide();
            $("#main #redeem-3-popup .calculator .redeem-3-plus-1").show();
        } else if (newValue >= maxStampCardsToRedeem) {
            newValue = maxStampCardsToRedeem;
            $("#main #redeem-3-popup .calculator .redeem-3-min-1").show();
            $("#main #redeem-3-popup .calculator .redeem-3-plus-1").hide();
        } else {
            $("#main #redeem-3-popup .calculator .redeem-3-min-1").show();
            $("#main #redeem-3-popup .calculator .redeem-3-plus-1").show();
        }
        input.text(newValue);
    }
});
