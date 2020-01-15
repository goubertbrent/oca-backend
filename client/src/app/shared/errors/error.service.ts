import { HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { MatSnackBar, MatSnackBarConfig } from '@angular/material/snack-bar';
import { Action, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, of } from 'rxjs';
import { SharedState } from '../shared.state';
import { ApiError } from './errors';

@Injectable({ providedIn: 'root' })
export class ErrorService {

  constructor(private translate: TranslateService,
              private snackbar: MatSnackBar,
              private store: Store<SharedState>) {
  }

  getErrorMessage(error: ApiError): string {
    // Translated on server
    if (error.error === 'oca.error') {
      return error.data.message;
    }
    if (this.translate.currentLang in this.translate.translations
      && error.error in this.translate.translations[ this.translate.currentLang ]) {
      return this.translate.instant(error.error, error.data);
    } else {
      return this.translate.instant('oca.error-occured-unknown-try-again');
    }
  }

  getMessage(error: any): string {
    if (error instanceof HttpErrorResponse) {
      if (error.error && error.error.error) {
        const e = error.error as ApiError;
        if (e.error === 'oca.error') {
          return e.data.message;
        }
        return e.error;
      }
    }
    if (error instanceof Error) {
      console.error(error);
    }
    return this.translate.instant('oca.error-occured-unknown-try-again');
  }

  toAction(action: any, error: any): Observable<Action> {
    const message = this.getMessage(error);
    return of(new (action as any)(message));
  }

  /**
   * Shows a snackbar with a 'retry' button to retry the failed action
   */
  handleError(originalAction: Action, failAction: any, error: any, duration?: number): Observable<Action> {
    this.showRetrySnackbar(originalAction, error, { duration });
    return this.toAction(failAction, error);
  }

  showRetrySnackbar(failedAction: Action, error: any, config?: MatSnackBarConfig) {
    const message = this.getMessage(error);
    const retry = this.translate.instant('oca.Retry');
    this.snackbar.open(message, retry, config).onAction().subscribe(() => this.store.dispatch(failedAction));
  }
}
