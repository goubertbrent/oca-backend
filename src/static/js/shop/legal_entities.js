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
"use strict";
var legalEntities = [],
    CURRENCIES_SORTED = getSortedCurrencies();

function getSortedCurrencies() {
    var keys = Object.keys(CURRENCIES).sort();
    var sorted = [];
    for (var i = 0; i < keys.length; i++) {
        if (CURRENCIES.hasOwnProperty(keys[i])) {
            sorted.push({
                symbol: keys[i],
                name: CURRENCIES[keys[i]]
            });
        }
    }
    return sorted;
}

function _getLegalEntity(entityId, callback) {
    if (typeof entityId === 'string') {
        entityId = parseInt(entityId);
    }
    getLegalEntities(function (entities) {
        var entity = entities.filter(function (e) {
            return e.id === entityId;
        })[0];
        callback(entity);
    });
}

function getLegalEntities(callback) {
    if (legalEntities.length) {
        callback(legalEntities);
    } else {
        sln.call({
            url: '/internal/shop/rest/legal_entity/list',
            success: function (data) {
                legalEntities = data;
                callback(legalEntities);
            }
        });
    }
}

function updateEntity(entityId, updatedEntity, callback) {
    _getLegalEntity(entityId, function (entity) {
        for (var key in updatedEntity) {
            if (updatedEntity.hasOwnProperty(key)) {
                entity[key] = updatedEntity[key];
            }
        }
        if (callback) {
            callback();
        }
    });
}

function renderListLegalEntities() {
    getLegalEntities(function (data) {
        var page = $.tmpl(JS_TEMPLATES['legal_entity_table']);
        $('#legal_entities_content').html(page);
        var pageContent = $.tmpl(JS_TEMPLATES['legal_entity_row'], {
            legalEntities: data,
            COUNTRIES: COUNTRIES
        });
        $('#legal_entities_body').html(pageContent)
            .find('tr').click(onLegalEntityClick);
    });
}

function renderPutLegalEntity(entityId) {
    _getLegalEntity(entityId, function (entity) {
        var page = $.tmpl(JS_TEMPLATES.legal_entity_put, {
            entity: entity || {},
            COUNTRIES: COUNTRIES,
            CURRENCIES: CURRENCIES_SORTED,
            TERMS_OF_USE: TERMS_OF_USE
        });
        $('#legal_entities_content').html(page);
        $('#mobicage_terms_of_use').change(termsOfUseLanguageChanged).change();
        $('#submit_legal_entity').click(function () {
            var values = {};
            $('[name^="entity_"]').map(function (i, inputField) {
                values[inputField.name.replace('entity_', '')] = inputField.value;
            });
            values.vat_percent = parseInt(values.vat_percent);
            if (entity) {
                values.id = entity.id;
            }
            putLegalEntity(values);
        });
    });
}

function termsOfUseLanguageChanged() {
    var lang = $(this).val() || 'en';
    $('#mobicage_terms_of_use_translated').text(TERMS_OF_USE[lang]);
}

function onLegalEntityClick() {
    window.location.hash = '#/legal_entities/update/' + $(this).attr('id');
}

function putLegalEntity(values) {
    sln.call({
        url: '/internal/shop/rest/legal_entity/put',
        method: 'post',
        data: {
            data: JSON.stringify({entity: values})
        },
        success: function (data) {
            if (data.success !== true) {
                sln.alert(data.errormsg, null, 'Error');
            } else {
                if (!values.id) {
                    legalEntities.push(data.entity);
                    window.location.hash = '#/legal_entities';
                } else {
                    updateEntity(values.id, data.entity, function () {
                        window.location.hash = '#/legal_entities';
                    });
                }
            }
        }
    });
}
