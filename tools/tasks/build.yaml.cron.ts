import * as gulp from 'gulp';
import { join } from 'path';
import { config } from '../config/config';
import * as newer from 'gulp-newer';

const mergeYaml = require('../utils/merge-yaml');

/**
 * Merges all cron.yaml files for every source root into one cron.yaml file.
 */
export = () => {
  let filename = 'cron.yaml';
  let src = config.SOURCE_ROOTS.map(root => join(root, filename));
  return gulp.src(src)
    .pipe(newer(join(config.BUILD_ROOT, filename)))
    .pipe(mergeYaml(filename))
    .pipe(gulp.dest(config.BUILD_ROOT));
};
