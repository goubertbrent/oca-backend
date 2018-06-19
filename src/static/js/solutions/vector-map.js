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

function VectorMap(name, data, enabledAreas, container, options) {
    this.name = name; // e.g. cities
    this.data = data; // all cities data
    this.enabledAreas = enabledAreas; // enabled areas
    this.container = container; // container element

    this.options = options;
    this.tooltip = options.tooltip;
    this.areaClicked = options.areaClicked;
    this.defaultAreaClicked = options.defaultAreaClicked;

    this.selectable = options.selectable || false;
    this.zoom = options.zoom || true;

    this.legend = options.legend || {
        enabled: false,
        values: {
            default: 'default',
            unselected: 'unselected',
            selected: 'selected',
        },
        texts: {
            default: 'default',
            unselected: 'unselected',
            selected: 'selected',
        },
    };
    this.colors = options.colors || {
        default: '#ffffff', /* default */
        selected: '#5bc4bF',
        unselected: '#f4f4e9',
        hover: '#a3e135',
        stroke: '#ced8d0',
        text: "#000000"
    };
    this.selected = options.selected || []; // selected areas
    this.readonly = options.readonly || false;

    this.addData(name, data);
}

VectorMap.prototype = {

    _areaSelected: function () {
    },
    onAreaSelected: function (f) {
        this._areaSelected = f;
    },

    addData: function (name, data) {
        var obj = {
            maps: {}
        };

        obj.maps[name] = {
            width: this.options.width || 600,
            height: this.options.height || 600,
            getCoords: this.options.getCoords || function(lat, lon) {
                return {x: 1, y: 1};
            },
            elems: data
        };

        $.extend(true, $.mapael, obj);
    },

    selectedAreas: function() {
        return this.selected;
    },

    isSelected: function(area) {
        return this.selected.indexOf(area) !== -1;
    },

    setSelection: function(area, selection) {
        // just like jquery-mapael event handlers example!
        var fillColor, value;

        if (selection) {
            fillColor = this.colors[area] || this.colors.selected;
            value = this.legend.values[area] || this.legend.values.selected;
            if (this.selected.indexOf(area) === -1) {
                this.selected.push(area);
            }
        } else {
            fillColor = this.colors.unselected;
            value = this.legend.values.unselected;
            if (this.selected.indexOf(area) !== -1) {
                this.selected.splice(this.selected.indexOf(area), 1);
            }
        }

        var newData = {
            areas: {}
        };

        newData.areas[area] = {
            value: value,
            attrs: {
                fill: fillColor
            }
        };

        this.container.trigger('update', [{
            mapOptions: newData
        }]);
        this._areaSelected(area, selection);
    },

    selectAll: function(selection) {
        for (var i in this.enabledAreas) {
            this.setSelection(this.enabledAreas[i], selection);
        }
    },

    prepareAreas: function() {
        var result = {};
        var self = this;

        Object.keys(self.data).forEach(function(area) {
            result[area] = {tooltip: {}};
            if (!self.readonly) {
                result[area].tooltip = {content: self.tooltip ? self.tooltip(area) : area};
            }

            if (self.enabledAreas.indexOf(area) !== -1) {
                var areaIsSelected = self.isSelected(area);
                var value, fillColor;

                if (areaIsSelected) {
                    value = self.legend.values[area] || self.legend.values.selected;
                    fillColor = self.colors[area] || self.colors.selected;
                } else {
                    value = self.legend.values.unselected;
                    fillColor = self.colors.unselected;
                }

                result[area].value = value;
                result[area].attrs = {
                    fill: fillColor,
                    cursor: 'pointer'
                };

                result[area].eventHandlers = {
                    click: function(e, id, mapElem, textElem, elemOptions) {
                        if (self.selectable) {
                            // toggle selection
                            self.setSelection(id, !self.isSelected(id));
                        }

                        if (self.areaClicked) {
                            self.areaClicked(id);
                        }
                    }
                };
            }
        });

        return result;
    },

    render: function() {
        var self = this;
        if (!self.container.is(':visible')) {
            // jquery-mapael is not happy with hidden containers
            return;
        }
        // grayed fill color for non-enabled areas
        var mapaelOptions = {
            map: {
                name: self.name,
                defaultArea: {
                    value: self.legend.values.default,
                    attrs: {
                        fill: self.colors.default,
                        stroke: self.colors.stroke,
                    },
                    attrsHover: {
                        animDuration: 0,
                        fill: self.readonly ? self.colors.unselected : self.colors.hover
                    },
                    text: {
                        attrs: {
                            cursor: "pointer",
                            "font-size": 10,
                            fill: self.colors.text
                        },
                        attrsHover: {
                            animDuration: 0
                        }
                    },
                    eventHandlers: {
                        click: function(e, id, mapElem, textElem, elemOptions) {
                            if(typeof self.defaultAreaClicked === 'function') {
                                self.defaultAreaClicked(id);
                            }
                        },
                    }
                },
            },
            areas: self.prepareAreas(),
        };

        if (self.zoom) {
            mapaelOptions.zoom = {
                enabled: true,
                step: 0.25,
                maxLevel: 20
            };
        }

        if (self.legend.enabled) {
            var slices = [];

            for (var value in self.legend.values) {
                if (self.legend.values.hasOwnProperty(value)) {
                    slices.push({
                        sliceValue: self.legend.values[value],
                        attrs: {
                            fill: self.colors[value]
                        },
                        label: self.legend.texts[value]
                    });
                }
            }
            mapaelOptions.legend = {
                area: {
                    title: '',
                    slices: slices,
                }
            };
        }
        self.container.mapael(mapaelOptions);
    },

    clear: function() {
        this.container.empty();
    }
};
