/**
 * Created by lucas on 2/27/16.
 */
(function () {
    'use strict';
    angular.module('monitoring')
        .factory('MonitoringResource', ['$resource', MonitoringResource]);
    function MonitoringResource($resource) {
        const BASE_URL = '/admin/rest/monitoring/';
        return $resource(BASE_URL, {}, {
            get: {
                method: 'GET',
                url: BASE_URL + 'get_status'
            },
            clear: {
                method: 'GET',
                url: BASE_URL + 'reset'
            }
        });
    }
})();