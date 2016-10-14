/**
 * Created by lucas on 3/2/16.
 */
(function () {
    'use strict';
    angular.module('monitoring')
        .constant('MonitoringConstants', {
            firstSounds: [
                {
                    filename: 'first_blood.wav',
                    text: 'First blood'
                }
            ],
            doubleSounds: [
                {
                    filename: 'double_kill.wav',
                    text: 'Double kill'
                }, {
                    filename: 'Dominating.wav',
                    text: 'Dominating'
                }, {
                    filename: 'Unstoppable.wav',
                    text: 'Unstoppable'
                }
            ],
            comboSounds: [
                {
                    filename: 'Combowhore.wav',
                    text: 'Combo whore'
                }, {
                    filename: 'Dominating.wav',
                    text: 'Dominating'
                }, {
                    filename: 'Unstoppable.wav',
                    text: 'Unstoppable'
                },
                {
                    filename: 'Hattrick.wav',
                    text: 'Hattrick'
                },
                {
                    filename: 'Killing_Spree.wav',
                    text: 'Killing spree'
                },
                {
                    filename: 'UltraKill.wav',
                    text: 'Ultra kill'
                },
                {
                    filename: 'LudicrousKill.wav',
                    text: 'Ultra kill'
                },
                {
                    filename: 'MonsterKill_F.wav',
                    text: 'Ultra kill'
                }
            ],
            miscSounds: [
                {
                    filename: 'WhickedSick.wav',
                    text: 'Whicked sick'
                }, {
                    filename: 'Rampage.wav',
                    text: 'Rampage'
                }, {
                    filename: 'godlike.wav',
                    text: 'Godlike'
                }, {
                    filename: 'Roadwarrior.wav',
                    text: 'Road warrior'
                }, {
                    filename: 'Unstoppable.wav',
                    text: 'Unstoppable'
                }
            ],
            lowAmountSounds: [
                {
                    filename: 'bottom_feeder.wav',
                    text: 'Bottom feeder'
                }, {
                    filename: 'Denied.wav',
                    text: 'Denied'
                }, {
                    filename: 'Humiliating_defeat.wav',
                    text: 'Humiliating defeat'
                }
            ],
            highAmountSounds: [
                {
                    filename: 'Flawless_victory.wav',
                    text: 'Flawless victory'
                }, {
                    filename: 'HolyShit_F.wav',
                    text: 'Holy shit'
                }, {
                    filename: 'Ownage.wav',
                    text: 'Ownage'
                }
            ]
        });
})();