import * as del from 'del';
import { join } from 'path';
import { config } from '../config/config';

export = () => {
  // Cleanup everything in the build folder except for libraries
  const src = [ join(config.BUILD_ROOT, '*.*'),
    ...config.LIBRARY_ROOTS.map(lib => '!' + join(lib, '**', '*')) ];
  return del(src);
};
