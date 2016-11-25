var gulp = require('gulp'),
    watch = require('gulp-watch'),
    shell = require('shelljs'),
    fs = require("fs"),
    _ = require('lodash'),
    del = require('del');

gulp.task('default', function () {
    // XXX: use gulp instead of python to manage file changes/building to reduce overhead
    var version = fs.readFileSync('BACKEND_VERSION', 'utf-8');
    del.sync('build');
    shell.exec('cd ../rogerthat-backend && git pull && git checkout ' + version, function (exitCode, stdOut, stdErr) {
        if (exitCode !== 0) {
            throw Error(stdErr);
        }
        rebuild();
        var debounced = _.debounce(rebuild, 2000, {'leading': true, 'maxwait': 2000});
        watch(['src/**/*', '../rogerthat-backend/src/**/*', '!*.pyc'], function (events, done) {
            debounced();
        });

        function rebuild() {
            shell.exec('python build.py');
        }

    });
});
