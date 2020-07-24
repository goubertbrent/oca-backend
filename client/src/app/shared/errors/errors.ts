import { HttpErrorResponse } from '@angular/common/http';
import { ApiError } from '@oca/web-shared';


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

export { ApiError, ErrorAction } from '@oca/web-shared';
