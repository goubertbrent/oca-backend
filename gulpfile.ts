import * as gulp from 'gulp';
import * as runSequence from 'run-sequence';

import { loadCompositeTasks, loadTasks } from './tools/utils/tasks_tools';
import { join } from 'path';

loadTasks(join(process.cwd(), 'tools', 'tasks'));
loadCompositeTasks(join(process.cwd(), 'tools', 'config', 'tasks.json'));

let firstRun = true;
gulp.task('init', (done: any) => {
  if (firstRun) {
    firstRun = false;
    runSequence('clean', 'build.versions', done);
  } else {
    done();
  }
});
