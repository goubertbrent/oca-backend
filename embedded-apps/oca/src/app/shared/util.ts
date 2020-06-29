export function encodeURIObject(object: { [ key: string ]: string }): string {
  return Object.entries(object).map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`).join('&');
}
