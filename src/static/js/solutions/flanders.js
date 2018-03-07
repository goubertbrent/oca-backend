$.getJSON('/unauthenticated/osa/apps/flanders').done(function (apps) {
    $.getJSON('/static/js/shop/libraries/flanders.json').done(function (maps) {
        createMap(apps, maps);
    });
});

function createMap(apps, data) {
    $.extend(true, $.mapael,
        {
            maps: {
                cities: {
                    width: 1024,
                    height: 401.680185916,
                    getCoords: function (lat, lon) {
                        // Convert latitude,longitude to x,y here
                        return {x: 1, y: 1};
                    },
                    elems: data.cities
                },
                provinces: {
                    width: 1024,
                    height: 401.680185916,
                    getCoords: function (lat, lon) {
                        // Convert latitude,longitude to x,y here
                        return {x: 1, y: 1};
                    },
                    elems: data.provinces
                }
            }
        }
    );

    // These are the apps in which we currently are active - show them in a different colour on the map
    // key: city name, value: options
    var areas = apps.reduce(function (result, value) {
        result[value.name] = {
            attrs: {
                fill: '#5bc4bf',
                stroke: '#fff',
                cursor: 'pointer',
            },
            href: '/install/' + value.app_id,
            target: '_blank',
            tooltip: {content: value.name}
        };
        return result;
    }, {});
    for (var appName in data.cities) {
        if (data.cities.hasOwnProperty(appName) && !(appName in areas)) {
            areas[appName] = {
                tooltip: {content: appName}
            };
        }
    }

    $('#flanders').mapael({
        map: {
            name: 'cities',
            defaultArea: {
                attrs: {
                    fill: '#f4f4e8',
                    stroke: "#ced8d0"
                },
                attrsHover: {
                    animDuration: 0,
                    fill: "#a4e100"
                },
                text: {
                    attrs: {
                        cursor: "pointer",
                        "font-size": 10,
                        fill: "#000"
                    },
                    attrsHover: {
                        animDuration: 0
                    }
                }
            },
        },
        areas: areas
    });
}
