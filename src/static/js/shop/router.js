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

$(document).ready(function () {
    // Show 'news' page by default
    $(window).on('hashchange', function () {
        var hash = window.location.hash.replace('#/', '').split('/');
        routingHandler(hash);
    });

    var hash = window.location.hash.replace('#/', '').split('/');
    routingHandler(hash);
});

/*
 Very primitive router based on the URL hash.
 */
function routingHandler(hash) {
    if (hash.length) {
        switch (hash[0]) {
            case 'news':
                // Show Extra city product by default.
                loadNews(function () {
                    if (hash[1]) {
                        switch (hash[1]) {
                            case 'new':
                                renderNewsForm();
                                break;
                            case 'edit':
                                renderNewsForm(hash[2]);
                                break;
                            case 'delete':
                                deleteNews(hash[2]);
                                break;
                            default:
                                renderNewsForm();
                                break;
                        }
                    }
                    else {
                        renderNews();
                    }
                });
                break;
            case 'legal_entities':
                switch (hash[1]) {
                    case 'create':
                        renderPutLegalEntity();
                        break;
                    case 'update':
                        renderPutLegalEntity(hash[2]);
                        break;
                    case 'list':
                    default:
                        renderListLegalEntities();
                        break;
                }
                break;
        }
    }
}
