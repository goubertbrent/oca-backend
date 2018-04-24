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

$(function() {
    var joynUrl = 'https://www.joyn.be/for-merchants';
    if (LANGUAGE == 'nl') {
        joynUrl = 'https://www.joyn.be/nl/for-merchants'
    } else if (LANGUAGE == 'fr') {
        joynUrl = 'https://www.joyn.be/fr/for-merchants'
    } else if (LANGUAGE == 'en') {
        joynUrl = 'https://www.joyn.be/en/for-merchants'
    }
    $('#joyn_become_merchant').attr("href", joynUrl)
});
