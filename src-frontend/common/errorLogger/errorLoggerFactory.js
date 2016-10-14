(function () {
    "use strict";
    angular.module('errorLogger')
        .factory('$exceptionHandler', ['$log', '$window', '$injector', function ($log, $window, $injector) {
            var getSourceMappedStackTrace = function (exception) {
                var $q = $injector.get('$q'),
                    $http = $injector.get('$http'),
                    SMConsumer = window.sourceMap.SourceMapConsumer,
                    cache = {};

                // Retrieve a SourceMap object for a minified script URL
                // https://stackoverflow.com/a/25081693/2396593
                var getMapForScript = function (url) {
                    if (cache[url]) {
                        return cache[url];
                    } else {
                        var promise = $http.get(url).then(function (response) {
                            var m = response.data.match(/\/\/# sourceMappingURL=(.+\.map)/);
                            if (m) {
                                var path = url.match(/^(.+)\/[^/]+$/);
                                path = path && path[1];
                                return $http.get(path + '/' + m[1]).then(function (response) {
                                    return new SMConsumer(response.data);
                                });
                            } else {
                                return $q.reject();
                            }
                        });
                        cache[url] = promise;
                        return promise;
                    }
                };

                if (exception.stack) { // not all browsers support stack traces
                    return $q.all(exception.stack.split(/\n/).map(function (stackLine) {
                        var match = stackLine.match(/^(.+)(http.+):(\d+):(\d+)/);
                        if (match) {
                            var prefix = match[1], url = match[2], line = match[3], col = match[4];
                            return getMapForScript(url).then(function (map) {
                                var pos = map.originalPositionFor({
                                    line: parseInt(line, 10),
                                    column: parseInt(col, 10)
                                });
                                var mangledName = prefix.match(/\s*(at)?\s*(.*?)\s*(\(|@)/);
                                mangledName = (mangledName && mangledName[2]) || '';
                                return '    at ' + (pos.name ? pos.name : mangledName) + ' ' +
                                    $window.location.origin + pos.source + ':' + pos.line + ':' +
                                    pos.column;
                            }, function () {
                                return stackLine;
                            });
                        } else {
                            return $q.when(stackLine);
                        }
                    })).then(function (lines) {
                        return lines.join('\n');
                    });
                } else {
                    return $q.when('');
                }
            };

            $window.onerror = function handleGlobalError(message, fileName, lineNumber, columnNumber, error) {
                // If this browser does not pass-in the original error object, let's
                // create a new error object based on what we know.
                if (!error) {
                    error = new Error(message);
                    error.fileName = fileName;
                    error.lineNumber = lineNumber;
                    error.columnNumber = ( columnNumber || 0 );
                }
                handleException(error);
            };

            function handleException(exception, cause) {
                // default error handler (which shows inaccurate line numbers)
                //$log.error.apply($log, arguments);
                getSourceMappedStackTrace(exception).then(function (error) {
                    // TODO: log error to server
                    $log.error(error);
                    $log.warn('Logging to server not implemented yet');
                });
            }

            return function (exception, cause) {
                handleException(exception, cause);
            };
        }
        ]);
})();
