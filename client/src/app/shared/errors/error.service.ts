import { HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarConfig } from '@angular/material/snack-bar';
import { Action, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, of } from 'rxjs';
import { SimpleDialogComponent, SimpleDialogData } from '../dialog/simple-dialog.component';
import { SharedState } from '../shared.state';
import { ApiError, ErrorAction } from './errors';

@Injectable({ providedIn: 'root' })
export class ErrorService {

  constructor(private translate: TranslateService,
              private snackbar: MatSnackBar,
              private matDialog: MatDialog,
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

  toAction(action: new(error: string) => ErrorAction, error: any): Observable<ErrorAction> {
    const message = this.getMessage(error);
    return of(new action(message));
  }

  /**
   * Shows a snackbar with a 'retry' button to retry the failed action
   */
  handleError<T>(originalAction: Action, failAction: new(error: string) => ErrorAction, error: any, duration?: number): Observable<Action> {
    this.showRetrySnackbar(originalAction, error, { duration: duration ?? 10000 });
    return this.toAction(failAction, error);
  }

  showRetrySnackbar(failedAction: Action, error: any, config?: MatSnackBarConfig) {
    const message = this.getMessage(error);
    const retry = this.translate.instant('oca.Retry');
    this.snackbar.open(message, retry, config).onAction().subscribe(() => this.store.dispatch(failedAction));
  }

  showErrorDialog(error: string) {
    const data: SimpleDialogData = {
      ok: this.translate.instant('oca.ok'),
      message: error,
      title: this.translate.instant('oca.Error'),
    };
    return this.matDialog.open(SimpleDialogComponent, { data });
  }
}
