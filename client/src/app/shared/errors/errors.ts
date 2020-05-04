import { HttpErrorResponse } from '@angular/common/http';
import { Action } from '@ngrx/store';

export interface ApiError<T = any> {
  status_code: number;
  error: string;
  data: T | null;
}

export interface ErrorAction extends Action {
  error: string;
}


export function transformErrorResponse(response: HttpErrorResponse): ApiError {
  let apiError: ApiError;
  if (typeof response.error === 'object' && response.error.error) {
    apiError = response.error;
  } else {
    // Most likely a non-json response, return generic error
    apiError = {
      status_code: response.status,
      error: 'oca.error-occured-unknown-try-again',
      data: {
        response: response.error,
      },
    };
  }
  return apiError;
}
