(function () {
    "use strict";
    angular
        .module('leftSidebar')
        .controller('LeftSidebarController', [
            '$scope', '$mdSidenav', 'ModuleConstants',
            LeftSidebarController
        ]);

    function LeftSidebarController($scope, $mdSidenav, ModuleConstants) {
        var self = this,
            modules = Object.keys(ModuleConstants);
        $scope.toggle = function () {
            $mdSidenav('left').toggle();
        };
        $scope.close = function () {
            $mdSidenav('left').close();
        };

        self.modules = modules.map(m=>{
            ModuleConstants[m].name = m;
            return ModuleConstants[m];
        });
    }
})();