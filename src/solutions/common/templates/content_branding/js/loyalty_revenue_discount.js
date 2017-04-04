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

var LOYALTY_TYPE_REVENUE_DISCOUNT = 1;

var x_visits = 10;
var x_discount = 5;

var setLoyaltySettingsRevenueDiscount = function() {
    if (rogerthat.service.data.loyalty != undefined) {
        if (rogerthat.service.data.loyalty.settings != undefined) {
            x_visits = rogerthat.service.data.loyalty.settings.x_visits;
            x_discount = rogerthat.service.data.loyalty.settings.x_discount;
        }
    }
    console.log("x_visits: " + x_visits);
    console.log("x_discount: " + x_discount);
};

var qrCodeScannedRevenueDiscount = function(now_, result) {
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

var hideAdd1PopupOverlay = function(callback) {
    console.log("hideAdd1PopupOverlay");
    if (callback != undefined) {
        $("#main #add-1-popup").on( "popupafterclose", function() {
            $("#main #add-1-popup").off( "popupafterclose");
            setTimeout(callback, 10);
        });
    }
    $("#main #add-1-popup").popup("close");  // needs to be double for first close
    if (shouldDoubleClose)
        $("#main #add-1-popup").popup("close");
};

var showAdd1PopupOverlay = function() {
    console.log("showAdd1PopupOverlay");
    
    $("#main #add-1-popup .add-1-popup-enabled").hide();
    $("#main #add-1-popup .add-1-popup-disabled").hide();
    $("#main #add-1-popup .user_name").text(getUserText());
    
    if (currentScannedInfo != null && currentScannedInfo.visits.length >= x_visits) {
        $("#main #add-1-popup .disabled_msg").text(Translations.ADD_POINTS_DISABLED_REDEEM_FIRST);
        $("#main #add-1-popup .add-1-popup-disabled").show();
    } else {
        var input = $('#main #add-1-popup .calculator .screen');
        calculatorDecimalAdded = false;
        input.text('');
        $("#main #add-1-popup .add-1-popup-enabled").show();
    }
    $("#main #add-1-popup").popup("open", {positionTo: 'window'});
};

var hideRedeem1PopupOverlay = function(callback) {
    console.log("hideRedeem1PopupOverlay");
    if (callback != undefined) {
        $("#main #redeem-1-popup").on( "popupafterclose", function() {
            $("#main #redeem-1-popup").off( "popupafterclose");
            setTimeout(callback, 10);
        });
    }
    $("#main #redeem-1-popup").popup("close");  // needs to be double for first close
    if (shouldDoubleClose)
        $("#main #redeem-1-popup").popup("close");
};

var showRedeem1PopupOverlay = function() {
    console.log("showRedeem1PopupOverlay");
    var redeemPopup = $("#main #redeem-1-popup");
    redeemPopup.find('.redeem-1-popup-enabled, .redeem-1-popup-disabled').hide();
    
    if (currentScannedInfo != null && currentScannedInfo.visits.length >= x_visits) {
        console.log("Redeem " + currentScannedInfo.visits.length + " visits");
        var totalPrice = 0;
        $.each(currentScannedInfo.visits, function (i, visit) {
            if (i >= x_visits) {
                return false;
            }
            totalPrice += visit.value_number;
        });
        console.log("Redeem " + totalPrice + " eurocents");
        totalPrice = totalPrice / 100;
        var totalPriceStr = totalPrice.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        var totalPriceDiscount = Math.round(totalPrice * x_discount) / 100;
        
        var totalPriceDiscountStr = totalPriceDiscount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        redeemPopup.find('.redeem_text')
            .text(Translations.REDEEM_TEXT_DISCOUNT.replace("{0}", x_discount + '%')
                .replace("{1}", totalPriceStr)
                .replace("{2}", totalPriceDiscountStr))
            .show();
        redeemPopup.find('.redeem-1-popup-enabled').show();
    } else {
       redeemPopup.find(".disabled_msg").text(Translations.REDEEM_POINTS_DISABLED_ADD_FIRST);
       redeemPopup.find(".redeem-1-popup-disabled").show();
    }
    redeemPopup.find(".user_name").text(getUserText());
    redeemPopup.popup("open", {positionTo: 'window'});
};

$(document).on("touchend click", ".closeAdd1Popup", function(event) {
    event.stopPropagation();
    event.preventDefault();

    var selected = $(this).attr("addAction");
    console.log("closeAdd1Popup selected: " + selected);
    if (LOYALTY_TYPE == LOYALTY_TYPE_REVENUE_DISCOUNT) {
        if (selected == "submit") {
            var priceText = $('#main #add-1-popup .calculator .screen').text();
            var priceFloat = parseFloat(priceText);
            
            if(isNaN(priceFloat)) {
                $("#main #add-1-popup .error_msg").text(Translations.PRICE_IS_NOT_A_NUMBER)
                    .show();
                return;
            }
            
            hideAdd();
            showLoading(Translations.ADDING_LOYALTY_POINTS);
            solutionsLoyaltyPutGuid = rogerthat.util.uuid();
            var tag = solutionsLoyaltyPutGuid;
            rogerthat.api.call("solutions.loyalty.put", 
                    JSON.stringify({
                            'loyalty_type': LOYALTY_TYPE,
                            'timestamp': Math.floor(Date.now() / 1000),
                            'user_details' : currentScannedUser,
                            'price' : priceFloat * 100
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

$(document).on("touchend click", ".closeRedeem1Popup", function(event) {
    event.stopPropagation();
    event.preventDefault();

    var selected = $(this).attr("redeemAction");
    console.log("closeRedeem1Popup selected: " + selected);
    if (LOYALTY_TYPE == LOYALTY_TYPE_REVENUE_DISCOUNT) {
        if (selected == "redeem") {
            hideRedeem();
            showLoading(Translations.REDEEMING_LOYALTY_POINTS);
            solutionsLoyaltyRedeemGuid = rogerthat.util.uuid();
            var tag = solutionsLoyaltyRedeemGuid;
            
            rogerthat.api.call("solutions.loyalty.redeem", 
                               JSON.stringify({
                                        'loyalty_type': LOYALTY_TYPE,
                                        'timestamp': Math.floor(Date.now() / 1000),
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
            
        } else if (selected == "close") {
            hideRedeem(showQRScannedSelectPopupOverlay);
        } else {
            hideRedeem(startScanningForQRCode);
        }
    } else {
        hideRedeem(startScanningForQRCode);
    }
});

$(document).on("touchend click", "#main #add-1-popup .calculator span", function(event) {
    event.stopPropagation();
    event.preventDefault();

    var btnVal = this.innerHTML;
    var input = $('#main #add-1-popup .calculator .screen');
    if(btnVal == 'C') {
        input.text('');
        calculatorDecimalAdded = false;
    } else if(btnVal == '.') {
        if(!calculatorDecimalAdded) {
            input.text(input.text() + btnVal);
            calculatorDecimalAdded = true;
        }
    } else {
        input.text(input.text() + btnVal);
    }
});
