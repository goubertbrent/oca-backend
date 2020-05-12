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

(function () {
    'use strict';
    var resolvingCouponUID,
        redeemingCouponUID,
        couponResolveCallback;

    modules.coupons = {
        resolveCoupon: resolveCoupon,
        resolveCouponFailed: resolveCouponFailed,
        redeemCoupon: redeemCoupon,
        redeemCouponFailed: redeemCouponFailed,
        couponResolved: couponResolved,
        couponRedeemed: couponRedeemed,
        couponRedeemedTimedOut: couponRedeemedTimedOut,
        processCouponResolved: processCouponResolved
    };

    function hideLoadingAndRestartScanning() {
        hideLoading();
        startScanningForQRCode();
    }

    function resolveCoupon(couponId, redeemingUser, callback) {
        var data = {
            coupon_id: couponId,
            redeeming_user: redeemingUser
        };
        couponResolveCallback = callback;
        var randomUID = rogerthat.util.uuid();
        // Used as tag for the API call.
        resolvingCouponUID = randomUID;
        rogerthat.api.call('solutions.coupons.resolve', JSON.stringify(data), resolvingCouponUID);

        setTimeout(function () {
            if (resolvingCouponUID === randomUID) {
                console.log('solutions.coupons.resolve timeout');
                resolvingCouponUID = null;
                showErrorPopupOverlay(Translations.INTERNET_SLOW_RETRY);
                hideLoadingAndRestartScanning();
            }
        }, 15000);
    }

    function resolveCouponFailed() {
        hideLoadingAndRestartScanning();
        resolvingCouponUID = null;
    }

    function redeemCoupon(couponId, redeemingUser) {
        var data = {
            coupon_id: couponId,
            redeeming_user: redeemingUser
        };
        var randomUID = rogerthat.util.uuid();
        // Used as tag for the API call.
        redeemingCouponUID = randomUID;
        rogerthat.api.call('solutions.coupons.redeem', JSON.stringify(data), redeemingCouponUID);

        setTimeout(function () {
            if (redeemingCouponUID === randomUID) {
                console.log('solutions.coupons.redeem timeout');
                redeemingCouponUID = null;
                hideLoadingAndRestartScanning();
                showErrorPopupOverlay(T('INTERNET_SLOW_RETRY'));
            }
        }, 15000);
    }

    function redeemCouponFailed() {
        redeemingCouponUID = null;
    }

    function couponRedeemed(data, tag) {
        if (!tag || tag !== redeemingCouponUID) {
            console.log('Invalid couponRedeemed tag', tag);
        } else if (!couponRedeemedTimedOut()) {
            hideLoadingAndRestartScanning();
            redeemingCouponUID = null;
            BootstrapDialog.alert(T('coupon_redeemed'));
        }
    }

    function couponResolved(data, tag) {
        if (!tag || tag !== resolvingCouponUID) {
            console.log('Invalid couponResolved tag', tag);
        } else if (!couponResolvedTimedOut()) {
            hideLoadingAndRestartScanning();
            resolvingCouponUID = null;
            couponResolveCallback(data);
        }
    }

    function couponRedeemedTimedOut() {
        return !redeemingCouponUID;
    }

    function couponResolvedTimedOut() {
        return !resolvingCouponUID;
    }

    function processCouponResolved(couponId, user, data) {
        // data should be a NewsCouponTO
        var msg = T('redeem_coupon_for_user', {user: user, coupon_content: data.content});
        BootstrapDialog.confirm({
            title: T('redeem_coupon'),
            message: msg,
            closable: true,
            btnOKLabel: T('Confirm'),
            callback: function (confirmed) {
                if (confirmed) {
                    showLoading(T('redeeming_coupon'));
                    redeemCoupon(couponId, user);
                }
            }
        });
    }
})();
