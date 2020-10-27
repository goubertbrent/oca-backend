import { Observable, Subject } from 'rxjs';

export function insertItem<T>(array: T[], updatedItem: T, index?: number): T[] {
  if (!index) {
    index = array.length;
  }
  return [ ...array.slice(0, index), updatedItem, ...array.slice(index) ];
}

export function updateItem<T>(array: T[], updatedItem: T, idProperty: (keyof T)): T[] {
  return array.map(item => item[ idProperty ] === updatedItem[ idProperty ] ? updatedItem : item);
}

export function removeItem<T>(array: T[], itemToRemove: T | number | string, idProperty: (keyof T)): T[] {
  const compareVal = typeof itemToRemove === 'number' || typeof itemToRemove === 'string' ? itemToRemove : itemToRemove[ idProperty ];
  return array.filter(item => item[ idProperty ] !== compareVal);
}

export function filterNull<T>() {
  return function filterNullImplementation(source: Observable<T | null>): Observable<T> {
    return Observable.create((subscriber: Subject<T>) => {
      return source.subscribe(value => {
          if (value !== null) {
            try {
              subscriber.next(<T>value);
            } catch (err) {
              subscriber.error(err);
            }
          }
        },
        err => subscriber.error(err),
        () => subscriber.complete());
    });
  };
}

export function createAppUser(email: string, appId?: string) {
  if (!appId || appId === 'rogerthat') {
    return email;
  }
  return `${email}:${appId}`;
}

export function encodeURIObject(object: { [ key: string ]: string }): string {
  return Object.entries(object).map(([ key, value ]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`).join('&');
}
