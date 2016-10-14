'use strict';
require('babel-polyfill');
var gulp = require('gulp'),
    jshint = require('gulp-jshint'),
    notify = require('gulp-notify'),
    uglify = require('gulp-uglify'),
    rename = require('gulp-rename'),
    concat = require('gulp-concat'),
    sourcemaps = require('gulp-sourcemaps'),
    babel = require('gulp-babel'),
    inject = require('gulp-inject'),
    livereload = require('gulp-livereload'),
    angularFilesort = require('gulp-angular-filesort'),
    config = require('../config');

// Scripts
exports.task = function () {
    return gulp.src(config.jsFiles)
        .pipe(sourcemaps.init())
        .pipe(babel({
            //presets: ['es2015']
            presets: ['es2015-without-strict']
        }))
        .pipe(jshint())
        .pipe(jshint.reporter('default'))
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
        }))
        .pipe(angularFilesort())
        .pipe(concat(config.projectName + '.js'))
        .pipe(gulp.dest(config.destFolder + '/js'))
        .pipe(rename({suffix: '.min'}))
        .pipe(uglify())
        .pipe(sourcemaps.write('.'))
        .pipe(gulp.dest(config.destFolder + '/js'))
        .pipe(livereload());
};