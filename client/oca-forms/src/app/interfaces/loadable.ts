export interface Loadable<T, U = any> {
  loading: boolean;
  success: boolean;
  data: T | null;
  error: U | null;
}

export const DEFAULT_LOADABLE: Loadable<null> = {
  loading: false,
  success: false,
  data: null,
  error: null,
};

export function onLoadableLoad(): Loadable<null> {
  return {
    loading: true,
    success: false,
    data: null,
    error: null,
  };
}

export function onLoadableSuccess<T>(data: T): Loadable<T> {
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
