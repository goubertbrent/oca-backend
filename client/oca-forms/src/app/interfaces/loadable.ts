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

export const DEFAULT_LIST_LOADABLE: Loadable<any[]> = {
  loading: false,
  success: false,
  data: [],
  error: null,
};

export function onLoadableLoad<T>(data: T): Loadable<T> {
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

export function onLoadableError<T>(error: T): Loadable<null, T> {
  return {
    data: null,
    loading: false,
    success: false,
    error,
  };
}
