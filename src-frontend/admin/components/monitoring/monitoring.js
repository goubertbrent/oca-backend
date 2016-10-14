(function () {
    "use strict";
    angular.module('monitoring', ['ngMaterial', 'channel', 'ngResource', 'LocalStorageModule', 'toolbar', 'audioPlayer'])
        .config(['localStorageServiceProvider', function (localStorageServiceProvider) {
            localStorageServiceProvider.setPrefix('monitoring');
        }]);
})();