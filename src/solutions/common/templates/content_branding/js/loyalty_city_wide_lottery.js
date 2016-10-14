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

var LOYALTY_TYPE_CITY_WIDE_LOTTERY = 4;

var qrCodeScannedCityWideLottery = function(now_, result) {
	hideLoading();
	rogerthat.api.call("solutions.loyalty.put", 
            JSON.stringify({
                'loyalty_type': LOYALTY_TYPE,
                'timestamp': Math.floor(Date.now() / 1000),
                'user_details': result.userDetails
            }),
            null);
	
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
            processCityWideLotteryPut(result.userDetails);
        }
    }, 15000);
};

var processCityWideLotteryPut = function(userDetails) {
	showTextPopupOverlay(Translations.TNX_LOYALTY_LOTTERY_VISIT_NO_DATE.replace("%(name)s", userDetails ? userDetails.name : ""), null, null, false, false);
	
	setTimeout(function(){
        hideTextPopupOverlay(startScanningForQRCode);
    }, 5000);
};
