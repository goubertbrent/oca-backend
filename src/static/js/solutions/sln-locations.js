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
 * @@license_version:1.3@@
 */

$(function() {
    var loadLocations = function() {
        sln.call({
            url : "/common/locations/load",
            type : "GET",
            success : function(data) {
                if (data.length) {
                    showLocations(data);
                } else {
                    window.location.reload();
                }
            },
            error : sln.showAjaxError
        });
    };

    var showLocations = function(locations) {
        var html = $.tmpl(templates.location, {
            locations : locations,
            CommonTranslations : CommonTranslations
        });
        
        $(".locations").empty().append(html);
        
        $(".use-this-location", html).click(function() {
           var service_identity = $(this).attr("service_identity");
           sln.showProcessing(CommonTranslations.LOADING_DOT_DOT_DOT);
           sln.call({
               url : "/common/locations/use",
               type : "POST",
               data : {
                   data : JSON.stringify({
                       service_identity : service_identity
                   })
               },
               success : function(data) {
               },
               error : sln.showAjaxError
           });
        });
    };
    
    loadLocations();
    
    var channelUpdates = function(data) {
        if (data.type == 'solutions.common.locations.update') {
            window.location.reload();
        }
    };
    sln.registerMsgCallback(channelUpdates);
});
