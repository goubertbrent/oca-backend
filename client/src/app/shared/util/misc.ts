export function deepCopy<T extends object>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

export function* chunks<T>(array: T[], chunkSize: number) {
  for (let i = 0; i < array.length; (i += chunkSize)) {
    yield array.slice(i, i + chunkSize);
  }
}
