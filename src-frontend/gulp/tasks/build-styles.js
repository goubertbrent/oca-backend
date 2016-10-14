'use strict';
var gulp = require('gulp'),
    stylus = require('gulp-stylus'),
    cssNano = require('gulp-cssnano'),
    rename = require('gulp-rename'),
    concat = require('gulp-concat'),
    sourcemaps = require('gulp-sourcemaps'),
    inject = require('gulp-inject'),
    config = require('../config');

exports.task = function () {
    return gulp.src(config.projectName + '/**/*.styl')
        .pipe(sourcemaps.init())
        .pipe(stylus())
        .pipe(concat(config.projectName + '.css'))
        .pipe(rename({suffix: '.min'}))
        .pipe(cssNano())
        .pipe(sourcemaps.write('.'))
        .pipe(gulp.dest(config.destFolder + '/css'));
};