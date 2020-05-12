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

var LOYALTY_TYPE_LOTTERY = 2;

var setLoyaltySettingsLottery = function() {
    
};

var getNextLottery = function() {
    if(rogerthat.service.data.loyalty == undefined) {
        rogerthat.service.data.loyalty = {};
    }
    if(rogerthat.service.data.loyalty_2.dates == undefined) {
        rogerthat.service.data.loyalty_2.dates = [];
    }
    rogerthat.service.data.loyalty_2.dates.sort(function(a, b) {
        var dA = new Date(a.date.year, a.date.month - 1, a.date.day, a.date.hour, a.date.minute);
        var dB = new Date(b.date.year, b.date.month - 1, b.date.day, b.date.hour, b.date.minute);
        return dA - dB;
    });
    
    var now_ = Math.floor(Date.now() / 1000);
    for (var i in rogerthat.service.data.loyalty_2.dates) {
        var d = rogerthat.service.data.loyalty_2.dates[i];
        var ld = new Date(d.date.year, d.date.month - 1, d.date.day, d.date.hour, d.date.minute);
        if (now_ <= ld.getTime() / 1000) {
            d.datetime = ld;
            return d;
        }
    }
    return null;
};

var qrCodeScannedLottery = function(now_, result) {
    hideLoading();
    
    if(rogerthat.user.data.loyalty_2 == undefined) {
        rogerthat.user.data.loyalty_2 = {};
    }
    if(rogerthat.user.data.loyalty_2.winners == undefined) {
        rogerthat.user.data.loyalty_2.winners = [];
    }
    var winnerData = null;
    console.log("validating " + rogerthat.user.data.loyalty_2.winners.length + " winners");
    $.each(rogerthat.user.data.loyalty_2.winners, function (index, winner) {
        console.log("validating winner: " + winner.user_details.email + ":" + winner.user_details.app_id);
        console.log("me: " + result.userDetails.email + ":" + result.userDetails.appId);
        if (winner.user_details.email == result.userDetails.email && winner.user_details.app_id == result.userDetails.appId) {
            winnerData = winner
            return false;
        }
    });
    if (winnerData != null) {
        rogerthat.api.call("solutions.loyalty.redeem", 
                JSON.stringify({
                    'loyalty_type': LOYALTY_TYPE,
                    'timestamp': Math.floor(Date.now() / 1000),
                    'user_details': result.userDetails,
                    'key': winnerData.key
                }),
                null);
        console.log("WINNER FOUND");
        playSound('sound/tada.mp3');
        
        showTextPopupOverlay(Translations.YOU_ARE_THE_WINNER, Translations.CONTACT_OWNER_TO_REDEEM, htmlize(winnerData.winnings), true, true);
        return;
    }
    
    solutionsLoyaltyPutGuid = rogerthat.util.uuid();
    var tag = solutionsLoyaltyPutGuid;
    
    rogerthat.api.call("solutions.loyalty.put", 
            JSON.stringify({
                'loyalty_type' : LOYALTY_TYPE,
                'timestamp': now_,
                'user_details' : result.userDetails
            }),
            tag);
    currentScannedUser = result.userDetails;
    showLoading(Translations.SAVING_DOT_DOT_DOT);
    
    setTimeout(function(){
        if (tag == solutionsLoyaltyPutGuid) {
            console.log("solutions.loyalty.put timeout");
            solutionsLoyaltyPutGuid = null;
            hideLoading();
            processLotteryPut(true, result.userDetails);
        }
    }, 15000);
};

var processLotteryPut = function(isPut, userDetails) {
    if (isPut) {
        var lottery = getNextLottery();
        
        if (lottery == null) {
            showTextPopupOverlay(Translations.TNX_LOYALTY_LOTTERY_VISIT_NO_DATE.replace("%(name)s", userDetails ? userDetails.name : ""), null, null, false, false);
        } else {
            showTextPopupOverlay(Translations.TNX_LOYALTY_LOTTERY_VISIT.replace("%(name)s", userDetails ? userDetails.name : "").replace("%(date)s", parseDateToEventDateTime(lottery.datetime)), null, null, false, false);
        }
        
    } else {
        showTextPopupOverlay(Translations.LOYALTY_LOTTERY_VISIT_ONLY_ONCE);
    }
    
    setTimeout(function(){
        hideTextPopupOverlay(startScanningForQRCode);
    }, 5000);
};
