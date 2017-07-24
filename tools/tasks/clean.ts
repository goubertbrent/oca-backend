import { config } from '../config/config';
import { join } from 'path';

import * as del from 'del';

export = () => {
  // Cleanup everything in the build folder except for libraries
  const src = [ join(config.BUILD_ROOT, '*.*'),
    ...config.LIBRARY_ROOTS.map(lib => '!' + join(lib, '**', '*')) ];
  return del(src);
};
