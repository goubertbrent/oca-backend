(function () {
    'use strict';
    angular.module('audioPlayer')
        .factory('audioPlayer', ['$http', '$log', audioPlayer]);

    function audioPlayer ($http, $log) {
        var audioContext;
        try {
            // Fix up for prefixing
            window.AudioContext = window.AudioContext || window.webkitAudioContext;
            audioContext = new AudioContext();
        }
        catch (e) {
            $log.warn('Web Audio API is not supported in this browser');
        }

        function play (url) {
            if (!audioContext) {
                $log.info('Could not play sound because no audioContext was found. AudioContext is probably not supported.', url);
                return;
            }
            $http.get(url, {responseType: 'arraybuffer'}).then(function (response) {
                audioContext.decodeAudioData(response.data, function (buffer) {
                    let source = audioContext.createBufferSource();
                    source.buffer = buffer;
                    source.connect(audioContext.destination);
                    source.start(0);
                }, function (err) {
                    $log.error('Failed to play sound', err);
                });
            }, function () {
                $log.warn('Failed to load sound');
            });
        }

        return {
            play: play
        };
    }
})();