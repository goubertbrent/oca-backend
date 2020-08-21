export interface ApiError<T = any> {
  status_code: number;
  error: string;
  data: T | null;
}

export interface ApiRequestStatus<T = any> {
  loading: boolean;
  success: boolean;
  error: ApiError<T> | null;
}

export const apiRequestInitial: ApiRequestStatus = {
  loading: false,
  success: false,
  error: null,
};

export const apiRequestLoading: ApiRequestStatus = {
  loading: true,
  success: false,
  error: null,
};

export const apiRequestSuccess: ApiRequestStatus = {
  loading: false,
  success: true,
  error: null,
};
