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

var map;

$(function() {
    var MAX_GRID_POINTS_COUNT = 10000;

    var currentRectangle = null;
    var currentCircles = [];
    var currentRadius = null;
    var searchAreaRectangles = [];
    var actions = {};

    var resize = function() {
        var margins = parseInt($('body').css('padding')) + parseInt($('body').css('margin'));
        var h = window.innerHeight - $('#map-canvas').position().top - margins;
        h = Math.max(400, Math.min(h, $('body').width() - 500 - margins));
        $('#map-canvas').css('height', h + 'px').css('width', h + 'px');
    };
    window.onresize = resize;
    resize();
    $('#map-options form p').css('width', '500px');

    var mapOptions = {
        zoom : 8,
        // Brussels
        center : new google.maps.LatLng(50.850922, 4.357622)
    };
    map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);

    $('#prospects_app_id').change(function() {
        if (!actions.searched) {
            $('#prospects_search_input').val($('#prospects_app_id option:selected').attr('app_name'));
        }

        while (searchAreaRectangles.length) {
            searchAreaRectangles[0].setMap(null);
            searchAreaRectangles.splice(0, 1);
        }

        var appId = $('#prospects_app_id').val();
        if (!appId) {
            return;
        }

        sln.call({
            url : '/internal/shop/rest/prospects/shop_app',
            type : 'GET',
            data : {
                app_id : appId
            },
            success : function(data) {
                if (data) {
                    showAppOnMap(data);
                    if (data.postal_codes) {
                        $('#prospects_postal_codes').val(data.postal_codes.join(', '));
                    }
                }
            },
            error : function() {
                showError('Failed to show the search history of ' + appId + ' on the map');
            }
        });
    });

    $('#prospects_radius').change(function() {
        currentRadius = parseInt($(this).val());
    }).change();

    $('#prospects_search_btn').click(function() {
        var city = $('#prospects_search_input').val();
        var country = $('#prospects_search_country').val();

        if (!city) {
            showError('City is required');
            return;
        }

        if (!country) {
            showError('Country is required');
            return;
        }

        if (currentRectangle) {
            currentRectangle.setMap(null);
            currentRectangle = null;
            actions.rectangleUpdated = false;
        }

        while (currentCircles.length) {
            currentCircles[0].setMap(null);
            currentCircles.splice(0, 1);
        }

        $('#map-options .submit-btn, #map-options .verify-btn').addClass('disabled').removeClass('btn-primary');

        showProcessing('Processing...');
        sln.call({
            url : '/internal/shop/rest/prospects/find_city_bounds',
            type : 'POST',
            data : {
                data : JSON.stringify({
                    country : country,
                    city : city
                })
            },
            success : function(data) {
                hideProcessing();
                if (data.success) {
                    actions.searched = true;

                    var bounds = createBounds(data.bounds);
                    currentRectangle = new google.maps.Rectangle({
                        bounds : bounds,
                        editable : true,
                        draggable : true,
                        strokeColor : '#8DB39C',
                        fillColor : '#8DB39C',
                        map : map
                    });

                    google.maps.event.addListener(currentRectangle, 'bounds_changed', currentRectangleUpdated);
                    google.maps.event.addListener(currentRectangle, 'dragend', currentRectangleUpdated);

                    $('#map-options .verify-btn').removeClass('disabled').addClass('btn-primary');
                    map.fitBounds(bounds);

                } else {
                    showError(data.errormsg);
                }
            },
            error : function() {
                hideProcessing();
                showError('An unknown error occurred. Check with the administrators.');
            }
        });
    });

    $('#save-postal-codes').click(function () {
        var postal_codes = $('#prospects_postal_codes').val().replace(/\s/g, '').split(',');
        var app_id = $('#prospects_app_id').val();
        if (!app_id) {
            sln.alert('Please select an app first');
            return;
        }
        sln.call({
            url: '/internal/shop/rest/shopapp/save_postal_codes',
            method: 'POST',
            data: {
                data: JSON.stringify({
                    app_id: app_id,
                    postal_codes: postal_codes
                })
            },
            success: function (data) {
                sln.alert(data.errormsg ? data.errormsg : 'Saved postal codes');
            },
            error: function () {
                sln.alert('Could not save postal codes');
            }
        });
    });

    $('#map-options').find('.verify-btn').click(function () {
        var southWest = currentRectangle.getBounds().getSouthWest();
        var northEast = currentRectangle.getBounds().getNorthEast();
        var data = {
            sw_lat : southWest.lat(),
            sw_lon : southWest.lng(),
            ne_lat : northEast.lat(),
            ne_lon : northEast.lng(),
            radius : currentRadius
        };
        console.log(data);

        while (currentCircles.length) {
            currentCircles[0].setMap(null);
            currentCircles.splice(0, 1);
        }

        var pointCountControlGroup = $('#prospects_point_count_error').parents('.control-group');
        var radiusControlGroup = $('#prospects_radius').parents('.control-group');

        $('#prospects_point_count_error').hide();
        pointCountControlGroup.removeClass('error');
        radiusControlGroup.removeClass('error');

        $('#prospects_point_count').val('');

        showProcessing('Calculating grid...');
        sln.call({
            url : '/internal/shop/rest/prospects/grid',
            type : 'GET',
            data : data,
            success : function(data) {
                hideProcessing();

                $('#prospects_point_count').val(data.length);

                if (MAX_GRID_POINTS_COUNT < data.length) {
                    $('#prospects_point_count_error').show();
                    pointCountControlGroup.addClass('error');
                    radiusControlGroup.addClass('error');
                } else {
                    $.each(data, function(i, pointTO) {
                        var circle = new google.maps.Circle({
                            map : map,
                            center : new google.maps.LatLng(pointTO.lat, pointTO.lon),
                            radius : currentRadius,
                            zIndex : -998
                        });
                        currentCircles.push(circle);
                    });

                    currentRectangle.setEditable(false);
                    currentRectangle.setDraggable(false);
                    $('#map-options .submit-btn').removeClass('disabled').addClass('btn-primary');
                }
            },
            error : function() {
                hideProcessing();
                showError('An unknown error occurred. Check with the administrators.');
            }
        });
    });

    $('#map-options .submit-btn').click(function() {
        var city = $('#prospects_search_input').val(),
            checkPhoneNumber = $('#prospects_check_phone_number').prop('checked');
        if ($(this).hasClass('disabled')) {
            return;
        }

        if (!currentRectangle || !(actions.searched || actions.rectangleUpdated)) {
            showError('You forgot to make a selection on the map');
            return;
        }

        var appId = $('#prospects_app_id').val();
        if (!appId) {
            showError('You forgot to select an app');
            return;
        }

        var postalCodes = $('#prospects_postal_codes').val();
        if (!postalCodes) {
            showError('You forgot to enter a postal code');
            return;
        }
        if (!city) {
            showError('Please fill in the "City" field.');
            return;
        }

        var bounds = currentRectangle.getBounds();
        var data = {
            sw_lat : bounds.getSouthWest().lat(),
            sw_lon : bounds.getSouthWest().lng(),
            ne_lat : bounds.getNorthEast().lat(),
            ne_lon : bounds.getNorthEast().lng(),
            app_id : appId,
            postal_codes : postalCodes,
            radius: currentRadius,
            city_name: city,
            check_phone_number: checkPhoneNumber
        };
        console.log(data);

        showProcessing('Processing...');
        sln.call({
            url : '/internal/shop/rest/prospects/find',
            type : 'POST',
            data : {
                data : JSON.stringify(data)
            },
            success : function(data) {
                hideProcessing();
                if (data.success) {
                    var city = $("#prospects_app_id option:selected").attr('app_name');
                    showAlert('Successfully started a job to find the prospects in ' + city + '.', function() {
                        clearForm();
                    }, 'Success');
                } else {
                    showError(data.errormsg);
                }
            },
            error : function() {
                hideProcessing();
                showError('An unknown error occurred. Check with the administrators.');
            }
        });
    });

    var clearForm = function() {
        $('#prospects_app_id').val('');
        $('#prospects_postal_codes').val('');
        $('#prospects_search_country').val('BE');
        $('#prospects_search_input').val('');
        $.each(actions, function(k, v) {
            actions[k] = false;
        });
    };

    var createBounds = function(boundsTO) {
        var southWest = new google.maps.LatLng(boundsTO.south_west.lat, boundsTO.south_west.lon);
        var northEast = new google.maps.LatLng(boundsTO.north_east.lat, boundsTO.north_east.lon);
        return new google.maps.LatLngBounds(southWest, northEast);
    };

    var currentRectangleUpdated = function() {
        actions.rectangleUpdated = true;
        map.fitBounds(currentRectangle.getBounds());
    };

    var showAppOnMap = function(shopApp) {
        if(shopApp.bounds) {
            map.fitBounds(createBounds(shopApp.bounds));
        }

        $.each(shopApp.searched_bounds, function(i, boundsTO) {
            searchAreaRectangles.push(new google.maps.Rectangle({
                bounds : createBounds(boundsTO),
                editable : false,
                draggable : false,
                strokeColor : 'white',
                fillColor : 'white',
                zIndex : -999,
                map : map
            }));
        });
    };

});
