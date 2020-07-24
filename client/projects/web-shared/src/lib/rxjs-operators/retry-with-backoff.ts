import { HttpErrorResponse } from '@angular/common/http';
import { Observable, of, throwError } from 'rxjs';
import { delay, mergeMap, retryWhen } from 'rxjs/operators';

const DEFAULT_MAX_RETRIES = 5;
const DEFAULT_BACKOFF = 1000;

export function retryWithBackoff<T>(maxRetry = DEFAULT_MAX_RETRIES, backoffMs = DEFAULT_BACKOFF) {
  let retries = 0;
  return (src: Observable<T>) => src.pipe(
    retryWhen((errors: Observable<unknown>) => errors.pipe(
      mergeMap(error => {
        // No retries for http errors 400-500 as those should always return the same status
        if (error instanceof HttpErrorResponse && error.status >= 400 && error.status < 500) {
          return throwError(error);
        }
        if (retries++ < maxRetry) {
          const backoffTime =  backoffMs * Math.pow(2, retries);
          return of(error).pipe(delay(backoffTime));
        }
        return throwError(error);
      }),
    )),
  );
}
