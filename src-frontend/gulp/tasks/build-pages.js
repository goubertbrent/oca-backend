'use strict';
var gulp = require('gulp'),
    livereload = require('gulp-livereload'),
    htmlMin = require('gulp-htmlmin'),
    config = require('../config');

// Pages
exports.task = function () {
    return gulp.src(config.projectName + '/**/*.html')
        .pipe(htmlMin(config.htmlMinOptions))
        .pipe(gulp.dest(config.destFolder + '/html'))
        .pipe(livereload());
};
