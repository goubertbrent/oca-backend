export function kebabCase(word: string): string {
  return word.replace(/\s+/g, '-').toLowerCase();
}
