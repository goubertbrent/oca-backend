import { Injectable } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { catchError, first, map, startWith, switchMap, tap } from 'rxjs/operators';
import { SimpleDialogComponent, SimpleDialogData } from '../shared/dialog/simple-dialog.component';
import { ErrorService } from '../shared/errors/error.service';
import { transformErrorResponse } from '../shared/errors/errors';
import {
  CopyFormAction,
  CopyFormCompleteAction,
  CopyFormFailedAction,
  CreateFormAction,
  CreateFormCompleteAction,
  CreateFormFailedAction,
  DeleteAllResponsesAction,
  DeleteAllResponsesCompleteAction,
  DeleteAllResponsesFailedAction,
  DeleteFormAction,
  DeleteFormCompleteAction,
  DeleteFormFailedAction,
  DeleteResponseAction,
  DeleteResponseCanceledAction,
  DeleteResponseCompleteAction,
  DeleteResponseFailedAction,
  DownloadResponsesCompleteAction,
  DownloadResponsesFailedAction,
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
  GetIntegrationsAction,
  GetIntegrationsCompleteAction,
  GetIntegrationsFailedAction,
  GetNextResponseAction,
  GetResponseAction,
  GetResponsesAction,
  GetResponsesCompleteAction,
  GetResponsesFailedAction,
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
  UpdateIntegrationAction,
  UpdateIntegrationCompleteAction,
  UpdateIntegrationFailedAction,
} from './forms.actions';
import { FormsService } from './forms.service';
import { FormsState, getForm, getResponsesData } from './forms.state';
import { OcaForm } from './interfaces/forms';

@Injectable({ providedIn: 'root' })
export class FormsEffects {
   getForms$ = createEffect(() => this.actions$.pipe(
    ofType<GetFormsAction>(FormsActionTypes.GET_FORMS),
    switchMap(() => this.formsService.getForms().pipe(
      map(forms => new GetFormsCompleteAction(forms)),
      catchError(err => of(new GetFormsFailedAction(transformErrorResponse(err)))))),
  ));

   getForm$ = createEffect(() => this.actions$.pipe(
    ofType<GetFormAction>(FormsActionTypes.GET_FORM),
    switchMap(action => this.formsService.getForm(action.id).pipe(
      map(form => new GetFormCompleteAction(form)),
      catchError(err => of(new GetFormFailedAction(transformErrorResponse(err)))))),
  ));

   getFormStatistics$ = createEffect(() => this.actions$.pipe(
    ofType<GetFormStatisticsAction>(FormsActionTypes.GET_FORM_STATISTICS),
    switchMap(action => this.formsService.getFormStatistics(action.id).pipe(
      map(form => new GetFormStatisticsCompleteAction(form)),
      catchError(err => of(new GetFormStatisticsFailedAction(transformErrorResponse(err)))))),
  ));

   saveForm$ = createEffect(() => this.actions$.pipe(
    ofType<SaveFormAction>(FormsActionTypes.SAVE_FORM),
    tap(action => action.payload.silent ? null : this.snackbar.open(this.translate.instant('oca.saving_form'),
      undefined, { duration: 5000 })),
    switchMap(action => this.formsService.saveForm(action.payload.data as OcaForm).pipe(
      tap(() => action.payload.silent ? null : this.snackbar.open(this.translate.instant('oca.form_saved'),
        this.translate.instant('oca.ok'), { duration: 3000 })),
      map(form => new SaveFormCompleteAction(form)),
      catchError(err => of(new SaveFormFailedAction(transformErrorResponse(err)))))),
  ));

   testForm$ = createEffect(() => this.actions$.pipe(
    ofType<TestFormAction>(FormsActionTypes.TEST_FORM),
    tap(action => {
      const params = { user: action.testers.join(',') };
      this.snackbar.open(this.translate.instant('oca.sending_test_form_to_x', params), undefined, { duration: 5000 });
    }),
    switchMap(action => this.formsService.testForm(action.formId, action.testers).pipe(
      tap(() => this.snackbar.open(this.translate.instant('oca.form_sent'), this.translate.instant('oca.ok'), { duration: 5000 })),
      map(() => new TestFormCompleteAction()),
      catchError(err => of(new TestFormFailedAction(transformErrorResponse(err)))))),
  ));

   createForm$ = createEffect(() => this.actions$.pipe(
    ofType<CreateFormAction>(FormsActionTypes.CREATE_FORM),
    tap(() => this.snackbar.open(this.translate.instant('oca.creating_form'), undefined, { duration: 3000 })),
    switchMap(() => this.formsService.createForm().pipe(
      map(form => new CreateFormCompleteAction(form)),
      tap(createAction => {
        this.router.navigate([ 'forms', createAction.form.form.id ]);
        this.snackbar.open(this.translate.instant('oca.form_created'), this.translate.instant('oca.ok'), { duration: 3000 });
      }),
      catchError(err => of(new CreateFormFailedAction(transformErrorResponse(err)))))),
  ));

   afterFailure$ = createEffect(() => this.actions$.pipe(
    ofType<CreateFormFailedAction | SaveFormFailedAction | DownloadResponsesFailedAction>(FormsActionTypes.CREATE_FORM_FAILED,
      FormsActionTypes.SAVE_FORM_FAILED, FormsActionTypes.TEST_FORM_FAILED, FormsActionTypes.DOWNLOAD_RESPONSES_FAILED),
    tap(action => {
      this.matDialog.open(SimpleDialogComponent, {
        data: {
          ok: this.translate.instant('oca.ok'),
          message: this.errorService.getErrorMessage(action.error),
          title: this.translate.instant('oca.Error'),
        } as SimpleDialogData,
      });
    }),
  ), { dispatch: false });

   deleteForm$ = createEffect(() => this.actions$.pipe(
    ofType<DeleteFormAction>(FormsActionTypes.DELETE_FORM),
    tap(() => this.snackbar.open(this.translate.instant('oca.deleting_form'), undefined, { duration: 5000 })),
    switchMap(action => this.formsService.deleteForm(action.form.id).pipe(
      tap(() => this.snackbar.open(this.translate.instant('oca.form_deleted'), this.translate.instant('oca.ok'), { duration: 3000 })),
      map(() => new DeleteFormCompleteAction(action.form)),
      catchError(err => of(new DeleteFormFailedAction(transformErrorResponse(err)))))),
  ));

   getTombolaWinners$ = createEffect(() => this.actions$.pipe(
    ofType<GetTombolaWinnersAction>(FormsActionTypes.GET_TOMBOLA_WINNERS),
    switchMap(action => this.formsService.getTombolaWinners(action.formId).pipe(
      map(data => new GetTombolaWinnersCompleteAction(data)),
      catchError(err => of(new GetTombolaWinnersFailedAction(transformErrorResponse(err)))))),
  ));

   showDeleteAllResponsesDialog$ = createEffect(() => this.actions$.pipe(
    ofType<ShowDeleteAllResponsesAction>(FormsActionTypes.SHOW_DELETE_ALL_RESPONSES),
    switchMap(action => this.matDialog.open(SimpleDialogComponent, {
        data: {
          ok: this.translate.instant('oca.Yes'),
          message: action.message,
          title: this.translate.instant('oca.confirm_deletion'),
          cancel: this.translate.instant('oca.No'),
        } as SimpleDialogData,
      }).afterClosed().pipe(
      map(result => result.submitted ? new DeleteAllResponsesAction(action.formId) : new ShowDeleteAllResponsesCanceledAction())),
    ),
  ));

   deleteAllResponses$ = createEffect(() => this.actions$.pipe(
    ofType<DeleteAllResponsesAction>(FormsActionTypes.DELETE_ALL_RESPONSES),
    switchMap(action => this.formsService.deleteAllResponses(action.formId).pipe(
      map(data => new DeleteAllResponsesCompleteAction()),
      catchError(err => of(new DeleteAllResponsesFailedAction(transformErrorResponse(err)))))),
  ));

   deleteResponse$ = createEffect(() => this.actions$.pipe(
    ofType<DeleteResponseAction>(FormsActionTypes.DELETE_RESPONSE),
    switchMap(action => this.matDialog.open(SimpleDialogComponent, {
      data: {
        ok: this.translate.instant('oca.Yes'),
        message: this.translate.instant('oca.confirm_delete_response'),
        title: this.translate.instant('oca.confirm_deletion'),
        cancel: this.translate.instant('oca.No'),
      },
    } as MatDialogConfig<SimpleDialogData>).afterClosed().pipe(
      switchMap(result => {
        if (result.submitted) {
          return this.formsService.deleteResponse(action.payload.formId, action.payload.submissionId).pipe(
            map(() => new DeleteResponseCompleteAction(action.payload)),
            catchError(err => of(new DeleteResponseFailedAction(transformErrorResponse(err)))));
        } else {
          return of(new DeleteResponseCanceledAction(action.payload));
        }
      }),
    ))));

   copyForm$ = createEffect(() => this.actions$.pipe(
    ofType<CopyFormAction>(FormsActionTypes.COPY_FORM),
    switchMap(() => this.store.pipe(select(getForm), first())),
    switchMap(form => this.formsService.copyForm(form.data as OcaForm).pipe(
      map(data => new CopyFormCompleteAction(data)),
      tap(() => this.snackbar.open(this.translate.instant('oca.form_copied'), this.translate.instant('oca.ok'), { duration: 3000 })),
      catchError(err => of(new CopyFormFailedAction(transformErrorResponse(err)))))),
  ));

   getResponses$ = createEffect(() => this.actions$.pipe(
    ofType<GetResponsesAction>(FormsActionTypes.GET_RESPONSES),
    switchMap(action => this.formsService.getResponses(action.payload).pipe(
      map(data => new GetResponsesCompleteAction(data)),
      catchError(err => of(new GetResponsesFailedAction(transformErrorResponse(err)))))),
  ));

   getNextResponse$ = createEffect(() => this.actions$.pipe(
    ofType<GetNextResponseAction>(FormsActionTypes.GET_NEXT_RESPONSE),
    switchMap(action => this.store.pipe(select(getResponsesData), first(), map(data => ({ data, action })))),
    switchMap(thing => {
      const { data, action } = thing;
      if (action.payload.responseId) {
        return of(new GetResponseAction({ id: action.payload.responseId }));
      } else {
        return of(new GetResponsesAction({ formId: action.payload.formId, page_size: 5, cursor: data.cursor as string }, false));
      }
    }),
  ));

   getIntegrations$ = createEffect(() => this.actions$.pipe(
    startWith(new GetIntegrationsAction()),
    ofType<GetIntegrationsAction>(FormsActionTypes.GET_INTEGRATIONS),
    switchMap(() => this.formsService.getIntegrations().pipe(
      map(data => new GetIntegrationsCompleteAction(data)),
      catchError(err => of(new GetIntegrationsFailedAction(transformErrorResponse(err)))))),
  ));

   updateIntegration$ = createEffect(() => this.actions$.pipe(
    ofType<UpdateIntegrationAction>(FormsActionTypes.UPDATE_INTEGRATION),
    switchMap(action => this.formsService.updateIntegration(action.payload).pipe(
      map(data => new UpdateIntegrationCompleteAction(data)),
      catchError(err => of(new UpdateIntegrationFailedAction(transformErrorResponse(err)))))),
  ));

   downloadResponses$ = createEffect(() => this.actions$.pipe(
    ofType(FormsActionTypes.DOWNLOAD_RESPONSES),
    tap(() => this.snackbar.open(this.translate.instant('oca.downloading_responses_pls_wait'), undefined, { duration: 10000 })),
    switchMap(action => this.formsService.downloadResponses(action.payload.id).pipe(
      map(data => new DownloadResponsesCompleteAction(data)),
      tap(a => window.open(a.payload.url, '_blank')),
      catchError(err => of(new DownloadResponsesFailedAction(transformErrorResponse(err)))))),
  ));

  constructor(private actions$: Actions<FormsActions>,
              private store: Store<FormsState>,
              private formsService: FormsService,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private errorService: ErrorService,
              private router: Router,
              private matDialog: MatDialog) {
  }
}
