/*
 * Copyright 2019 Green Valley Belgium NV
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
 * @@license_version:1.5@@
 */

(function () {
    "use strict";
    $('button[action=delete_expired_subscription]').click(function () {
        var customerId = parseInt($(this).parents('tr').attr('data-customer-id'));
        sln.confirm('Are you sure you want to delete this expired subscription?', function () {
            deleteExpiredSubscription(customerId);
        });
    });

    $('button[action=set_expired_subscription_status]').click(function () {
        var customerId = $(this).parents('tr').attr('data-customer-id');
        var expiredSubscriptionStatus = $(this).parents('tr').attr('data-subscription-status');
        $('#set_expired_subscription_modal').data('customerId', customerId).modal('show');
        $('#expired-subscription-status').val(expiredSubscriptionStatus);
    });

    $('#save-expired-subscription-status').click(function () {
        var modal = $('#set_expired_subscription_modal'),
            customerId = parseInt(modal.data('customerId')),
            status = parseInt($('#expired-subscription-status').val());
        sln.call({
            url: '/internal/shop/rest/customers/expired_subscriptions/set_status',
            method: 'post',
            data: {
                customer_id: customerId,
                status: status
            },
            success: function (data) {
                if (data.errormsg) {
                    sln.alert(data.errormsg);
                } else {
                    modal.modal('hide');
                    // Give the datastore some time to update indexes
                    setTimeout(function () {
                        location.reload();
                    }, 1500);
                }
            }
        });
    });

    function deleteExpiredSubscription (customerId) {
        sln.call({
            url: '/internal/shop/rest/customers/expired_subscriptions/delete',
            method: 'post',
            data: {
                customer_id: customerId
            },
            success: function (data) {
                if (data.errormsg) {
                    sln.alert(data.errormsg);
                } else {
                    $('tr[data-customer-id=' + customerId + ']').remove();
                }
            }
        });
    }
})();
