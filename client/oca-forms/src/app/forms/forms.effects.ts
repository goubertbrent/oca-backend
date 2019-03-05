import { Injectable } from '@angular/core';
import { MatDialog, MatSnackBar } from '@angular/material';
import { Router } from '@angular/router';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs/internal/observable/of';
import { switchMap } from 'rxjs/internal/operators/switchMap';
import { tap } from 'rxjs/internal/operators/tap';
import { catchError, map } from 'rxjs/operators';
import { SimpleDialogComponent, SimpleDialogData } from '../dialog/simple-dialog.component';
import {
  CreateFormAction,
  CreateFormCompleteAction,
  CreateFormFailedAction,
  FormsActions,
  FormsActionTypes,
  GetFormAction,
  GetFormCompleteAction,
  GetFormFailedAction,
  GetFormsAction,
  GetFormsCompleteAction,
  GetFormsFailedAction,
  GetFormStatisticsAction,
  GetFormStatisticsCompleteAction,
  GetFormStatisticsFailedAction,
  GetTombolaWinnersAction,
  GetTombolaWinnersCompleteAction,
  GetTombolaWinnersFailedAction,
  SaveFormAction,
  SaveFormCompleteAction,
  SaveFormFailedAction,
  TestFormAction,
  TestFormCompleteAction,
  TestFormFailedAction,
} from './forms.actions';
import { FormsService } from './forms.service';

@Injectable({ providedIn: 'root' })
export class FormsEffects {
  @Effect() getForms$ = this.actions$.pipe(
    ofType<GetFormsAction>(FormsActionTypes.GET_FORMS),
    switchMap(() => this.formsService.getForms().pipe(
      map(forms => new GetFormsCompleteAction(forms)),
      catchError(err => of(new GetFormsFailedAction(err))))),
  );

  @Effect() getForm$ = this.actions$.pipe(
    ofType<GetFormAction>(FormsActionTypes.GET_FORM),
    switchMap(action => this.formsService.getForm(action.id).pipe(
      map(form => new GetFormCompleteAction(form)),
      catchError(err => of(new GetFormFailedAction(err))))),
  );

  @Effect() getFormStatistics$ = this.actions$.pipe(
    ofType<GetFormStatisticsAction>(FormsActionTypes.GET_FORM_STATISTICS),
    switchMap(action => this.formsService.getFormStatistics(action.id).pipe(
      map(form => new GetFormStatisticsCompleteAction(form)),
      catchError(err => of(new GetFormStatisticsFailedAction(err))))),
  );

  @Effect() saveForm$ = this.actions$.pipe(
    ofType<SaveFormAction>(FormsActionTypes.SAVE_FORM),
    tap(() => this.snackbar.open(this.translate.instant('oca.saving_form'), null, { duration: 5000 })),
    switchMap(action => this.formsService.saveForm(action.form).pipe(
      map(form => new SaveFormCompleteAction(form)),
      tap(() => this.snackbar.open(this.translate.instant('oca.form_saved'), this.translate.instant('oca.ok'), { duration: 3000 })),
      catchError(err => of(new SaveFormFailedAction(err))))),
  );

  @Effect() testForm$ = this.actions$.pipe(
    ofType<TestFormAction>(FormsActionTypes.TEST_FORM),
    tap(action => {
      const params = { user: action.testers.join(',') };
      this.snackbar.open(this.translate.instant('oca.sending_test_form_to_x', params), null, { duration: 5000 });
    }),
    switchMap(action => this.formsService.testForm(action.formId, action.testers).pipe(
      tap(() => this.snackbar.open(this.translate.instant('oca.form_sent'), this.translate.instant('oca.ok'), { duration: 5000 })),
      map(() => new TestFormCompleteAction()),
      catchError(err => of(new TestFormFailedAction(err))))),
  );

  @Effect() createForm$ = this.actions$.pipe(
    ofType<CreateFormAction>(FormsActionTypes.CREATE_FORM),
    tap(() => this.snackbar.open(this.translate.instant('oca.saving_form'), null, { duration: 3000 })),
    switchMap(action => this.formsService.createForm(action.form).pipe(
      map(form => new CreateFormCompleteAction(form)),
      tap(createAction => this.router.navigate([ 'forms', createAction.form.form.id ])),
      catchError(err => of(new CreateFormFailedAction(err))))),
  );

  @Effect({ dispatch: false }) afterSaveFailed$ = this.actions$.pipe(
    ofType<CreateFormFailedAction | SaveFormFailedAction>(FormsActionTypes.CREATE_FORM_FAILED, FormsActionTypes.SAVE_FORM_FAILED,
      FormsActionTypes.TEST_FORM_FAILED),
    tap(action => {
      this.matDialog.open(SimpleDialogComponent, {
        data: {
          ok: this.translate.instant('oca.ok'),
          message: action.error.error.error,
          title: this.translate.instant('oca.error'),
        } as SimpleDialogData,
      });
    }),
  );

  @Effect() getTombolaWinners$ = this.actions$.pipe(
    ofType<GetTombolaWinnersAction>(FormsActionTypes.GET_TOMBOLA_WINNERS),
    switchMap(action => this.formsService.getTombolaWinners(action.formId).pipe(
      map(data => new GetTombolaWinnersCompleteAction(data)),
      catchError(err => of(new GetTombolaWinnersFailedAction(err))))),
  );

  constructor(private actions$: Actions<FormsActions>,
              private formsService: FormsService,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private router: Router,
              private matDialog: MatDialog) {

  }

}
