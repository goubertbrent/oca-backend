import { HttpErrorResponse } from '@angular/common/http';
import { of } from 'rxjs';
import { ApiError, ApiRequestStatus } from './rpc.interfaces';

export function transformErrorResponse<T = any>(response: HttpErrorResponse): ApiRequestStatus<T> {
  let apiError: ApiError<T>;
  if (typeof response.error === 'object') {
    apiError = response.error;
  } else {
    // Most likely a non-json response
    apiError = {
      status_code: response.status,
      error: response.statusText,
      data: <any>{
        response: response.error,
      },
    };
  }
  return {
    error: apiError,
    loading: false,
    success: false,
  };
}

export function handleApiError(action: any, response: HttpErrorResponse) {
  return of(new action(transformErrorResponse(response)));
}
