import * as gulp from 'gulp';
import { join } from 'path';
import { config } from '../config/config';
import * as newer from 'gulp-newer';

const mergeYaml = require('../utils/merge-yaml');
/**
 * Merges all app.yaml files for every source root into one app.yaml file.
 */
export = () => {
  let filename = 'app.yaml';
  let src = config.SOURCE_ROOTS.map(root => join(root, filename));
  return gulp.src(src)
    .pipe(newer({ dest: join(config.BUILD_ROOT, filename) }))
    .pipe(mergeYaml(filename, { appYaml: true }))
    .pipe(gulp.dest(config.BUILD_ROOT));
};
