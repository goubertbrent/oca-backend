import { Injectable } from '@angular/core';
import { MatDialog, MatSnackBar } from '@angular/material';
import { Router } from '@angular/router';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { SimpleDialogComponent, SimpleDialogData } from '../dialog/simple-dialog.component';
import { OcaForm } from '../interfaces/forms.interfaces';
import {
  CreateFormAction,
  CreateFormCompleteAction,
  CreateFormFailedAction,
  DeleteAllResponsesAction,
  DeleteAllResponsesCompleteAction,
  DeleteAllResponsesFailedAction,
  DeleteFormAction,
  DeleteFormCompleteAction,
  DeleteFormFailedAction,
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
  ShowDeleteAllResponsesAction,
  ShowDeleteAllResponsesCanceledAction,
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
    tap(action => action.payload.silent ? null : this.snackbar.open(this.translate.instant('oca.saving_form'), undefined, { duration: 5000 })),
    switchMap(action => this.formsService.saveForm(action.payload.data as OcaForm).pipe(
      tap(() => action.payload.silent ? null : this.snackbar.open(this.translate.instant('oca.form_saved'), this.translate.instant('oca.ok'), { duration: 3000 })),
      map(form => new SaveFormCompleteAction(form)),
      catchError(err => of(new SaveFormFailedAction(err))))),
  );

  @Effect() testForm$ = this.actions$.pipe(
    ofType<TestFormAction>(FormsActionTypes.TEST_FORM),
    tap(action => {
      const params = { user: action.testers.join(',') };
      this.snackbar.open(this.translate.instant('oca.sending_test_form_to_x', params), undefined, { duration: 5000 });
    }),
    switchMap(action => this.formsService.testForm(action.formId, action.testers).pipe(
      tap(() => this.snackbar.open(this.translate.instant('oca.form_sent'), this.translate.instant('oca.ok'), { duration: 5000 })),
      map(() => new TestFormCompleteAction()),
      catchError(err => of(new TestFormFailedAction(err))))),
  );

  @Effect() createForm$ = this.actions$.pipe(
    ofType<CreateFormAction>(FormsActionTypes.CREATE_FORM),
    tap(() => this.snackbar.open(this.translate.instant('oca.creating_form'), undefined, { duration: 3000 })),
    switchMap(() => this.formsService.createForm().pipe(
      map(form => new CreateFormCompleteAction(form)),
      tap(createAction => {
        this.router.navigate([ 'forms', createAction.form.form.id ]);
        this.snackbar.open(this.translate.instant('oca.form_created'), this.translate.instant('oca.ok'), { duration: 3000 });
      }),
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

  @Effect() deleteForm$ = this.actions$.pipe(
    ofType<DeleteFormAction>(FormsActionTypes.DELETE_FORM),
    tap(() => this.snackbar.open(this.translate.instant('oca.deleting_form'), undefined, { duration: 5000 })),
    switchMap(action => this.formsService.deleteForm(action.form.id).pipe(
      tap(() => this.snackbar.open(this.translate.instant('oca.form_deleted'), this.translate.instant('oca.ok'), { duration: 3000 })),
      map(() => new DeleteFormCompleteAction(action.form)),
      catchError(err => of(new DeleteFormFailedAction(err))))),
  );

  @Effect() getTombolaWinners$ = this.actions$.pipe(
    ofType<GetTombolaWinnersAction>(FormsActionTypes.GET_TOMBOLA_WINNERS),
    switchMap(action => this.formsService.getTombolaWinners(action.formId).pipe(
      map(data => new GetTombolaWinnersCompleteAction(data)),
      catchError(err => of(new GetTombolaWinnersFailedAction(err))))),
  );

  @Effect() showDeleteAllResponsesDialog$ = this.actions$.pipe(
    ofType<ShowDeleteAllResponsesAction>(FormsActionTypes.SHOW_DELETE_ALL_RESPONSES),
    switchMap(action => this.matDialog.open(SimpleDialogComponent, {
        data: {
          ok: this.translate.instant('oca.yes'),
          message: action.message,
          title: this.translate.instant('oca.confirm_deletion'),
          cancel: this.translate.instant('oca.no'),
        } as SimpleDialogData,
      }).afterClosed().pipe(
      map(result => result.submitted ? new DeleteAllResponsesAction(action.formId) : new ShowDeleteAllResponsesCanceledAction())),
    ),
  );

  @Effect() deleteAllResponses$ = this.actions$.pipe(
    ofType<DeleteAllResponsesAction>(FormsActionTypes.DELETE_ALL_RESPONSES),
    switchMap(action => this.formsService.deleteAllResponses(action.formId).pipe(
      map(data => new DeleteAllResponsesCompleteAction()),
      catchError(err => of(new DeleteAllResponsesFailedAction(err))))),
  );

  constructor(private actions$: Actions<FormsActions>,
              private formsService: FormsService,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private router: Router,
              private matDialog: MatDialog) {
  }
}
