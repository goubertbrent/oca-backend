/*
 * Copyright 2017 GIG Technology NV
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
   if (!Modernizr.canvas || 
       !Modernizr.canvastext || 
       !Modernizr.inputtypes.number || 
       !Modernizr.inputtypes.color || 
       !Modernizr.borderradius) {
       
       sln.alert(CommonTranslations.BROWSER_SWITCH_TO_CHROME + '<br><br><a href="https://www.google.com/chrome/" target="_blank">' + CommonTranslations.DOWNLOAD_GOOGLE_CHROME + '</a>', 
               null, 
               CommonTranslations.BROWSER_NOT_FULLY_SUPPORTED);
   }
});
