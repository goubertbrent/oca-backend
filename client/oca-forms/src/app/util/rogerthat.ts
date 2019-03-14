export function createAppUser(email: string, appId?: string) {
  if (!appId || appId === 'rogerthat') {
    return email;
  }
  return `${email}:${appId}`;
}
