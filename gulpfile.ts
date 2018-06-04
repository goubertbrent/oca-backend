import * as gulp from 'gulp';
import { join } from 'path';
import { loadCompositeTasks, loadTasks } from './tools/utils/tasks_tools';

loadTasks(join(process.cwd(), 'tools', 'tasks'));

let firstRun = true;
gulp.task('init', (done: any) => {
  if (firstRun) {
    firstRun = false;
    gulp.series(['clean', 'build.versions'])(done);
  } else {
    done();
  }
});
loadCompositeTasks(join(process.cwd(), 'tools', 'config', 'tasks.json'));
