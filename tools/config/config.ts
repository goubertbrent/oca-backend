import { realpathSync } from 'fs';
import { join } from 'path';

const PROJECT_ROOT = realpathSync(join(__dirname, '..', '..'));

export class Config {
  PROJECT_ROOT = PROJECT_ROOT;
  BUILD_ROOT = join(PROJECT_ROOT, 'build');
  SOURCE_ROOTS = [
    realpathSync(join(PROJECT_ROOT, '..', 'rogerthat-backend', 'src')),
    realpathSync(join(PROJECT_ROOT, 'src')), // Files with the same name will be overwritten from this repo
  ];
  LIBRARY_ROOTS = [
    join(this.BUILD_ROOT, 'lib'),
    join(this.BUILD_ROOT, 'static', 'node_modules'),
  ];
  TEMP_FILES: string[] = [
    '**/*___jb_tmp___',
    '**/*~',
  ];
}

export const config = new Config();
