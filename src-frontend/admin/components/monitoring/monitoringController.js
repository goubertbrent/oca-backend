(function () {
    "use strict";
    angular.module('monitoring')
        .controller('MonitoringController', ['$scope', '$interval', '$timeout', '$filter', '$sce', '$mdDialog',
            'localStorageService',
            'Channel', 'audioPlayer',
            'MonitoringResource', 'MonitoringConstants', 'ToolbarActionsFactory', 'audioPlayer',
            MonitoringController]);

    function MonitoringController ($scope, $interval, $timeout, $filter, $sce, $mdDialog, // angular internal services
                                   LocalStorage, Channel, audioPlayer,
                                   MonitoringResource, MonitoringConstants, ToolbarActionsFactory) {
        var self = this;
        self.noConnection = false;
        self.lastServerError = LocalStorage.get('lastServerError') || new Date();
        self.errorCounts = {};
        self.hasClientErrors = false;
        self.slowQueues = [];
        self.scoreboard = LocalStorage.get('scoreboard') || [];
        self.getSoundType = () => {
            var soundType = LocalStorage.get('UTSoundsEnabled');
            if (soundType === null || soundType === undefined) {
                soundType = true;
                LocalStorage.set('UTSoundsEnabled', soundType);
            }
            return soundType;
        };
        self.setSoundType = (type) => {
            self.UTSoundsEnabled = type;
            LocalStorage.set('UTSoundsEnabled', type);
        };


        self.UTSoundsEnabled = self.getSoundType();
        self.toggleUTSounds = () => {
            self.UTSoundsEnabled = !self.UTSoundsEnabled;
            LocalStorage.set('UTSoundsEnabled', self.UTSoundsEnabled);
        };
        var toolbarActions = [{
            icon: 'audiotrack',
            text: 'UT sounds',
            type: 'switch',
            value: self.UTSoundsEnabled,
            changed: self.setSoundType
        }];
        ToolbarActionsFactory.setActions(toolbarActions);
        self.showScoreDetail = (score, event) => {
            var time = $filter('date')(score.datetime, "EEEE d MMMM 'at' H:mm");
            var amount = $filter('currency')(score.amount, score.currency, 0);
            var text;
            if (score.manager) {
                text = 'On ' + time + ', ' + score.manager + ' signed a ' + amount + ' order at customer "' + score.customer + '".';
                var totalAmountForManager = 0;
                self.scoreboard.filter(s=> {
                    return s.manager === score.manager;
                }).map(s => {
                    totalAmountForManager += s.amount;
                });
                text += '<br />' + score.manager + ' has earned a total of ' + score.currency + totalAmountForManager + ' in the last seven days.';
            } else {
                text = 'On ' + time + ', ' + score.customer + ' placed a ' + score.currency + amount + ' order.';
            }
            $mdDialog.show(
                $mdDialog.alert()
                    .clickOutsideToClose(true)
                    .title('Score details')
                    .htmlContent($sce.trustAsHtml(text))
                    .ariaLabel('Who cares about this')
                    .ok('Close')
                    .targetEvent(event)
            );
        };
        self.orderSigned = data => {
            var text = '';
            self.playAppropriateSound(data.info);
            if (data.info.manager !== 'test') {
                self.updateScoreboard(data.info);
            }
            if (data.info.manager) {
                text = data.info.manager + ' has signed a ' + data.info.currency + ' ' + data.info.amount + ' order at ' + data.info.customer + '!';
            } else {
                text = data.info.customer + ' just placed a ' + data.info.currency + ' ' + data.info.amount + ' order!';
            }
            $mdDialog.show({
                controller: ['$mdDialog', '$scope', 'text', function ($mdDialog, $scope, text) {
                    $scope.text = text;
                    $scope.close = function () {
                        $mdDialog.cancel();
                    };
                }],
                autoWrap: false,
                parent: angular.element(document.body),
                templateUrl: '/static/admin/html/components/monitoring/newOrderDialog.html',
                locals: {
                    text: text
                },
                clickOutsideToClose: true,
                openFrom: '#scoreboard', // Doesn't work for some reason.
                closeTo: '#scoreboard'
            });
            $timeout($mdDialog.hide, 15 * 1000);
        };
        self.updateScoreboard = (data) => {
            var scoreboard = LocalStorage.get('scoreboard');

            if (!scoreboard) {
                scoreboard = [];
            }
            scoreboard.push({
                datetime: new Date().toISOString(),
                amount: data.amount,
                manager: data.manager,
                customer: data.customer,
                currency: data.currency
            });
            LocalStorage.set('scoreboard', scoreboard);
            self.scoreboard = scoreboard;
        };
        self.clearOldScores = () => {
            var scoreboard = LocalStorage.get('scoreboard');
            var lastWeek = new Date(new Date().getTime() - (24 * 3600 * 7 * 1000));
            if (scoreboard) {
                scoreboard = scoreboard.filter(score=> {
                    return new Date(score.datetime) > lastWeek;
                });
                LocalStorage.set('scoreboard', scoreboard);
            }
        };
        self.playAppropriateSound = score => {
            if (self.getSoundType() === false) {
                audioPlayer.play('/static/audio/careless_whisper.mp3');
                return;
            }

            function random (array) {
                return array[Math.floor(Math.random() * array.length)];
            }

            const now = new Date();
            var sound;
            var isFirstOfTheDay = !self.scoreboard.some(s=> {
                return now.getDate() === new Date(s.datetime).getDate();
            });
            if (isFirstOfTheDay) {
                // First order of the day
                sound = random(MonitoringConstants.firstSounds);
            } else {
                // Is it a low-amount order?
                if (score.amount < 150) {
                    sound = random(MonitoringConstants.lowAmountSounds);
                }
                // Is it a high-amount order?
                else if (score.amount > 1200) {
                    sound = random(MonitoringConstants.highAmountSounds);
                } else {

                    var lastOrders = self.scoreboard.sort((s1, s2)=> {
                        var d1 = new Date(s1.datetime);
                        var d2 = new Date(s2.datetime);
                        return d2 - d1;
                    });
                    // Was the previous order also from this manager?
                    if (lastOrders[0].manager === score.manager) {
                        if (lastOrders[1].manager === score.manager) {
                            // Third or more consecutive order also from this manager?
                            sound = random(MonitoringConstants.comboSounds);
                        } else {
                            sound = random(MonitoringConstants.doubleSounds);
                        }
                    }
                    else {
                        sound = random(MonitoringConstants.miscSounds);
                    }
                }
            }
            audioPlayer.play('/static/audio/scorestreaks/' + sound.filename);
            return sound.text;
        };
        self.refresh = () => {
            MonitoringResource.get(status => {
                    self.noConnection = false;
                    self.status = status;
                    var now = new Date();
                    if (self.status.error_count !== 0 && self.status.error_count !== LocalStorage.get('lastServerErrorCount')) {
                        LocalStorage.set('lastServerErrorCount', self.status.error_count);
                        LocalStorage.set('lastServerError', now);
                        self.lastServerError = now;
                    }
                    self.slowQueues = [];
                    angular.forEach(self.status.queues, (queue)=> {
                        if (queue.oldest_eta_usec && queue.oldest_eta_used < self.status.five_min_ago) {
                            self.slowQueues.push(queue);
                        }
                    });
                    var uniqueErrors = {};
                    angular.forEach(self.status.client_errors, error => {
                        if (uniqueErrors[error.parent_id]) {
                            uniqueErrors[error.parent_id].count += error.count;
                        } else {
                            uniqueErrors[error.parent_id] = error;
                        }
                    });
                    var allErrors = LocalStorage.get('client_errors');
                    for (var error in uniqueErrors) {
                        if (uniqueErrors.hasOwnProperty(error)) {
                            if (!allErrors) {
                                allErrors = {};
                            }
                            if (allErrors[error]) {
                                allErrors[error].lastOccurence = now;
                            } else {
                                allErrors[error] = uniqueErrors[error];
                                allErrors[error].lastOccurence = now;
                            }
                        }
                    }
                    LocalStorage.set('client_errors', allErrors);
                    self.errorCounts = {};
                    self.hasClientErrors = false;
                    for (error in allErrors) {
                        if (allErrors.hasOwnProperty(error)) {
                            var e = allErrors[error];
                            if (!self.errorCounts[e.platform]) {
                                self.errorCounts[e.platform] = 0;
                            }
                            if (!e.deleted) {
                                // We are not interested in how much this specific error occurred here, so +1 instead of e.count
                                self.errorCounts[e.platform] += 1;
                                self.hasClientErrors = true;
                            }
                        }
                    }
                }, ()=> {
                    self.noConnection = true;
                }
            );
        };
        self.clearAllErrors = (fromChannel) => {
            // Clear server errors.
            if (!fromChannel) {
                MonitoringResource.clear();
            }
            self.status.error_count = 0;
            // Clear client errors.
            self.hasClientErrors = false;
            var errors = LocalStorage.get('client_errors');
            for (var error in errors) {
                if (errors.hasOwnProperty(error)) {
                    errors[error].deleted = true;
                }
            }
            LocalStorage.set('client_errors', errors);
            for (var platform in self.errorCounts) {
                if (self.errorCounts.hasOwnProperty(platform)) {
                    self.errorCounts[platform] = 0;
                }
            }
        };
        self.clearOldErrors = () => {
            // Mark errors as 'deleted' after they have been there for a day (so we can still filter them out)
            // Delete the errors for good after a week as we assume they will have been replaced by new ones.
            var errors = LocalStorage.get('client_errors');
            var yesterday = new Date(new Date().getTime() - (24 * 3600 * 1000));
            var lastWeek = new Date(new Date().getTime() - (24 * 3600 * 7 * 1000));
            angular.forEach(errors, (error) => {
                var lastOccurence = new Date(error.lastOccurence);
                if (lastOccurence < lastWeek) {
                    delete errors[error];
                }
                else if (lastOccurence < yesterday) {
                    errors[error].deleted = true;
                }
            });
        };
        // Refresh status every minute.
        Channel.registerCallback('shop.monitoring.signed_order', self.orderSigned);
        Channel.registerCallback('shop.monitoring.reset', self.clearAllErrors);
        Channel.registerCallback('shop.monitoring.playsound', function (data) {
            audioPlayer.play('/static/audio/scorestreaks/' + data.sound);
        });
        $interval(self.refresh, 1000 * 60);
        $interval(self.clearOldScores, 1000 * 3600 * 4);
        $interval(self.clearOldErrors, 1000 * 3600);
        self.refresh();
    }
})();