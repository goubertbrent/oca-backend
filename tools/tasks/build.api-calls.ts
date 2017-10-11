import * as gulp from 'gulp';
import { join } from 'path';
import { config } from '../config/config';
import * as newer from 'gulp-newer';
import * as concat from 'gulp-concat';

export = () => {
  let filename = 'rogerthat_service_api_calls.py';
  let src = config.SOURCE_ROOTS.map(root => join(root, filename));
  return gulp.src(src)
    .pipe(newer({ dest: join(config.BUILD_ROOT, filename) }))
    .pipe(concat(filename))
    .pipe(gulp.dest(config.BUILD_ROOT));
};
