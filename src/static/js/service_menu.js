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

var serviceMenuScript = function () {
    var BRANDING_TYPE_NORMAL = 1;
    var BRANDING_TYPE_APP = 2;

    var COLORSCHEME_LIGHT = "light";
    var COLORSCHEME_DARK = "dark";
    var DEFAULT_COLORSCHEME = COLORSCHEME_LIGHT;

    var LABEL_ABOUT = "About";
    var LABEL_MESSAGES = "History";
    var LABEL_CALL = "Call";
    var LABEL_SHARE = "Recommend";

    var SMI_START_FLOW = 'radio_start_flow';
    var SMI_DEFAULT_SCREEN = 'radio_default_screen';
    var SMI_WEB_CALLBACK = 'radio_web_callback';
    var SMI_FORM = 'radio_form';
    var SMI_EMBEDDED_APP = 'radio_embedded_app';
    var SMI_WEB_PAGE = 'radio_web_page';

	var container = "#serviceMenuContainer";
	var lj = mctracker.getLocaljQuery(container);
	var current_page = 0;
	var create_icon_dialog = null;
	var smi_click_radio = null;
	var edit_menu_dialog = null;
	var edit_menu_icon = null;
	var edit_menu_icon_color = null;
	var color_preview = null;
	var color_error = null;
	var color_test = /^([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})$/;
	var edit_menu_icon_label = null;
	var edit_menu_icon_tag = null;
    var edit_menu_icon_current_tag = '';
    var edit_menu_icon_roles_label = null;
    var edit_menu_icon_current_roles = [];
	var edit_menu_coords = null;
	var edit_menu_icon_requires_wifi = null
	var edit_menu_icon_run_in_background = null;
	var edit_menu_icon_fall_through = null;
	var menu = null;
	var trash = null;
	var deleting = false;
	var title_height = null;
	var pages_height = null;
	var menu_height = null;
	var visible_rows = 0;
	var branding = null;
	var screen_branding_select = null;
	var static_flow_select = null;
	var share = null;
    var about_item_label = null;
    var messages_item_label = null;
    var share_item_label = null;
    var call_item_label = null;
    var call_popup = null;
    var service_identities = null;
    var service_identity_select = null;
    var selected_service_identity = DEFAULT_SERVICE_IDENTITY;
    var service_roles = null;
    var select_roles_dialog = null;

    var color_scheme = DEFAULT_COLORSCHEME;
    var default_menu_item_color = color_scheme == COLORSCHEME_LIGHT ? "000000" : "FFFFFF";

    var menu_loaded = false;
    var service_identities_loaded = false;

	var details_templ = "{{each items}}<tr class=\"row${$value.row}\"><td>${$value.display_coords}</td><td>${$value.label}</td><td>${$value.tag}</td></tr>{{/each}}";

    var roles_templ = '{{each service_roles}}<label><input type="checkbox" value="${$value.id}" {{if $value.checked}}checked{{/if}}/> ${$value.name}</label><br />{{/each}}';

    var ICONS = [];

    var configureDelayedTextInput = function (textInput, callback) {
        var lastKeyStroke = 0;
        textInput.keyup(function () {
            lastKeyStroke = new Date().getTime();
            window.setTimeout(function () {
                if (new Date().getTime() - lastKeyStroke >= 2000) {
                    callback($.trim(textInput.val()));
                }
            }, 2000);
        });
    };

    var configureLabelKeyUp = function (textInput, column) {
        configureDelayedTextInput(textInput, function (val) {
            mctracker.call({
                url: '/mobi/rest/service/menu/item_label',
                type: 'POST',
                data: {
                    data: JSON.stringify({
                        label: val,
                        column: column
                    })
                },
                success: function () {
                    loadMenu();
                }
            });
        });
    };

	var initScreen = function() {
		title_height = lj("#title").height();
		pages_height = lj("#pages").height();
		menu_height = lj("#menu").height();
		edit_menu_icon = lj("#icon");
		edit_menu_icon_color = lj("#color");
		color_preview = lj("#color_preview");
		color_error = lj("#color_error");
		edit_menu_icon_label = lj("#label");
		edit_menu_icon_tag = lj("#tag").change(function() {
		    edit_menu_icon_current_tag = edit_menu_icon_tag.val();
		});
		edit_menu_icon_roles_label = lj("#roles");
		edit_menu_icon_requires_wifi = lj("#requires_wifi");
		edit_menu_icon_run_in_background = lj("#run_in_background");
		edit_menu_icon_fall_through = lj("#fall_through");
		branding = lj("#branding");
        screen_branding_select = lj("#default_screen");
		static_flow_select = lj("#static_flow");
        share = lj("#share");
        about_item_label = lj("#about_label");
        messages_item_label = lj("#configuration #messages_label");
        call_item_label = lj("#configuration #call_label");
        share_item_label = lj("#configuration #share_label");
        call_popup = lj("#configuration #call_popup");
        service_identity_select = lj("#menu_identity select").change(function () {
            selected_service_identity = $(this).val();
            loadMenu();
        });

        lj("#menu_identity #edit_service_identity").click(function () {
            loadServiceIdentityForEditing(selected_service_identity);
        });

        edit_menu_icon_color.keyup(function () {
            var $this = $(this);
            var color = $this.val() || default_menu_item_color;
			if (color_test.test(color)) {
                color_preview.css('background-color', '#' + color);
                color_preview.show();
                color_error.hide();
                edit_menu_icon.parent().find('i').css('color', '#' + color);
                if (edit_menu_icon.attr('url')) {
                    edit_menu_icon.attr('src', edit_menu_icon.attr('url') + "?color=" + color);
                }
            } else {
                color_preview.hide();
                color_error.show();
            }
		});

		lj("#editDialog #edit_icon").click(function() {
            showCreateIconLibrary(function () {
            });
        });

		lj("#editDialog #set_roles").click(function() {
            if (!service_roles) {
                mctracker.alert("First add roles in the 'Service roles' page.", null, "There are no roles yet");
                return;
            }

            select_roles_dialog.dialog('open');

            var visibleForEveryone = edit_menu_icon_current_roles.length == 0;
            $("#checkboxEveryone", select_roles_dialog).prop('checked', visibleForEveryone);
            $.each(service_roles, function (i, role) {
                role.checked = !visibleForEveryone && edit_menu_icon_current_roles.indexOf(role.id) != -1;
            });
            $("#rolesContainer", select_roles_dialog).empty().append($.tmpl(roles_templ, {
                service_roles : service_roles,
                edit_menu_icon_current_roles : edit_menu_icon_current_roles
            }));

            roleEveryoneClick();
        });

        select_roles_dialog = lj("#selectRolesDialog").dialog({
            title : "Visible for",
            autoOpen : false,
            modal : true,
            buttons : {
                Ok : submitRoles,
                Cancel : function() {
                    select_roles_dialog.dialog('close');
                }
            }
        });

        $("#checkboxEveryone", select_roles_dialog).click(roleEveryoneClick);

        var SHOW_CONTENT_HEIGHT = 640;
        var START_FLOW_HEIGHT = 545;
        var OPEN_WEB_PAGE_HEIGHT = 560;
        var WEBCALLBACK_HEIGHT = 500;

		edit_menu_dialog = lj("#editDialog").dialog({
			title: "Edit menu item",
			autoOpen: false,
			modal: true,
			width: 410,
			height: SHOW_CONTENT_HEIGHT,
			resizable: false,
			buttons: {
				Save: submitIcon,
				Cancel: function () {
				    edit_menu_dialog.dialog('close');
				    select_roles_dialog.dialog('close');
			    }
			}
		});

		smi_click_radio = $("input[name='behavior']", edit_menu_dialog).change(function () {
            var selection = {
                start_flow: edit_menu_dialog.find('#' + SMI_START_FLOW).prop('checked'),
                default_screen: edit_menu_dialog.find('#' + SMI_DEFAULT_SCREEN).prop('checked'),
                web_page: edit_menu_dialog.find('#' + SMI_WEB_PAGE).prop('checked'),
                web_callback: edit_menu_dialog.find('#' + SMI_WEB_CALLBACK).prop('checked'),
                form: edit_menu_dialog.find('#' + SMI_FORM).prop('checked'),
                embedded_app: edit_menu_dialog.find('#' + SMI_EMBEDDED_APP).prop('checked')
            };

            $.each(selection, function (behavior, selected) {
                edit_menu_dialog.find('tr[behavior="' + behavior + '"]').toggle(selected);
            });

            if (selection.start_flow) {
                edit_menu_icon_tag.attr('disabled', false).val(edit_menu_icon_current_tag);
                edit_menu_dialog.dialog("option", "height", START_FLOW_HEIGHT);
            } else if (selection.default_screen) {
                edit_menu_icon_tag.attr('disabled', false).val(edit_menu_icon_current_tag);
                edit_menu_dialog.dialog("option", "height", SHOW_CONTENT_HEIGHT);
            } else if (selection.web_page) {
                edit_menu_icon_tag.attr('disabled', false).val(edit_menu_icon_current_tag);
                edit_menu_dialog.dialog("option", "height", OPEN_WEB_PAGE_HEIGHT);
            } else if (selection.form) {
                edit_menu_icon_tag.attr('disabled', false).val(edit_menu_icon_current_tag);
                edit_menu_dialog.dialog("option", "height", OPEN_WEB_PAGE_HEIGHT);
            } else if (selection.embedded_app) {
                edit_menu_icon_tag.attr('disabled', false).val(edit_menu_icon_current_tag);
                edit_menu_dialog.dialog("option", "height", OPEN_WEB_PAGE_HEIGHT);
            } else {
                // Web callback
                edit_menu_icon_tag.attr('disabled', false).val(edit_menu_icon_current_tag);
                edit_menu_dialog.dialog("option", "height", WEBCALLBACK_HEIGHT);
            }
        });
		lj("#menu td").click(menuItemClick).droppable({
			drop: function (event, ui) {
				var source_coords = ui.draggable.parent().data('item').coords;
				var target_coords = getCoords($(this));
				ui.draggable.css('z-index', '10');
				mctracker.call({
					url: "/mobi/rest/service/menu/move",
					type: "POST",
					data: {
						data: JSON.stringify({
							source_coords: source_coords,
							target_coords: target_coords
						})
					},
					success: function () {
						loadMenu(function () {
							ui.draggable.css('left', '');
							ui.draggable.css('top', '');
							ui.draggable.css('z-index', '');
						});
					}
				});
			},
			accept: function (draggable) {
				if (! draggable.parent().data('item'))
					return false;
				return $(this).attr("used") == "false";
            }
		});
        lj("#menu td div").draggable({
			revert: "invalid",
			zIndex: 10,
			cursor: 'move',
			start: function () { trash.fadeIn('slow');},
			stop: function () { if (! deleting) trash.fadeOut('slow');}
		});
		trash = lj("#editor #trash");
		trash.droppable({
			drop: function (event, ui) {
				var coords = ui.draggable.parent().data('item').coords;
				deleting = true;
				mctracker.call({
					url: "/mobi/rest/service/menu/delete",
					type: "POST",
					data: {
						data: JSON.stringify({
							coords: coords
						})
					},
					success: function () {
						loadMenu(function () {
							ui.draggable.css('left', '');
							ui.draggable.css('top', '');
							ui.draggable.css('z-index', '');
							trash.fadeOut('slow');
							deleting = false;
						});
					}
				});
			},
			accept: function (draggable) {
				if (! draggable.parent().data('item'))
					return false;
				return true;
			}
		});

		configureLabelKeyUp(about_item_label, 0);
		configureLabelKeyUp(messages_item_label, 1);
		configureLabelKeyUp(call_item_label, 2);
        configureLabelKeyUp(share_item_label, 3);

		loadMenu();
        loadServiceIdentities();

        loadBrandings();
        loadStaticFlows();
        loadServiceRoles();
	};

    var loadBrandings = function () {
        screen_branding_select.empty();
        mctracker.call({
            url: "/mobi/rest/branding/list",
            data: {
                filtered_type: -1
            },
            success: function (data) {
                screen_branding_select.append($("<option></option>").attr('value', '').text('no screen'));

                $.each(data.sort(descriptionSort), function (i, brand) {
                    screen_branding_select.append($("<option></option>").attr('value', brand.id).text(brand.description+" ["+mctracker.formatDate(brand.timestamp)+"]"));
                });
            }
       });
    };

    var loadStaticFlows = function () {
        static_flow_select.empty();
        mctracker.call({
            url: "/mobi/rest/mfd/list_valid",
            success: function (data) {
                static_flow_select.append($("<option></option>").attr('value', '').text('no message flow'));

                $.each(data.message_flows, function (i, mfd) {
                    static_flow_select.append($("<option></option>").attr('value', mfd.name).text(mfd.name + " [" + mctracker.formatDate(mfd.timestamp) + "]"));
                });
            }
       });
    };

	var onIdentitySaved = function (success, errorMsg) {
	    if (success) {
	        loadMenu();
	        createIdentityDialog.dialog('close');
	    } else {
	        mctracker.alert(errorMsg);
	    }
	}

    var loadServiceIdentityForEditing = function (identifier) {
        mctracker.call({
            url:"/mobi/rest/service/identity",
            data: {
                identifier: identifier
            },
            success: function (serviceIdentityToBeEdited) {
                if (serviceIdentityToBeEdited.identifier == DEFAULT_SERVICE_IDENTITY) {
                    setDefaultServiceIdentity(serviceIdentityToBeEdited);
                    openEditServiceIdentityDialog(serviceIdentityToBeEdited, onIdentitySaved);
                } else {
                    // Load default identity
                    mctracker.call({
                        url:"/mobi/rest/service/identity",
                        data: {
                            identifier: DEFAULT_SERVICE_IDENTITY
                        },
                        success: function (defaultServiceIdentityForEditing) {
                            setDefaultServiceIdentity(defaultServiceIdentityForEditing);
                            openEditServiceIdentityDialog(serviceIdentityToBeEdited, onIdentitySaved);
                        }
                    });
                }
            }
        });
    };

    var loadServiceIdentities = function () {
        service_identities_loaded = false;
        mctracker.call({
            url: '/mobi/rest/service/identities',
            success: function (identities) {
                service_identity_select.empty();
                service_identities = [];
                var selected_identity_found = false;
                $.each(identities.sort(sortServiceIdentities), function (i, identity) {
                    service_identities[identity.identifier] = identity;
                    var identifier = identity.identifier == DEFAULT_SERVICE_IDENTITY ? "default" : identity.identifier;
                    service_identity_select.append($("<option></option>").text(identity.name + ' [' + identifier + ']').val(identity.identifier));
                    if (selected_service_identity == identity.identifier)
                        selected_identity_found = true;
                });
                if (!selected_identity_found)
                    selected_service_identity = DEFAULT_SERVICE_IDENTITY;

                service_identity_select.val(selected_service_identity);

                if (!selected_identity_found)
                    service_identity_select.val(selected_service_identity).change();

                service_identities_loaded = true;
                if (menu_loaded)
                    showPage();
            }
        });
    };

    var loadServiceRoles = function () {
        mctracker.call({
            url: '/mobi/rest/service/roles',
            success: function (roles) {
                service_roles = roles;

                if (service_roles.length == 0) {
                    lj("#editDialog #set_roles").removeAttr('disabled');
                } else {
                    lj("#editDialog #set_roles").attr('disabled', 'true');
                }
            }
        });
    };

	var getCoords = function (td) {
        var coords = $.map(td.attr('id').split('x'), function (o, i) {
            return Number(o);
        });
		coords.push(current_page);
		return coords;
	};

    var roleEveryoneClick = function () {
        var rolesCheckboxes = $("#rolesContainer input", select_roles_dialog);
        var rolesLabels = $("#rolesContainer label", select_roles_dialog);
        if ($("#checkboxEveryone", select_roles_dialog).prop('checked')) {
            rolesCheckboxes.attr("disabled", "true");
            rolesLabels.attr("disabled", "true");
        } else {
            rolesCheckboxes.removeAttr("disabled");
            rolesLabels.removeAttr("disabled");
        }
    };

	var menuItemClick = function() {
		var td = $(this);
		var coords = getCoords(td);
        if (coords[1] == 0 && coords[2] == 0)
			return; // reserved for system actions
		edit_menu_coords = coords;
		edit_menu_icon_color.attr('placeholder', default_menu_item_color);
		var item = td.data('item');

        edit_menu_dialog.find('#input_web_page').val('');
        edit_menu_dialog.find('#input_form_id').val('');
        edit_menu_dialog.find('#input_embedded_app').val('');
        edit_menu_dialog.find('#external_web_page').val('internal');
        edit_menu_dialog.find('#user_context_web_page').prop('checked', false);

		if (item) {
			edit_menu_icon_color.val(item.iconColor);
			var color = item.iconColor || default_menu_item_color;
            edit_menu_icon.attr('name', item.iconName);
            color_preview.css('background-color', '#' + color);
            if (item.iconName.indexOf('fa-') === 0) {
                edit_menu_icon.hide()
                    .parent().find('i')
                    .attr('class', 'fa ' + item.iconName)
                    .css('color', '#' + color);
            } else {
                edit_menu_icon.show()
                    .attr('src', item.iconUrl + "?color=" + color)
                    .attr('url', item.iconUrl)
                    .parent().find('i').removeClass();
            }
            edit_menu_icon_label.val(item.label);
            edit_menu_icon_tag.val(item.tag);
            edit_menu_icon_requires_wifi.prop('checked', item.requiresWifi);
            edit_menu_icon_run_in_background.prop('checked', item.runInBackground);
            edit_menu_icon_fall_through.prop('checked', item.fallThrough);
            edit_menu_icon_current_tag = item.tag;
            edit_menu_icon_current_roles = item.roles;
            screen_branding_select.val(item.screenBranding || '');
            static_flow_select.val(item.staticFlowName || '');
            if (item.link) {
                edit_menu_dialog.find('#' + SMI_WEB_PAGE).prop('checked', true).change();
                edit_menu_dialog.find('#input_web_page').val(item.link.url);
                edit_menu_dialog.find('#external_web_page').val(item.link.external ? "external" : "internal");
                edit_menu_dialog.find('#user_context_web_page').prop('checked', item.link.request_user_link);
            } else if (item.screenBranding) {
                edit_menu_dialog.find('#' + SMI_DEFAULT_SCREEN).prop('checked', true).change();
            } else if (item.staticFlowName) {
                edit_menu_dialog.find('#' + SMI_START_FLOW).prop('checked', true).change();
            } else if (item.form) {
                edit_menu_dialog.find('#' + SMI_FORM).prop('checked', true).change();
                edit_menu_dialog.find('#input_form_id').val(item.form.id);
            } else if (item.embeddedApp) {
                edit_menu_dialog.find('#' + SMI_EMBEDDED_APP).prop('checked', true).change();
                edit_menu_dialog.find('#input_embedded_app').val(item.embeddedApp);
            } else {
                edit_menu_dialog.find('#' + SMI_WEB_CALLBACK).prop('checked', true).change();
            }
		} else {
			edit_menu_icon_color.val('');
			color_preview.css('background-color', '#' + default_menu_item_color);
            edit_menu_icon.parent().find('i').removeClass();
			edit_menu_icon.attr('src', '');
			edit_menu_icon.attr('url', '');
			edit_menu_icon.attr('name', '');
			edit_menu_icon_label.val('');
			edit_menu_icon_tag.val('');
			edit_menu_icon_requires_wifi.prop('checked', false);
            edit_menu_icon_run_in_background.prop('checked', true);
            edit_menu_icon_fall_through.prop('checked', false);
			edit_menu_icon_current_tag = null;
            edit_menu_icon_current_roles = []; // Everyone
			screen_branding_select.val('');
			static_flow_select.val('');
			$('#' + SMI_WEB_CALLBACK, edit_menu_dialog).prop('checked', true).change();
		}
        setSelectedRolesString();
		edit_menu_dialog.dialog('open');
	};

	var setSelectedRolesString = function () {
	    var s;
	    if (edit_menu_icon_current_roles.length == 0) {
	        s = 'Everyone';
	    } else {
	        s = '';
	        $.each(service_roles, function (i, role) {
	            if (edit_menu_icon_current_roles.indexOf(role.id) != -1) {
	                if (s)
	                    s += ", ";
	                s += role.name;
	            }
	        });
	    }
	    edit_menu_icon_roles_label.text(s);
	};

	var loadMenu = function (callback) {
	    menu_loaded = false;
		mctracker.call({
			url: '/mobi/rest/service/menu',
			data: {
			    identifier: selected_service_identity
			},
			success: function (data) {
				menu = data;
				$.each(menu.items, function (i, item) {
					item.display_coords = item.coords[2]+1;
					item.row = item.coords[1]+1;
				});
				lj("#details").empty().append($.tmpl(details_templ, data));
				menu_loaded = true;
				if (service_identities_loaded)
				    showPage();
				if (callback)
					callback();
			}
		});
	};

	var processColorScheme = function () {
	    if ( color_scheme == COLORSCHEME_LIGHT ) {
            lj(".rt-cs-dark").removeClass("rt-cs-dark").addClass("rt-cs-light");
            lj(".rt-cs-dark-empty").removeClass("rt-cs-dark-empty").addClass("rt-cs-light-empty");
            lj("img[src=\"/static/images/current_page.png\"]").attr("src", "/static/images/current_page_light.png");
            lj("img[src=\"/static/images/other_page.png\"]").attr("src", "/static/images/other_page_light.png");
        } else {
            lj(".rt-cs-light").removeClass("rt-cs-light").addClass("rt-cs-dark");
            lj(".rt-cs-light-empty").removeClass("rt-cs-light-empty").addClass("rt-cs-dark-empty");
            lj("img[src=\"/static/images/current_page_light.png\"]").attr("src", "/static/images/current_page.png");
            lj("img[src=\"/static/images/other_page_light.png\"]").attr("src", "/static/images/other_page.png");
        }
	};

	var showPage = function () {
	    lj("#title").text(service_identities[selected_service_identity].name);
		lj("#canvas").css('background', '');
		lj("#pages").css('margin-top', '');
		lj("#branding").val(menu.branding);
		lj("#phone").val(menu.phoneNumber);
        lj(".rt-cs-dark").removeClass("rt-cs-dark");
        lj(".rt-cs-light").removeClass("rt-cs-light");
		share.val(menu.shareQRId || '');

		about_item_label.val(menu.aboutLabel || LABEL_ABOUT);
		messages_item_label.val(menu.messagesLabel || LABEL_MESSAGES);
		call_item_label.val(menu.callLabel || LABEL_CALL);
		share_item_label.val(menu.shareLabel || LABEL_SHARE);

		if (menu.phoneNumber) {
            lj("#call_label_row").show();
            lj("#call_popup_row").show();
            call_popup.val(menu.callConfirmation || "Call " + menu.phoneNumber);
	    } else {
            lj("#call_label_row").hide();
            lj("#call_popup_row").hide();
	    }
	    if (menu.shareQRId) {
	        lj("#share_label_row").show();
	    } else {
	        lj("#share_label_row").hide();
	    }

		if ( menu.branding ) {
			lj("#title").hide();
			var iframe = lj("#canvas_branding")
				.attr('src', '/branding/'+menu.branding+'/branding.html')
				.css('height', '')
				.load(function () {
				    $('nuntiuz_identity_name', iframe.contents()).replaceWith($('<span></span>').text(service_identities[selected_service_identity].name));

					var branding_doc = iframe.get(0).contentWindow.document;
					var background_color = $("meta[property=\"rt:style:background-color\"]", branding_doc).attr("content");
					color_scheme = $("meta[property=\"rt:style:color-scheme\"]", branding_doc).attr("content") || DEFAULT_COLORSCHEME;
					var branded_menu_item_color = $("meta[property=\"rt:style:menu-item-color\"]", branding_doc).attr("content");
					if (branded_menu_item_color) {
					    if (branded_menu_item_color.indexOf("#") == 0)
					        default_menu_item_color = branded_menu_item_color.substring(1);
					    else
					        default_menu_item_color = branded_menu_item_color;
					} else {
					    default_menu_item_color = color_scheme == COLORSCHEME_LIGHT ? "000000" : "FFFFFF";
					}
                    if (current_page === 0) {
                        lj('.rounded_icon_background').css('background-color', '#' + default_menu_item_color);
                        lj("#0x0").find('i').show().css('color', background_color);
                        lj("#1x0").find('i').show().css('color', background_color);
                        lj("#2x0").find('i').show().css('color', background_color);
                        lj("#3x0").find('i').show().css('color', background_color);
					}
					$.each(menu.items, function(i, item) {
                        if (!item.iconColor && item.iconName.indexOf('fa-') === 0 && item.coords[2] == current_page) {
                            lj("#" + item.coords[0] + "x" + item.coords[1]).find('i').css('color', background_color);
                        }
                    });
					processColorScheme();

					if ( background_color ) {
						lj("#canvas").css('background', background_color);
					}
					iframe.show();
                    iframe.height(50);
                    var iframeDocument = iframe.contents().get(0);
                    iframe.height($(iframeDocument).height() + 5);
				});
		} else {
			lj("#title").show();
			lj("#canvas").css('background', color_scheme == COLORSCHEME_LIGHT ? 'white' : 'dark');
			lj("#canvas_branding").hide();
         		processColorScheme();
			$("tr", lj("#menu")).show();
			visible_rows = 4;
        	}
		var clear_contents = ["0x1", "1x1", "2x1", "3x1", "0x2", "1x2", "2x2", "3x2"];
		if (current_page == 0) {
			var parent = lj("#0x0");
			parent.find('i').show().attr('class', 'fa ' + "fa-info").parent().show();
			parent.find('img').hide();
            		$("span.menu_icon_label", parent).text(menu.aboutLabel || LABEL_ABOUT);
			parent.addClass("rt-cs-reserved");
			parent.removeClass("rt-cs-light");
			parent.removeClass("rt-cs-light-empty");
			parent.removeClass("rt-cs-dark-empty");
			parent.attr("used", "true");
			parent.data("item", null);
			parent = lj("#1x0");
			parent.find('i').show().attr('class', 'fa ' + "fa-envelope").parent().show();
			parent.find('img').hide();
            		$("span.menu_icon_label", parent).text(menu.messagesLabel || LABEL_MESSAGES);
			parent.addClass("rt-cs-reserved");
			parent.removeClass("rt-cs-light");
			parent.removeClass("rt-cs-light-empty");
			parent.removeClass("rt-cs-dark-empty");
			parent.attr("used", "true");
			parent.data("item", null);
			$.each([2,3], function (i, o) {
				parent = lj("#"+o+"x0");
				$("img", parent).attr('src', '/static/images/menu_reserved.png').parent().show();
				parent.find('i').hide();
                $("span.menu_icon_label", parent).text("");
				parent.addClass("rt-cs-reserved");
				parent.removeClass("rt-cs-light");
				parent.removeClass("rt-cs-light-empty");
				parent.removeClass("rt-cs-dark-empty");
				parent.attr("used", "true");
				parent.data("item", null);
			});
			parent = lj("#2x0");
			if ( menu.phoneNumber ) {
				parent.find('i').show().attr('class', 'fa ' + "fa-phone").parent().show();
				parent.find('img').hide();
                $("span.menu_icon_label", parent).text(menu.callLabel || LABEL_CALL);
				parent.addClass("rt-cs-reserved");
				parent.removeClass("rt-cs-light");
				parent.removeClass("rt-cs-light-empty");
				parent.removeClass("rt-cs-dark-empty");
				parent.attr("used", "true");
				parent.data("item", null);
			} else {
				parent.find('i').show().attr('class', 'fa ' + "fa-phone").parent().hide();
				parent.find('img').hide();
                        }
			parent = lj("#3x0");
			if ( menu.shareQRId ) {
				parent.find('i').show().attr('class', 'fa ' + "fa-thumbs-o-up").parent().show();
				parent.find('img').hide();
                $("span.menu_icon_label", parent).text(menu.shareLabel || LABEL_SHARE);
				parent.addClass("rt-cs-reserved");
				parent.removeClass("rt-cs-light");
				parent.removeClass("rt-cs-light-empty");
				parent.removeClass("rt-cs-dark-empty");
				parent.attr("used", "true");
				parent.data("item", null);
			} else {
				parent.find('i').show().attr('class', 'fa ' + "fa-thumbs-o-up").parent().hide();
				parent.find('img').hide();
			}
		} else {
			clear_contents.push("0x0");
			clear_contents.push("1x0");
			clear_contents.push("2x0");
			clear_contents.push("3x0");
		}
		$.each(clear_contents, function (i, item) {
			var parent = lj("#"+item);
			parent.find('i').show().attr('class', 'fa ' + "fa-question-circle").css('color', '#646464').parent().show();
			parent.find('img').hide();
            		$("span.menu_icon_label", parent).text("Empty");
			parent.removeClass("rt-cs-reserved");
			parent.removeClass("rt-cs-light");
			parent.addClass("rt-cs-light-empty");
			parent.attr("used", "false");
			parent.data("item", null);
		});
		var max_page = 0;
		$.each(menu.items, function (i, item) {
			if (item.coords[2] > max_page)
                max_page = item.coords[2];
			if (item.coords[2] != current_page)
				return;
			var parent = lj("#"+item.coords[0]+"x"+item.coords[1]);
            if (item.iconName.indexOf('fa-') === 0) {
                parent.find('i').show().attr('class', 'fa ' + item.iconName).css('color', '#' + item.iconColor || default_menu_item_color).parent().show();
                parent.find('img').hide();
            } else {
                parent.find('i').hide().parent().hide();
                parent.find('img').show()
                    .attr('src', '/mobi/service/menu/icons?coords=' + item.coords.join("x") + '&service=' + encodeURIComponent(loggedOnUserEmail) + '&time=' + (new Date().getTime() / 1000));
            }
            $("span.menu_icon_label", parent).text(item.label);
            parent.data("item", item)
                .removeClass("rt-cs-reserved rt-cs-light-empty rt-cs-dark-empty")
                .addClass("rt-cs-light")
                .attr("used", "true");
		});
		var pages = lj("#editor #pages");
		pages.empty();
		var change_page_function = function (page) {
			return function () {
				current_page = page;
				showPage();
			};
        };
		max_page++;
		for (var page=0; page <= max_page; page++) {
			if (page == current_page) {
				pages.append($("<img></img>").attr("src", "/static/images/current_page_light.png"));
			} else {
				pages.append($("<img></img>").attr("src", "/static/images/other_page_light.png").css('cursor','pointer').click(change_page_function(page)));
			}
		}
	};

    var submitRoles = function () {
	    var visibleForEveryone = $('#checkboxEveryone', select_roles_dialog).is(':checked');
	    if (visibleForEveryone) {
	        edit_menu_icon_current_roles = [];
	    } else {
	        var checkedRoleCheckboxes = $('#rolesContainer input[type="checkbox"]:checked', select_roles_dialog);

	        edit_menu_icon_current_roles = checkedRoleCheckboxes.map(function() {
	            return parseInt(this.value);
	        }).get();
	    }

	    setSelectedRolesString();
	    select_roles_dialog.dialog('close');
	};

	var submitIcon = function() {
		var icon_name = edit_menu_icon.attr('name');
		var icon_color = edit_menu_icon_color.val() || null;
		var icon_label = edit_menu_icon_label.val();
		var icon_tag = edit_menu_icon_tag.val();
		var icon_requires_wifi = edit_menu_icon_requires_wifi.prop('checked');
		var icon_run_in_background = edit_menu_icon_run_in_background.prop('checked');
		var icon_fall_through = edit_menu_icon_fall_through.prop('checked');

        var sb = ($('#' + SMI_DEFAULT_SCREEN, edit_menu_dialog).prop('checked')) ? (screen_branding_select.val() || null) : null;
		var sf = ($('#' + SMI_START_FLOW, edit_menu_dialog).prop('checked')) ? (static_flow_select.val() || null) : null;

		var link = null;
		if (edit_menu_dialog.find('#' + SMI_WEB_PAGE).prop('checked')) {
		    link = {
		        url: edit_menu_dialog.find('#input_web_page').val(),
		        external: edit_menu_dialog.find('#external_web_page').val() == 'external',
		        request_user_link: edit_menu_dialog.find('#user_context_web_page').prop('checked')
		    };
		}

        var formId = null;
        if (edit_menu_dialog.find('#' + SMI_FORM).prop('checked')) {
            formId = parseInt(edit_menu_dialog.find('#input_form_id').val());
        }
        var embeddedApp = null;
        if (edit_menu_dialog.find('#' + SMI_EMBEDDED_APP).prop('checked')) {
            embeddedApp = edit_menu_dialog.find('#input_embedded_app').val();
        }

		if (! (icon_name && icon_label && icon_tag)) {
			mctracker.alert("Not all properties are set.");
			return;
		}
		if (icon_color && !color_test.test(icon_color)) {
			mctracker.alert("Icon color is not valid.");
			return;
		}

		mctracker.call({
			url: "/mobi/rest/service/menu/create",
			type: "POST",
			data: {
				data: JSON.stringify({
					icon_name: icon_name,
					icon_color: icon_color,
					label: icon_label,
					tag: icon_tag,
					roles: edit_menu_icon_current_roles,
					coords: edit_menu_coords,
                    screen_branding: sb,
					static_flow: sf,
					requires_wifi: icon_requires_wifi,
					run_in_background: icon_run_in_background,
					link: link,
                    fall_through: icon_fall_through,
                    form_id: formId,
                    embedded_app: embeddedApp,
				})
			},
			success: function (data) {
			    if (data.success) {
    				edit_menu_dialog.dialog('close');
                    select_roles_dialog.dialog('close');
    				loadMenu();
			    } else {
			        mctracker.alert(data.errormsg);
			    }
			}
		});
	};

    var iconSelected = function (icon) {
	    var color = edit_menu_icon_color.val();
	    if (!color || !color_test.test(color)) {
	        color = default_menu_item_color;
	    }
		create_icon_dialog.dialog('close');
        edit_menu_icon.attr('name', icon.name);
        if (icon.name.indexOf('fa-') === 0) {
            edit_menu_icon.hide().parent().find('i').show().attr('class', 'fa ' + icon.name).css('color', '#' + color);
        } else {
            edit_menu_icon.attr('src', '/mobi/service/menu/icons/lib/' + icon.name + "?color=" + color);
            edit_menu_icon.show().parent().find('i').hide();
        }
	};

    var showCreateIconLibrary = function () {
		if (create_icon_dialog) {
			create_icon_dialog.dialog('open');
			return;
		}
		mctracker.call({
			url: "/mobi/rest/service/icon-library/list",
			success: function (data) {
                ICONS = data;
				var table = lj("#createIconDialog #icons");
				var tr = null;
                $.each(ICONS, function (i, icon) {
					if ( i % 7 == 0) {
						tr = $("<tr></tr>");
						table.append(tr);
					}
					var td = $("<td></td>");
					tr.append(td);
                    var html;
                    if (icon.name.indexOf('fa-') === 0) {
                        html = $('<i class="fa">').addClass(icon.name).css('font-size', '50px');
                    } else {
                        html = $("<img>");
                        html.attr("src", '/mobi/service/menu/icons/lib/' + icon.name);
                        html.attr("width", "50");
                        html.attr("height", "50");
                    }
                    td.append(html);
                    td.append($("<div>").text(icon.label));
					td.addClass("un_selected_icon");
                    td.attr('name', icon.name);
				});
                $("td", table).click(function () {
                    table.find("td").attr("class", "un_selected_icon");
                    var $this = $(this);
                    var td = $this.addClass("selected_icon");
                    var name = $this.attr('name');
                    var ic = ICONS.filter(function (i) {
                        return i.name === name;
                    })[0];
                    iconSelected(ic);
				});
				create_icon_dialog = lj("#createIconDialog").dialog({
					title: "Select icon",
					autoOpen: false,
					width: 800,
					height: 500,
					resizable: false,
					modal: true
				});
				showCreateIconLibrary();
			}
		});
	};

    return function () {
		initScreen();
        mctracker.registerMsgCallback(function (data) {
            if (data.type == 'rogerthat.services.identity.refresh') {
                loadServiceIdentities();
                loadMenu();
            } else if (data.type == 'rogerthat.service.branding.refresh') {
                loadBrandings();
            } else if (data.type == 'rogerthat.mfd.changes') {
                loadStaticFlows();
            } else if (data.type == 'rogerthat.service.roles.updated') {
                loadServiceRoles();
            }
        });
	};
};

mctracker.registerLoadCallback("serviceMenuContainer", serviceMenuScript());
