import {readdirSync, readFileSync, unlinkSync} from 'fs';
import {join} from 'path';

const directory = process.argv[2];

const foundIcons = new Set();
const allIcons = readdirSync(join(directory, 'svg')).map(filename => filename.replace('.svg', ''));

// Shitty way to check if icon is used in source code. Gives a few false positives like push, text, radio but this
// is better than having to manually add icons to a mapping on a per-project basis.
for (const file of readdirSync(directory)) {
  const path = join(directory, file);
  if (path.endsWith('.js') && !path.includes('polyfills')) {
    const fileContent = readFileSync(path).toString();
    for (const icon of allIcons) {
      if (foundIcons.has(icon)) {
        continue;
      }
      if (fileContent.includes(`"${icon}"`)) {
        foundIcons.add(icon);
      }
    }
  }
}
const iconsToRemove = allIcons.filter(icon => !foundIcons.has(icon));

console.log(`Removing ${iconsToRemove.length} unused icons`);

for (const icon of iconsToRemove) {
  const path = join(directory, 'svg', `${icon}.svg`);
  unlinkSync(path);
}
