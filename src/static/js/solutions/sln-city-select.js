/*
 * Copyright 2018 Mobicage NV
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

var NotImplmentedError = new Error('not implmented');

function CitySelect(cityApps, appStats, selected, currency) {
    this.cityApps = cityApps;
    this.stats = appStats;
    this.selectedApps = selected;
    this.defaultAppReach = this.stats[ACTIVE_APPS[0]] || 0;
    this.currency = currency;
}


CitySelect.prototype = {
    getTooltip: function(city) {
        var appId = this.cityApps[city];
        if (appId) {
            var userCount = this.stats[appId];
            var estimatedReach = modules.news.getEstimatedReach(userCount);
            var costCount = appId === ACTIVE_APPS[0] ? 0 : userCount;
            var estimatedCost = modules.news.getEstimatedCost(costCount, this.currency);
            return '<b>' + city + '</b><br>' + CommonTranslations['broadcast-estimated-reach'] + ': ' + estimatedReach
                + ' ' + CommonTranslations['broadcast-out-of'] + ' ' + userCount + '<br>'
                + CommonTranslations['broadcast-estimated-cost'] + ' ' + estimatedCost;
        } else {
            return city;
        }
    },

    getEnabledApps: function() {
        var cities = this.data.cities;
        return Object.keys(this.cityApps).filter(function(city) {
            return cities[city] !== undefined;
        });
    },

    selectionChanged: function() {
    },

    onSelectionCompleted: function() {
    },

    selectClicked: function() {
    },

    onShown: function() {
        throw NotImplmentedError;
    },

    createModal: function() {
        throw NotImplmentedError;
    },

    setupModalHandlers: function() {
        this.modal.unbind('shown').on('shown', this.onShown.bind(this));
        $('button[action=submit]', this.modal).unbind().click(this.saveClicked.bind(this));
        $('button[action=select_all]', this.modal).unbind().click(this.selectAll.bind(this));
        $('button[action=deselect_all]', this.modal).unbind().click(this.deselectAll.bind(this));
    },

    show: function() {
        if (!this.modal) {
            this.createModal();
        }

        this.setupModalHandlers();
        this.modal.modal('show');
    },

    getSelectedApps: function() {
        throw NotImplmentedError;
    },

    getSelectedAppIds: function() {
        var self = this;
        return this.getSelectedApps().map(function(city) {
            return self.cityApps[city];
        });
    },

    saveClicked: function() {
        var selected = this.getSelectedApps();

        if (!selected.length) {
            sln.alert(CommonTranslations.news_target_audience_select_at_least_one_app);
            return;
        }

        this.selectionChanged(selected);
        this.onSelectionCompleted(selected);
        this.modal.modal('hide');
    },

    selectAll: function() {
        throw NotImplmentedError;
    },

    deselectAll: function() {
        throw NotImplmentedError;
    }
};


// with a map
function MapCitySelect(cityApps, appStats, selected, previewContainer, mapData, readonly, currency) {
    CitySelect.call(this, cityApps, appStats, selected);

    this.data = mapData;
    this.vectorMap = null;
    this.previewContainer = previewContainer;
    this.previewMap = null;
    this.defaultCity = ALL_APPS[0].name;
    this.readonly = readonly || false;
    this.currency = currency;

    this.renderPreview();
}

MapCitySelect.prototype = Object.create(CitySelect.prototype);
MapCitySelect.prototype.constructor = MapCitySelect;

MapCitySelect.prototype.renderPreview = function() {
    this.previewContainer.empty();
    this.previewContainer.append('<div class="map"></div>');

    var data = this.data;
    if (!this.previewMap) {
        this.previewMap = new VectorMap('minimap', data.cities, this.getEnabledApps(), this.previewContainer, {
            width: data.width,
            height: data.height,
            selectable: false,
            selected: this.getSelectedApps(),
            zoom: false,
            readonly: this.readonly,
        });
        this.configureDefaultCity(this.previewMap);
    }
    this.previewMap.render();
};
MapCitySelect.prototype.lockPreview = function() {
    this.previewContainer.css('pointer-events',  'none');
};
MapCitySelect.prototype.setOnSelectClicked = function(callback) {
    this.previewMap.areaClicked = callback;
};
MapCitySelect.prototype.setOnDefaultClicked = function(callback) {
    this.previewMap.defaultAreaClicked = callback;
};
MapCitySelect.prototype.selectionChanged = function(selected) {
    // update the preview
    this.previewMap.selected = selected;
    this.previewMap.render();
};
MapCitySelect.prototype.configureDefaultCity = function(map) {
    map.colors[this.defaultCity] = '#6a8acd';
    map.legend.values[this.defaultCity] = this.defaultCity;
    map.legend.texts[this.defaultCity] = CommonTranslations.city_select_default_city;
};

MapCitySelect.prototype.setTotalEstimatedReach = function () {
    var total = 0;
    var areas = this.vectorMap.selectedAreas();
    for (var _i = 0, areas_1 = areas; _i < areas_1.length; _i++) {
        var area = areas_1[_i];
        var appId = this.cityApps[area];
        if (appId) {
            total += this.stats[appId];
        }
    }
    $('#popup-total-reach').text(total);
    $('#popup-estimated-reach').text(modules.news.getEstimatedReach(total));
    $('#popup-estimated-cost').text(modules.news.getEstimatedCost(total - this.defaultAppReach, this.currency));
};

MapCitySelect.prototype.onShown = function() {
    var self = this;
    if (!this.vectorMap) {
        var cities = this.data.cities;
        var enabledApps = this.getEnabledApps();
        this.vectorMap = new VectorMap('cities', cities, enabledApps, this.container, {
            tooltip: this.getTooltip.bind(this),
            width: this.data.width,
            height: this.data.height,
            selectable: true,
            selected: this.selectedApps,
        });
        this.vectorMap.legend.enabled = true;
        this.vectorMap.legend.texts = {
            selected: CommonTranslations.city_select_selected,
            unselected: CommonTranslations.city_select_unselected,
            default: CommonTranslations.city_select_unsupported,
        };
        this.vectorMap.onAreaSelected(function () {
            self.setTotalEstimatedReach();
        });
        // default city
        this.configureDefaultCity(this.vectorMap);
    }
    this.vectorMap.render();
    // bootstrap-modal-fullscreen sets max-height
    var modalBody = this.container.parent();
    modalBody.css('min-height', modalBody.css('max-height'));
    setTimeout(function () {
        self.setTotalEstimatedReach();
    }, 500);
};
MapCitySelect.prototype.createModal = function() {
    var html = $.tmpl(templates.city_select, {
        mapEnabled: true,
        apps: this.cityApps,
        stats: this.stats,
        selected: this.selectedApps,
    });

    this.modal = sln.createModal(html);
    this.container = $('#map_container', this.modal);
};
MapCitySelect.prototype.getSelectedApps = function() {
    // returns app names (cities)
    if (this.vectorMap) {
        return this.vectorMap.selectedAreas();
    } else {
        return this.selectedApps;
    }
};
MapCitySelect.prototype.selectAll = function() {
    this.vectorMap.selectAll(true);
};
MapCitySelect.prototype.deselectAll = function() {
    this.vectorMap.selectAll(false);
};
MapCitySelect.prototype.setSelection = function(area, selection) {
    var map = this.vectorMap;
    if (map) {
        map.setSelection(area, selection);
    } else {
        var idx = this.selectedApps.indexOf(area);
        if (selection) {
            if (idx === -1) {
                this.selectedApps.push(area);
            }
        } else {
            if (idx !== -1) {
                this.selectedApps.splice(idx, 1);
            }
        }
    }

    var selected = this.getSelectedApps();
    this.selectionChanged(selected);
    this.onSelectionCompleted(selected);
};


// Just a check list
function ListCitySelect(cityApps, appStats, selected, previewContainer, currency) {
    CitySelect.call(this, cityApps, appStats, selected, currency);
    this.previewContainer = previewContainer;

    this.renderPreview();
}

ListCitySelect.prototype = Object.create(CitySelect.prototype);
ListCitySelect.prototype.constructor = ListCitySelect;

ListCitySelect.prototype.renderPreview = function() {
    var self = this;
    var apps = this.getSelectedApps().map(function(city) {
        return {
            app_id: self.cityApps[city],
            name: city
        };
    });
    var html = $.tmpl(templates['broadcast/news_app_check_list'], {
        apps: apps,
        stats: this.stats,
    });

    this.previewContainer.html(html);
};
ListCitySelect.prototype.lockPreview = function() {
    this.previewContainer.find('#select_city_apps').hide();
};
ListCitySelect.prototype.setOnSelectClicked = function(callback) {
    this.previewContainer.on('click', '#select_city_apps', callback);
};
ListCitySelect.prototype.setOnDefaultClicked = function(callback) {
};
ListCitySelect.prototype.selectionChanged = function(selected) {
    this.renderPreview();
};
ListCitySelect.prototype.onShown = function() {
    $('input[name=app]', this.modal).on('change', this.appCheckboxChanged.bind(this));
};
ListCitySelect.prototype.getSelectedApps = function() {
    return this.selectedApps;
};
ListCitySelect.prototype.createModal = function() {
    var html = $.tmpl(templates.city_select, {
        mapEnabled: false,
        apps: this.cityApps,
        stats: this.stats,
        selected: this.selectedApps,
    });

    this.modal = sln.createModal(html);
};
ListCitySelect.prototype.selectApp = function(app, selection) {
    var idx = this.selectedApps.indexOf(app);
    if (selection) {
        if (idx === -1) {
            this.selectedApps.push(app);
        }
    } else {
        if (idx !== -1) {
            this.selectedApps.splice(idx, 1);
        }
    }
};
ListCitySelect.prototype.appCheckboxChanged = function(event) {
    var elem = $(event.target);
    var city = elem.val();
    this.selectApp(city, elem.is(':checked'));
};
ListCitySelect.prototype.selectAll = function() {
    $('input[name=app]', this.modal).prop('checked', true);
};
ListCitySelect.prototype.deselectAll = function() {
    $('input[name=app]', this.modal).prop('checked', false);
};
ListCitySelect.prototype.setSelection = function(app, selection) {
    $('input[name=app][value=' + app + ']', this.modal).prop('checked', selection);
    this.selectApp(app, selection);
    var selected = this.getSelectedApps();
    this.selectionChanged(selected);
    this.onSelectionCompleted(selected);
};
