export interface Loadable<T, U = any> {
  loading: boolean;
  success: boolean;
  data: T | null;
  error: U | null;
}

export interface NonNullLoadable<T, U = any> {
  loading: boolean;
  success: boolean;
  data: T;
  error: U | null;
}

export const DEFAULT_LOADABLE: Loadable<null> = {
  loading: false,
  success: false,
  data: null,
  error: null,
};

export const DEFAULT_LIST_LOADABLE: NonNullLoadable<any[]> = {
  loading: false,
  success: false,
  data: [],
  error: null,
};

export function onLoadableLoad<T>(data: T): NonNullLoadable<T> {
  return {
    data,
    loading: true,
    success: false,
    error: null,
  };
}

export function onLoadableSuccess<T>(data: T): NonNullLoadable<T> {
  return {
    data,
    loading: false,
    success: true,
    error: null,
  };
}

export function onLoadableError<T, U>(error: T, data: U): NonNullLoadable<U, T> {
  return {
    data,
    loading: false,
    success: false,
    error,
  };
}
