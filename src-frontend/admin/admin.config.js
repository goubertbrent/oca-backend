(function () {
    'use strict';
    var app = angular
        .module('app', [
            // Third party dependencies
            'ngAnimate', 'ngRoute', 'ngSanitize', 'ui.router', 'ngMaterial', 'pascalprecht.translate',
            // 'business' logic / constants
            'errorLogger', 'channel',
            // Components/views
            'leftSidebar', 'toolbar', 'monitoring'
        ])
        .config(['$mdThemingProvider', ThemingConfig])
        .config(['$translateProvider', TranslateConfig])
        .config(['$urlRouterProvider', '$locationProvider', StateConfig])
        .run(['$rootScope', '$state', '$stateParams', 'Channel', 'ToolbarActionsFactory', Run]);

    function ThemingConfig ($mdThemingProvider) {
        $mdThemingProvider.theme('default')
            .primaryPalette('green')
            .accentPalette('light-green');
    }

    function TranslateConfig ($translateProvider) {
        // We don't really need translations in this project, we just use this so we can recycle the 'channel' module
        var translations = {
            'channel-disconnected-reload-browser': 'Could not renew auto updating channel automatically. Please reload the page to resolve this problem.',
            'lost-channel-connection-reconnecting': 'Lost connection. Attempting to reconnect..',
            'lost-channel-connection-permanently': 'Lost connection. Please reload the page.',
            'Warning': 'Warning',
            'Close': 'Close'
        };
        $translateProvider.translations('en', translations);
        $translateProvider.useSanitizeValueStrategy('escape');
        $translateProvider.useMissingTranslationHandlerLog();
        $translateProvider.use('en');
    }

    function StateConfig ($urlRouterProvider, $locationProvider) {
        $locationProvider.html5Mode({
            enabled: true,
            requireBase: true
        });
        // Default route
        $urlRouterProvider.otherwise('/monitoring');
    }

    function Run ($rootScope, $state, $stateParams, Channel, ToolbarActionsFactory) {
        Channel.init('/internal/token', '/internal/channel/large_object');
        $rootScope.$on('$stateChangeSuccess', function () {
            ToolbarActionsFactory.clearActions();
            $rootScope.currentModule = $state.current.name.split('.')[0];
        });
        $rootScope.$state = $state;
        $rootScope.$stateParams = $stateParams;
    }
})();