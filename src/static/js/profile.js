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

function profileScript() {
    'use strict';
	var container = "#profileContainer";
	var lj = mctracker.getLocaljQuery(container);
	var isService = false;
    var newImage = null;
	
	var applyJQueryInUI = function () {
        reloadAvatar();
		lj("button.save_button").button().click(save);
		lj("#change_pwd").button().click(function () {
			window.location = "/resetpassword?email=" + loggedOnUserEmail;
		});
        lj('#avatar_div').click(function () {
            mctracker.uploadImage('Create profile picture', 150, 150, acceptAvatar);
        });

        function acceptAvatar(image) {
            newImage = image;
            save();
        }

    };

    function reloadAvatar() {
        $("#avatar, #myProfile img").attr('src', '/mobi/profile/my_avatar?user=' + encodeURIComponent(loggedOnUserEmail) + '&_=' + new Date().getTime());
    }

    function save() {
	    var name = null;
	    var language = null;
	    if (!isService) {
            name = trim(lj("#name").val());
            if (! name || name.search(/@/) != -1  || name.length > 50) {
                lj("#nameErrorMsg").show();
                return;
            }
            lj("#nameErrorMsg").hide();
            language = lj("#language").val();
        }
		
		mctracker.call({
			url: "/mobi/rest/profile/update",
			data: { 
				data: JSON.stringify({
					name: name,
					language: language,
                    image: newImage,
				})
			},
			type: 'POST',
            success: function (data) {
                if (data) {
                    mctracker.alert("Could not persist your profile.\nRefresh the page and try again.\nError: " + data);
                }
                reloadAvatar();
			},
			error: function(XMLHttpRequest, textStatus, errorThrown) {
			    mctracker.alert("Could not persist your profile.\nRefresh the page and try again.\nError: "+errorThrown);
			}
		});
    }

    function loadProfile() {
		mctracker.call({
			url: "/mobi/rest/profile/get",
            success: function (data) {
				if (data) {
				    isService = data.isService;
					if (isService) {
						lj(".human_users_only").hide();
                        lj(".service_users_only").show();
                        lj("#organization_type").val(data.organizationType);
					} else {
                        lj(".service_users_only").hide();
                        lj(".human_users_only").show();
					    lj("#name").val(data.name).focus();
						lj("#passport").attr('src', '/invite?code='+data.userCode).parent().attr('href', '/q/i'+data.userCode);
						
						var language = data.userLanguage ? data.userLanguage : 'en';
						
						var select = lj("#language");
				        for (var i = 0; i < data.allLanguages.length; i++) {
				            var short_lang = data.allLanguages[i];
				            var long_lang = data.allLanguagesStr[i];
				            select.append($('<option></option>').attr('value', short_lang).text(long_lang));
				        }
				        $("option[value='"+language+"']", select).attr('selected', '');
					}
				}
			},
			error: mctracker.showAjaxError		
		});
    }

    return function () {
        applyJQueryInUI();
		loadProfile();
	};
}

mctracker.registerLoadCallback("profileContainer", profileScript());
