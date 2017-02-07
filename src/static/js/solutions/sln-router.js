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

$(document).ready(function () {
    // Show 'news' page by default
    $(window).on('hashchange', function () {
        var hash = window.location.hash.replace('#/', '').split('/');
        routingHandler(hash);
    });

    var hash = window.location.hash.replace('#/', '').split('/');
    if (SOLUTION != 'djmatic') {
        if (!hash) {
            window.location.hash = '#/news';
            return;
        } else if (hash[0] === '') {
            window.location.hash = '#/news';
            return;
        }
    }
    routingHandler(hash);
});

/*
 Very primitive router based on the URL hash.
 */
function routingHandler(hash) {
    var topMenuElement = $('#topmenu');
    if (hash.length) {
        switch (hash[0]) {
            case 'shop':
                $('#shoplink').click();
                var page = SHOP_PAGES[hash[1]];
                getStoreProducts(function () {
                    // Show Extra city product by default.
                    if (!hash[1]) {
                        window.location.hash = '/shop/product/' + EXTRA_CITY_CODE;
                    }
                    else if (SHOP_PAGES[hash[1]]) {
                        SHOP_PAGES[hash[1]](hash[2]);
                    } else {
                        SHOP_PAGES['product'](EXTRA_CITY_CODE);
                    }
                });
                break;
            case 'loyalty':
            	if (currentLoyaltyType > 0) {
            		if (currentLoyaltyType == LOYALTY_TYPE_CITY_WIDE_LOTTERY && HAS_LOYALTY) {
            			console.log("Not showing loyalty");
            		} else {
            			topMenuElement.find('[menu=loyalty] a').click();
            			switch (hash[1]) {
            			case 'export':
            				loadLoyaltyExportList();
            				loadVoucherExportList();
            				break;
            			default:
            				renderLoyaltyPage();
            			}
            		}
            	} else {
            		console.log("Loyalty settings not loaded yet.");
            	}
                break;
            case 'discussion_groups':
                topMenuElement.find('[menu=discussion_groups] a').click();
                switch (hash[1]) {
                    case 'new':
                        renderPutDiscussionGroup();
                        break;
                    case 'edit':
                        renderPutDiscussionGroup(hash[2]);
                        break;
                    case 'remove':
                        deleteDiscussionGroup(parseInt(hash[2]));
                        break;
                    default:
                        renderDiscussionGroups();
                }
                break;
            default:
                if(ROUTES[hash[0]]) {
                    topMenuElement.find('li[menu=' + hash[0] + '] a').click();
                    ROUTES[hash[0]](hash);
                }
        }
    }
}
