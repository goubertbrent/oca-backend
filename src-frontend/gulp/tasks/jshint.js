var config = require('../config'),
    gulp = require('gulp'),
    notify = require('gulp-notify'),
    jshint = require('gulp-jshint');

exports.task = function () {
    return gulp.src(config.jsFiles)
        .pipe(jshint('.jshintrc'))
        //.pipe(jshint.reporter('fail'))
        .pipe(notify(function (file) {
            if (file.jshint.success) {
                // Don't show something if success
                return false;
            }
            var errors = file.jshint.results.map(function (data) {
                if (data.error) {
                    return "(" + data.error.line + ':' + data.error.character + ') ' + data.error.reason;
                }
            }).join("\n");
            return file.relative + " (" + file.jshint.results.length + " errors)\n" + errors;
        }));
};
