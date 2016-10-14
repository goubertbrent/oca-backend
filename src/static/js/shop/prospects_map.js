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

var map, prospectTypeaheadTimeout, oms;
var currentMarkers = [];
var currentProspects = [];

$(function() {
    var ViewModeType = {
        MAP : 'map',
        LIST : 'list'
    };
    var mapCanvas = $('#map-canvas');
    var body = $('body');

    var viewMode = ViewModeType[$('#prospects_view_mode').find('.btn.active').attr('data-view-mode').toUpperCase()];

    var FilteredStatusTypes = [];
    $.each(StatusType, function(k, v) {
        if (v != StatusType.NOT_EXISTING) {
            FilteredStatusTypes.push(v);
        }
    });
    var prospectExportElem = $('#prospects_export');

    var resize = function() {
        var h = window.innerHeight - mapCanvas.position().top - parseInt(body.css('padding'))
            - parseInt(body.css('margin'));
        mapCanvas.css('height', h - 12 + 'px');
        $('#list-canvas').css('height', h - 113 + 'px');
    };

    window.onresize = resize;
    resize();

    prospectExportElem.click(exportCurrentProspects);

    $('#prospects_filter').click(function() {
        if ($(this).hasClass('disabled')) {
            return;
        }

        var modal = $('#prospects_filter_modal').modal('show');
        var statusContainer = $('#filter-status', modal).empty();
        $.each(ORDERED_STATUSES, function(i, status) {
            var html = $($('#prospects_filter_checkbox_tmpl').html());
            $('input', html).val(status).prop('checked', FilteredStatusTypes.indexOf(status) != -1);
            $('img', html).attr('src', getMarkerIcon(status));
            $('.status-string', html).text(StatusTypeStrings[status]);
            statusContainer.append(html);
        });
    });

    $('#prospects_filter_modal').on('hide', function() {
        var modal = $(this);
        FilteredStatusTypes = $('#filter-status').find('input[type="checkbox"]:checked', modal).map(function () {
            return parseInt(this.value);
        }).get();

        filterProspects();
    });

    $('#prospects_filter_modal .select-all-btn, #prospects_filter_modal .deselect-all-btn').click(
            function() {
                $('#prospects_filter_modal').find('.tab-pane.active input[type="checkbox"]').prop('checked',
                        $(this).hasClass('select-all-btn'));
            });

    $('#prospects_view_mode').find('.btn').click(function () {
        viewMode = ViewModeType[$(this).attr('data-view-mode')];
        initView();
    });

    var listCanvasBody = $('#list-canvas').find('tbody');
    var appSelect = $('#prospects_app_id');
    var categorySelect = $('#prospect_category');
    categorySelect.change(function () {
        var $this = $(this);
        loadProspects(appSelect.val(), categorySelect.val(), null);
    });
    appSelect.change(function () {
        var appId = appSelect.val();
        $('#prospects_filter, #prospects_export').toggleClass('disabled', !appId);
        loadProspects(appId, categorySelect.val(), null);
    });

    var isProspectVisible = function(prospect) {
        // STATUS
        return FilteredStatusTypes.indexOf(prospect.status) !== -1;
    };

    var filterProspects = function() {
        // Map
        $.each(currentMarkers, function(i, marker) {
            var visible = isProspectVisible(marker._prospect);
            marker.setVisible(visible);
        });

        // List
        listCanvasBody.find('tr').each(function () {
            var tr = $(this);
            var prospectId = tr.attr('data-prospect-id');
            var prospect = currentProspects.filter(function (p) {
                return p.id === prospectId;
            })[0];
            if (isProspectVisible(prospect)) {
                tr.removeClass('hide');
            } else {
                tr.addClass('hide');
            }
        });
    };

    var addProspectToMap = function(prospect) {
        var coords = new google.maps.LatLng(prospect.lat, prospect.lon);
        var markerOptions = {
            position : coords,
            map : map,
            cursor : 'pointer',
            visible: FilteredStatusTypes.indexOf(prospect.status) != -1,
            zIndex : (prospect.status == StatusType.TODO ? 1 : -1)
        };
        var markerIcon = getMarkerIcon(prospect.status);
        if (markerIcon) {
            markerOptions.icon = markerIcon;
        }
        var marker = new google.maps.Marker(markerOptions);
        marker._prospect = prospect;
        currentMarkers.push(marker);

        oms.addMarker(marker);
    };


    var addProspectsToList = function (prospects, updateOrNew) {
        var currentCategory = $('#prospect_category').val();
        var html = $.tmpl(JS_TEMPLATES.prospect_list_view_row, {
            prospects: prospects,
            currentCategory: currentCategory,
            MarkerStatusMapping: MarkerStatusMapping,
            htmlize: sln.htmlize,
            FILTERED_STATUS_TYPES: FilteredStatusTypes,
            getMarkerIcon: getMarkerIcon
        });
        if (updateOrNew === 'update') {
            var prospect = prospects[0];
            // We received a channel update with a new prospect
            // Find the right place where to insert this prospect
            var prospectIndex = currentProspects.indexOf(prospect);
            if (prospectIndex == -1) {
                currentProspects.push(prospect);
                currentProspects.sort(addressSort);
                prospectIndex = currentProspects.indexOf(prospect);
            }

            if (prospectIndex === 0) {
                listCanvasBody.prepend(html);
            } else {
                var insertAfter = currentProspects[prospectIndex - 1];
                listCanvasBody.find('tr[data-prospect-id="' + insertAfter.id + '"]').after(html);
            }
        } else if (updateOrNew === 'edit') {
            $('#list-canvas').find('tbody').find('tr[data-prospect-id="' + prospects[0].id + '"]').replaceWith(html);
        }
        else {
            listCanvasBody.append(html);
        }

        listCanvasBody.find('tr').unbind('click').click(function () {
            var prospectId = $(this).attr('data-prospect-id');
            var prospect = currentProspects.filter(function (p) {
                return p.id === prospectId;
            })[0];
            showProspectInfo(prospect);
        });
    };

    var addressSort = function(a, b) {
        return sln.smartSort(a.address, b.address);
    };

    var loadProspects = function (appId, category, cursor) {
        if (!appId) {
            return;
        }
        if (cursor == null) {
            showProcessing('Loading prospects...');
            // Clear list view
            listCanvasBody.empty();
        }
        
        sln.call({
            url : '/internal/shop/rest/prospects/map',
            data : {
                app_id: appId,
                category: category,
                cursor: cursor
            },
            success : function(data) {
                if (cursor == null) {
                    regioManagersPerApp[appId] = data.regio_managers;
                    currentProspects = []
                }
                Array.prototype.push.apply(currentProspects, data.prospects);
                
                console.time('Population prospect list');
                addProspectsToList(data.prospects);
                console.timeEnd('Population prospect list');
                if (data.prospects.length == 0 && data.cursor == null) {
                    hideProcessing();
                    console.time('Population prospect map');
                    renderProspectMarkers();
                    console.timeEnd('Population prospect map');
                    resize();
                } else {
                    loadProspects(appId, category, data.cursor);
                }
            },
            error : function() {
                hideProcessing();
                showError("An error occurred while loading data. Please reload this window.");
            }
        });
    };

    var initView = function() {
        $('.prospects-view').each(function() {
            var $this = $(this);
            if ($this.attr('id') == viewMode + '-canvas') {
                $this.show();
            } else {
                $this.hide();
            }
        });

        if (viewMode == ViewModeType.MAP) {
            if (!map) {
                var mapOptions = {
                    zoom: 8,
                    // Brussels
                    center: new google.maps.LatLng(50.850922, 4.357622)
                };
                map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);
                oms = new OverlappingMarkerSpiderfier(map, {
                    keepSpiderfied: true
                });
                oms.addListener('click', function (marker, event) {
                    showProspectInfo(marker._prospect, false, function (modal) {
                        modal.data('marker', marker);
                    });
                });
            }
            renderProspectMarkers();
        }
        resize();
    };

    var initSearch = function() {
        $('#prospect-form').submit(function (e) {
            e.preventDefault();
        });
        var searchItemsArray = [], searchItems = {};

        function sortByName(a, b) {
            if (a.name < b.name) {
                return -1;
            }
            if (a.name > b.name) {
                return 1;
            }
            return 0;
        }

        function matchHighLighter(i, match) {
            return '<strong>' + match + '</strong>';
        }

        function getProspectIds(prospect) {
            return prospect.id;
        }

        var searchInput = $('#search-prospect-query').typeahead({
            minLength: 3,
            source: function (query, callback) {
                if (prospectTypeaheadTimeout) {
                    clearTimeout(prospectTypeaheadTimeout);
                }
                prospectTypeaheadTimeout = setTimeout(function () {
                    sln.call({
                        url: '/internal/shop/rest/prospects/search',
                        data: {query: query},
                        success: function (data) {
                            var tempSorted = data.sort(sortByName);
                            searchItemsArray = data;
                            for (var i = 0, len = data.length; i < len; i++) {
                                searchItems[data[i].id] = data[i];
                            }
                            var mapped = data.map(getProspectIds);
                            callback(mapped);
                        }
                    });
                }, 400);
            },
            sorter: function (ids) {
                return searchItemsArray.map(getProspectIds);
            },
            matcher : function(item) {
                return true;
            },
            highlighter: function (prospectId) {
                var item = searchItems[prospectId];
                var adjustFor = [StatusType.TODO, StatusType.ADDED_BY_DISCOVERY, StatusType.INVITED_TO_INTRODUCTION];
                var matchRegex = new RegExp('(' + this.query + ')', 'ig');
                var h = adjustFor.indexOf(item.status) !== -1 ? 20 : 30;
                var m = adjustFor.indexOf(item.status) !== -1 ? 0 : -4;
                var img = '<img src="' + getMarkerIcon(item.status) + '" style="margin-top:15px;float:left;height: ' + h
                    + 'px; margin-left: ' + m + 'px;" /> </div>';
                var highlightedName = '<div class="prospect-search-result-small">(Unnamed prospect)</div>';
                if (item.name) {
                    highlightedName = '<div class="prospect-search-result-name">' + item.name.replace(matchRegex, matchHighLighter) + '</div>';
                }
                var highLightedAddress = '<div class="prospect-search-result-small">(No address specified)</div>';
                if (item.address) {
                    highLightedAddress = '<div class="prospect-search-result-small">'
                        + item.address.replace(matchRegex, matchHighLighter)
                        + '</div>';
                }
                item.phone = item.phone ? item.phone : '';
                var highlightedMisc = '<div class="prospect-search-result-small">' + item.phone.replace(matchRegex, matchHighLighter);
                if (item.email) {
                    highlightedMisc += ', ' + item.email.replace(matchRegex, matchHighLighter);
                }
                highlightedMisc += '</div>';
                return img + highlightedName + highLightedAddress + highlightedMisc;
            },
            items : 20,
            updater: function (prospectId) {
                showProspectInfo(searchItems[prospectId]);
            }
        });
    };

    var channelUpdates = function(data) {
        if (data.type == 'shop.prospect.updated') {
            if (currentProspects[0] && data.prospect.app_id === currentProspects[0].app_id) {
                // update map view
                $.each(currentMarkers, function(i, marker) {
                    if (marker._prospect.id == data.prospect.id) {
                        mergeObject(marker._prospect, data.prospect);
                        var markerIcon = getMarkerIcon(data.prospect.status);
                        if (markerIcon) {
                            marker.setIcon(markerIcon);
                        }
                        marker.setVisible(FilteredStatusTypes.indexOf(data.prospect.status) != -1);
                        marker.setPosition(new google.maps.LatLng(data.prospect.lat, data.prospect.lon));
                        return false;
                    }
                });
                // update list view
                addProspectsToList([data.prospect], 'edit');
            }
        } else if (data.type == 'shop.prospect.created') {
            if (currentProspects[0] && data.prospect.app_id === currentProspects[0].app_id) {
                currentProspects.push(data.prospect);
                currentProspects.sort(addressSort);
                if (map) {
                    addProspectToMap(data.prospect);
                }
                addProspectsToList([data.prospect], 'update');
            }
        }
    };

    sln.registerMsgCallback(channelUpdates);

    initView();
    initSearch();

    function renderProspectMarkers() {
        if (map) {
            var choice = $('#prospects_app_id').find('option[value="' + appSelect.val() + '"]');
            var northEast = new google.maps.LatLng(parseFloat(choice.attr('ne_lat')), parseFloat(choice
                .attr('ne_lon')));
            var southWest = new google.maps.LatLng(parseFloat(choice.attr('sw_lat')), parseFloat(choice
                .attr('sw_lon')));
            var bounds = new google.maps.LatLngBounds(southWest, northEast);
            while (currentMarkers.length) {
                var marker = currentMarkers[0];
                marker.setMap(null);
                currentMarkers.splice(0, 1);
            }
            oms.clearMarkers();
            map.fitBounds(bounds);
            for (var i = 0, len = currentProspects.length; i < len; i++) {
                addProspectToMap(currentProspects[i]);
            }
        }
    }

    function exportCurrentProspects () {
        var $this = $(this);
        $this.attr('disabled', true).unbind('click');
        var prospectsIds = currentProspects.filter(isProspectVisible).map(function (p) {
            return p.id;
        });
        sln.call({
            url: '/internal/shop/rest/prospects/export',
            method: 'post',
            data: {
                prospect_ids: prospectsIds
            },
            success: function (data) {
                if (data.success === true) {
                    sln.alert('You will receive an email soon containing the exported prospects.');
                } else {
                    sln.alert(data.errormsg);
                }
            },
            complete: function () {
                $this.attr('disabled', false).click(exportCurrentProspects);
            }
        });
    }
});
