import * as gulp from 'gulp';
import { join } from 'path';
import { config } from '../config/config';
import * as newer from 'gulp-newer';

/**
 * Copies files from all source roots to the build folder
 */
export = () => {
  const src = [
    ...config.SOURCE_ROOTS.map(root => join(root, '**')),
    ...config.SOURCE_ROOTS.map(root => join(`!${root}`, '*.yaml'))
  ];
  return gulp.src(src)
    .pipe(newer(config.BUILD_ROOT))
    .pipe(gulp.dest(config.BUILD_ROOT));
};
