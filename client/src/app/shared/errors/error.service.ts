import { HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarConfig } from '@angular/material/snack-bar';
import { Action, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, of } from 'rxjs';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '../dialog/simple-dialog.component';
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
   * Shows a snackbar or dialog with a 'retry' button to retry the failed action
   * Defaults to showing a snackbar with a duration of 10 seconds.
   */
  handleError<T>(originalAction: Action,
                 failAction: new(error: string) => ErrorAction,
                 error: any,
                 options?: { duration?: number; format?: 'dialog' | 'toast', canRetry?: boolean }): Observable<Action> {
    const format = options?.format ?? 'toast';
    const retry = options?.canRetry ?? true;
    const clickAction: { action: Action, text: string } | undefined = retry ? {
      text: this.translate.instant('oca.Retry'),
      action: originalAction,
    } : undefined;
    const message = this.getMessage(error);
    if (format === 'toast') {
      this.showErrorSnackbar(message, clickAction, { duration: options?.duration ?? 10000 });
    } else {
      this.showErrorDialog(message, clickAction, retry ? this.translate.instant('Close') : undefined);
    }
    return this.toAction(failAction, error);
  }

  showErrorSnackbar(message: string, clickAction?: { action: Action, text: string }, config?: MatSnackBarConfig) {
    const snackbar = this.snackbar.open(message, clickAction?.text, config);
    if (clickAction?.action) {
      snackbar.onAction().subscribe(() => this.store.dispatch(clickAction.action));
    }
  }

  showErrorDialog(message: string, clickAction?: { action: Action, text: string }, cancel?: string): MatDialogRef<SimpleDialogComponent> {
    const data: SimpleDialogData = {
      ok: clickAction?.text ?? this.translate.instant('oca.Close'),
      cancel,
      message,
      title: this.translate.instant('oca.Error'),
    };
    const dialog = this.matDialog.open(SimpleDialogComponent, { data });
    if (clickAction?.action) {
      dialog.afterClosed().subscribe((result?: SimpleDialogResult) => {
        if (result?.submitted) {
          this.store.dispatch(clickAction.action);
        }
      });
    }
    return dialog;
  }
}
