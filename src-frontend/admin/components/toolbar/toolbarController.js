(function () {
    "use strict";
    angular
        .module('leftSidebar')
        .controller('ToolbarController', [
            '$scope', '$mdSidenav', 'ToolbarActionsFactory',
            ToolbarController
        ]);

    function ToolbarController ($scope, $mdSidenav, ToolbarActionsFactory) {
        $scope.toggleLeft = buildToggler('left');
        $scope.actionsFactory = ToolbarActionsFactory;

        function buildToggler (navID) {
            return function () {
                $mdSidenav(navID).toggle();
            };
        }
    }
})();
