/**
 * Created by lucas on 2/14/16.
 */
(function () {
    'use strict';
    angular.module('channel')
        .factory('Channel', [
            // Native angular modules
            '$rootScope', '$log', '$window', '$http', '$timeout',
            // Modules from libraries
            '$mdToast', '$mdDialog', '$translate',
            Channel
        ]);

    /**
     * Easy way to use the google channel API.
     * Shows a toast when the connection is lost, and retries 5 times before giving up. Shows a popup when that happens.
     * @returns {{registerCallback: registerCallback, removeCallback: removeCallback}}
     * @constructor
     */
    function Channel ($rootScope, $log, $window, $http, $timeout, $mdToast, $mdDialog, $translate) {
        var self = this,
            closing = false,
            callbacks = [],
            retries = 0,
            toast;

        function registerCallback (type, callback) {
            callbacks.push({type: type, callback: callback});
        }

        function removeCallback (callback) {
            var index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            } else {
                $log.debug('Cannot remove listener for callback: no listener found', callback);
            }
        }

        function runChannel (token) {
            var channel = new goog.appengine.Channel(token),
                socket = channel.open({
                    onopen: onOpen,
                    onmessage: onMessage,
                    onerror: onError,
                    onclose: onClose
                });
            $log.debug('Connected to channel');
        }

        $window.addEventListener('beforeunload', function () {
            closing = true;
        });
        function onOpen () {
            broadcast({type: 'rogerthat.system.channel_connected'});
        }

        function showChannelToast (permantentFailure) {
            if (toast && !permantentFailure) {
                return;
            }
            $translate(['lost-channel-connection-reconnecting', 'lost-channel-connection-permanently', 'reload', 'Close'])
                .then(translations => {
                    if (permantentFailure) {
                        toast = $mdToast.simple()
                            .textContent(translations['lost-channel-connection-permanently'])
                            .action(translations.reload);
                    }
                    else {
                        toast = $mdToast.simple()
                            .textContent(translations['lost-channel-connection-reconnecting'])
                            .action(translations.Close);
                    }
                    toast.highlightAction(true)
                        .hideDelay(0)
                        .position('top right');
                    $mdToast.show(toast).then(response => {
                        if (permantentFailure) {
                            $window.location.reload();
                        }
                    });
                });
        }

        function hideChannelToast () {
            if (toast) {
                $mdToast.hide(toast).then(function () {
                    toast = undefined;
                });
            }
        }

        function onMessage (message) {
            $rootScope.$apply(()=> {
                $log.info("Received channel update");
                if (message.data.indexOf("large_object=") === 0) {
                    // todo: verify if this works
                    $http({
                        method: 'GET',
                        url: self.largeObjectUrl,
                        data: {
                            key: message.data.substring(13)
                        }
                    })
                        .then(function (data) {
                            process(data);
                        })
                        .then(function (data) {
                            $log.error('Failed to retrieve large channel object', data);
                        });
                } else {
                    process(message.data);
                }
                function process (raw_data) {
                    var data = JSON.parse(raw_data);
                    $log.debug('Channel data:', data);
                    if (angular.isArray(data)) {
                        angular.forEach(data, function (messageData) {
                            broadcast(messageData);
                        });
                    } else {
                        broadcast(data);
                    }
                }
            });
        }

        function broadcast (data) {
            var callbackObjects = callbacks.filter(function (c) {
                return c.type === data.type;
            });
            angular.forEach(callbackObjects, function (callbackObject) {
                callbackObject.callback(data);
            });
        }

        function onError (data) {
            $log.error('Failed to open channel');
        }

        function getToken () {
            $http({
                method: 'GET',
                url: self.renewUrl
            }).then(response => {
                retries = 0;
                runChannel(JSON.parse(response.data));
                hideChannelToast();
            }, () => {
                retries += 1;
                if (retries <= 2) {
                    let seconds = Math.pow(2, retries);
                    showChannelToast();
                    $log.warn('Lost channel connection. Attempting to reconnect in ' + seconds + ' seconds...');
                    $timeout(getToken, seconds * 1000);
                } else {
                    showChannelToast(true);
                    $log.warn('Too many attempts to reconnect to channel. Giving up.');
                    $translate(['channel-disconnected-reload-browser', 'Warning', 'Close'])
                        .then(translations => {
                            $mdDialog.show(
                                $mdDialog.alert()
                                    .clickOutsideToClose(true)
                                    .title(translations.Warning)
                                    .textContent(translations['channel-disconnected-reload-browser'])
                                    .ok(translations.Close)
                            );
                        });
                }
            });
        }

        function onClose () {
            if (!closing) {
                getToken();
            }
        }

        function init (renewUrl, largeObjectUrl) {
            self.renewUrl = renewUrl || '/common/token';
            self.largeObjectUrl = largeObjectUrl || '/mobi/rest/channel';
            getToken();
        }


        return {
            init: init,
            registerCallback: registerCallback,
            removeCallback: removeCallback
        };
    }
})();