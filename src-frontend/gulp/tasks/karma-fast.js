var gutil = require('gulp-util');
var karma = require('karma').server;
var util = require('../util');
var ROOT = require('../const').ROOT;
var Server = require('karma').Server;
var args = util.args;
var karmaConfig = {
    logLevel: 'debug',
    singleRun: true,
    autoWatch: false,
    projectName: args.project,
    configFile: ROOT + '/config/karma.conf.js'
};


// NOTE: `karma-fast` does NOT pre-make a full build of JS and CSS

exports.task = function (done) {
    var errorCount = 0;

    if (args.browsers) {
        karmaConfig.browsers = args.browsers.trim().split(',');
    }
    // NOTE: `karma-fast` does NOT test Firefox by default.

    if (args.reporters) {
        karmaConfig.reporters = args.reporters.trim().split(',');
    }


    gutil.log('Running unit tests on minified source.');
    process.env.KARMA_TEST_COMPRESSED = true;
    karma = new Server(karmaConfig, captureError(clearEnv, clearEnv));
    karma.start();


    function clearEnv () {
        process.env.KARMA_TEST_COMPRESSED = undefined;
        if (errorCount > 0) {
            process.exit(errorCount);
        }
        done();
    }

    function captureError (next, done) {
        return function (exitCode) {
            if (exitCode !== 0) {
                gutil.log(gutil.colors.red("Karma exited with the following exit code: " + exitCode));
                errorCount++;
            }
            // Do not process next set of tests if current set had >0 errors.
            (errorCount > 0) && done() || next();
        };
    }
};
