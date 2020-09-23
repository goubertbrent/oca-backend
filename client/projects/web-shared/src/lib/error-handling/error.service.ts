import { HttpErrorResponse } from '@angular/common/http';
import { Inject, Injectable, InjectionToken } from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarConfig } from '@angular/material/snack-bar';
import { Action, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, of } from 'rxjs';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '../simple-dialog';
import { ApiError, ErrorAction, ErrorActionCreator, ErrorActionCreatorOrErrorAction } from './error';
import { ErrorHandlingModule } from './error-handling.module';
import { ERROR_HANDLING_TRANSLATIONS, ErrorServiceTranslations } from './providers';


@Injectable({ providedIn: ErrorHandlingModule })
export class ErrorService {

  constructor(private translate: TranslateService,
              private snackbar: MatSnackBar,
              private matDialog: MatDialog,
              private store: Store,
              @Inject(ERROR_HANDLING_TRANSLATIONS)
              private translationKeys: ErrorServiceTranslations) {
  }

  getErrorMessage(error: ApiError): string {
    // Translated on server
    if (error.error === this.translationKeys.knownErrorKey) {
      return error.data.message;
    }
    if (this.translate.currentLang in this.translate.translations
      && error.error in this.translate.translations[ this.translate.currentLang ]) {
      return this.translate.instant(error.error, error.data);
    } else {
      return this.translate.instant(this.translationKeys.unknownError);
    }
  }

  getMessage(error: any): string {
    if (error instanceof HttpErrorResponse) {
      if (error.error && error.error.error) {
        const e = error.error as ApiError;
        if (e.error === this.translationKeys.knownErrorKey) {
          return e.data.message;
        }
        return e.error;
      }
    }
    if (error instanceof Error) {
      console.error(error);
    }
    return this.translate.instant(this.translationKeys.unknownError);
  }

  toAction<T extends string>(action: ErrorActionCreatorOrErrorAction<T>, error: any): Observable<ErrorAction> {
    const message = this.getMessage(error);
    if (isActionCreator(action)) {
      return of(action({ error: message }));
    } else {
      return of(new action(message));
    }
  }

  /**
   * Shows a snackbar or dialog with a 'retry' button to retry the failed action
   * Defaults to showing a snackbar with a duration of 10 seconds.
   */
  handleError<T extends string>(originalAction: Action,
                                failAction: ErrorActionCreatorOrErrorAction<T>,
                                error: any,
                                options?: { duration?: number; format?: 'dialog' | 'toast', canRetry?: boolean }): Observable<Action> {
    const format = options?.format ?? 'toast';
    const retry = options?.canRetry ?? true;
    const clickAction: { action: Action, text: string } | undefined = retry ? {
      text: this.translate.instant(this.translationKeys.retry),
      action: originalAction,
    } : undefined;
    const message = this.getMessage(error);
    if (format === 'toast') {
      this.showErrorSnackbar(message, clickAction, { duration: options?.duration ?? 10000 });
    } else {
      this.showErrorDialog(message, clickAction, retry ? this.translate.instant(this.translationKeys.close) : undefined);
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
      ok: clickAction?.text ?? this.translate.instant(this.translationKeys.close),
      cancel,
      message,
      title: this.translate.instant(this.translationKeys.error),
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

function isActionCreator<T extends string>(obj: ErrorActionCreatorOrErrorAction<T>): obj is ErrorActionCreator<T> {
  return 'type' in obj;
}
