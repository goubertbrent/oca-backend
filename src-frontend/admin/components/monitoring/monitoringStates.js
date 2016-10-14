(function () {
    "use strict";
    angular.module('monitoring')
        .config(['$stateProvider', States]);

    function States($stateProvider) {
        $stateProvider
            .state('monitoring', {
                url: '/monitoring',
                templateUrl: '/static/admin/html/components/monitoring/monitoring.html',
                data: {
                    pageTitle: 'Monitoring'
                }
            });
    }
})();