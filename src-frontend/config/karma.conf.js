module.exports = function (config) {
    var root = '../src/static/';
    var UNCOMPILED_SRC = [
        root + config.projectName + '/js/' + config.projectName + '.js',

        config.projectName + '/**/*.spec.js'
    ];

    var COMPILED_SRC = [
        root + config.projectName + '/css/' + config.projectName + '.min.css',
        root + config.projectName + '/js/' + config.projectName + '.min.js',

        config.projectName + '/**/*.spec.js'
    ];

    var dependencies = [
        root + 'libs/angular/angular.js',
        root + 'libs/angular-translate/angular-translate.min.js',
        root + 'libs/angular-translate-loader-url/angular-translate-loader-url.min.js',
        root + 'libs/angular-translate-handler-log/angular-translate-handler-log.min.js',
        root + 'libs/angular-ui-router/release/angular-ui-router.min.js',
        root + 'libs/angular-resource/angular-resource.js',
        root + 'libs/angular-route/angular-route.js',
        root + 'libs/angular-animate/angular-animate.js',
        root + 'libs/angular-aria/angular-aria.js',
        root + 'libs/angular-sanitize/angular-sanitize.js',
        root + 'libs/angular-touch/angular-touch.js',
        root + 'libs/angular-mocks/angular-mocks.js',
        root + 'libs/angular-material/angular-material.js'
    ];
    var testSrc = process.env.KARMA_TEST_COMPRESSED ? COMPILED_SRC : UNCOMPILED_SRC;
    config.set({

        basePath: __dirname + '/..',
        frameworks: ['jasmine'],
        files: dependencies.concat(testSrc),

        browserDisconnectTimeout: 500,

        logLevel: config.LOG_DEBUG,
        port: 9876,
        reporters: ['progress'],
        colors: true,
        // Continuous Integration mode
        // enable / disable watching file and executing tests whenever any file changes
        singleRun: true,
        autoWatch: false,

        // Only launch one browser at a time since doing multiple can cause disconnects/issues
        concurrency: 1,

        // Start these browsers, currently available:
        // - Chrome
        // - ChromeCanary
        // - Firefox
        // - Opera (has to be installed with `npm install karma-opera-launcher`)
        // - Safari (only Mac; has to be installed with `npm install karma-safari-launcher`)
        // - PhantomJS2
        // - IE (only Windows; has to be installed with `npm install karma-ie-launcher`)
        browsers: [/*'Chrome', */'PhantomJS2']
    });

};
