(function () {
    "use strict";
    /**
     * @ngdoc controller
     * @name constants:ModuleConstants
     *
     * @description Contains the constants which define all the pages that are visitable.
     *
     *
     * @requires $scope
     * */
    angular.module('constants')
        .constant('ModuleConstants', {
            monitoring: {
                state: 'monitoring',
                pageName: 'Monitoring',
                icon: 'show_chart',
                sortOrder: 1
            }
        });
})();
