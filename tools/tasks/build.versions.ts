import { config } from '../config/config';
import { dirname, join, sep } from 'path';
import * as shell from 'shelljs';
import * as fs from 'fs';

/**
 * Writes versions of source roots to version/__init__.py
 */
export = () => {
  const versions = config.SOURCE_ROOTS.map(root => {
    const { stdout, stderr } = shell.exec('git rev-parse --short HEAD', { silent: true, cwd: root });
    if (stderr) {
      console.error(stderr);
      throw Error('Error getting version');
    }
    return { version: (<string>stdout).trim(), repo: dirname(root).split(sep).pop() };
  });

  const versionsString = versions.map(v => `    '${v.repo}': '${v.version}'`).join(',\n');
  const content = `# coding=utf-8
VERSIONS = {
${versionsString}
}`;
  const dir = join(config.BUILD_ROOT, 'version');
  const filePath = join(dir, '__init__.py');
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir);
  }
  fs.writeFileSync(filePath, content);
}
