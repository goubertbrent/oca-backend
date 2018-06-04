import { copyFile, unlink } from 'fs';
import * as gulp from 'gulp';
import * as gutil from 'gulp-util';
import * as gulpWatch from 'gulp-watch';
import { join } from 'path';
import { config } from '../config/config';

const deleteEmpty = require('delete-empty');
const debounce = require('lodash.debounce');

if (process.platform === 'darwin') {
  try {
    require('fsevents');
  } catch (ignored) {
    throw new Error('Could not require fsevents, please execute `npm install` again.');
  }
}

/**
 * Copies files from build roots over to the 'build' folder.
 * Ensures changes are in sync with the source root by copying changed files and removing deleted files.
 */
export function watch() {
  const debouncedClean = debounce(cleanEmptyFolders, 200);
  return function () {
    let paths: string[] = [
      ...config.SOURCE_ROOTS.map(root => join(root, '**')),
      ...config.TEMP_FILES.map(temp => '!' + temp) ];

    gulpWatch(paths, (e) => {
      if (e.path.endsWith('.yaml')) {
        gulp.task('merge.yaml')(() => {
          gutil.log('Rebuild yaml files');
        });
      } else {
        const sourceRoot = config.SOURCE_ROOTS.find(root => e.path.startsWith(root));
        const buildFolderPath = e.path.replace(sourceRoot, config.BUILD_ROOT);
        switch (e.event) {
          case 'add':
            copyFile(e.path, buildFolderPath, () => gutil.log(gutil.colors.green(`Created file ${buildFolderPath}`)));
            break;
          case 'unlink':
            unlink(buildFolderPath, () => gutil.log(gutil.colors.red(`Removed file ${buildFolderPath}`)));
            if (buildFolderPath.endsWith('.py')) {
              unlink(buildFolderPath.replace('.py', '.pyc'), () => {
              });
            }
            debouncedClean();
            break;
          case 'change':
            copyFile(e.path, buildFolderPath, () => gutil.log(gutil.colors.yellow(`Updated file ${buildFolderPath}`)));
            break;
        }
      }
    });
  };
}

export function cleanEmptyFolders() {
  return deleteEmpty.sync(config.BUILD_ROOT);
}
