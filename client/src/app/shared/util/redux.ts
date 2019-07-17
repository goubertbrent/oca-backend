import { Observable } from 'rxjs';

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
  return (source: Observable<T | null>): Observable<T> => new Observable(observer =>
    source.subscribe(value => {
        if (value !== null) {
          try {
            observer.next(value as T);
          } catch (err) {
            observer.error(err);
          }
        }
      },
      err => observer.error(err),
      () => observer.complete()));
}
