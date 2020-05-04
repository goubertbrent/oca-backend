import { Injectable } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { combineLatest } from 'rxjs';
import { catchError, distinctUntilChanged, filter, map, switchMap, tap } from 'rxjs/operators';
import { RootState } from '../reducers';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '../shared/dialog/simple-dialog.component';
import { ErrorService } from '../shared/errors/error.service';
import { filterNull } from '../shared/util';
import { JobStatus } from './jobs';
import {
  CreateJobOfferAction,
  CreateJobOfferCompleteAction,
  CreateJobOfferFailedAction,
  GetJobOfferAction,
  GetJobOfferCompleteAction,
  GetJobOfferFailedAction,
  GetJobOfferListAction,
  GetJobOfferListCompleteAction,
  GetJobOfferListFailedAction,
  GetJobSettingsAction,
  GetJobSettingsCompleteAction,
  GetJobSettingsFailedAction,
  GetSolicitationMessagesAction,
  GetSolicitationMessagesCompleteAction,
  GetSolicitationMessagesFailedAction,
  GetSolicitationsAction,
  GetSolicitationsCompleteAction,
  GetSolicitationsFailedAction,
  JobsActions,
  JobsActionTypes,
  NewJobSolicitationMessageReceivedAction,
  SendSolicitationMessageAction,
  SendSolicitationMessageCompleteAction,
  SendSolicitationMessageFailedAction,
  UpdateJobOfferAction,
  UpdateJobOfferCompleteAction,
  UpdateJobOfferFailedAction,
  UpdateJobSettingsAction,
  UpdateJobSettingsCompleteAction,
  UpdateJobSettingsFailedAction,
} from './jobs.actions';
import { JobsService } from './jobs.service';
import { getCurrentJobId, getCurrentSolicitationId } from './jobs.state';

@Injectable({ providedIn: 'root' })
export class JobsEffects {
  @Effect() getJobOffers$ = this.actions$.pipe(
    ofType<GetJobOfferListAction>(JobsActionTypes.GET_JOB_OFFER_LIST),
    switchMap(action => this.service.getJobOffersList().pipe(
      map(result => new GetJobOfferListCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetJobOfferListFailedAction, err)))),
  );

  @Effect() getJobOffer$ = this.actions$.pipe(
    ofType<GetJobOfferAction>(JobsActionTypes.GET_JOB_OFFER),
    switchMap(action => this.service.getJobOffer(action.payload.jobId).pipe(
      map(result => new GetJobOfferCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetJobOfferFailedAction, err)))),
  );

  @Effect() createJobOffer$ = this.actions$.pipe(
    ofType<CreateJobOfferAction>(JobsActionTypes.CREATE_JOB_OFFER),
    switchMap(action => this.service.createJobOffer(action.payload).pipe(
      map(result => new CreateJobOfferCompleteAction(result)),
      tap(successAction => this.router.navigateByUrl(`/jobs/${successAction.payload.offer.id}`)),
      catchError(err => this.errorService.handleError(action, CreateJobOfferFailedAction, err)))),
  );

  @Effect({ dispatch: false }) afterJobOfferCreated$ = this.actions$.pipe(
    ofType<CreateJobOfferCompleteAction>(JobsActionTypes.CREATE_JOB_OFFER_COMPLETE),
    map(() => {
      this.service.getJobsSettings().subscribe(result => {
        if (result.emails.length === 0) {
          this.showSettingsDialog();
        }
      });
    }),
  );

  @Effect() updateJobOffer$ = this.actions$.pipe(
    ofType<UpdateJobOfferAction>(JobsActionTypes.UPDATE_JOB_OFFER),
    switchMap(action => this.service.updateJobOffer(action.payload.id, action.payload.offer).pipe(
      map(result => new UpdateJobOfferCompleteAction(result)),
      tap(updateAction => {
        if (updateAction.payload.offer.status === JobStatus.DELETED) {
          this.router.navigateByUrl('/jobs');
        } else {
          this.snackbar.open(this.translate.instant('oca.job_updated'), this.translate.instant('oca.Close'), { duration: 5000 });
        }
      }),
      catchError(err => this.errorService.handleError(action, UpdateJobOfferFailedAction, err)))),
  );

  @Effect() getSolicitations$ = this.actions$.pipe(
    ofType<GetSolicitationsAction>(JobsActionTypes.GET_SOLICITATIONS),
    switchMap(action => this.service.getJobSolicitations(action.payload.jobId).pipe(
      map(result => new GetSolicitationsCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetSolicitationsFailedAction, err)))),
  );

  @Effect() getJobSolicitationMessages$ = this.actions$.pipe(
    ofType<GetSolicitationMessagesAction>(JobsActionTypes.GET_SOLICITATION_MESSAGES),
    switchMap(action => this.service.getSolicitationMessages(action.payload.jobId, action.payload.solicitationId).pipe(
      map(result => new GetSolicitationMessagesCompleteAction({ solicitationId: action.payload.solicitationId, messages: result })),
      catchError(err => this.errorService.handleError(action, GetSolicitationMessagesFailedAction, err)))),
  );

  @Effect() sendSolicitationMessage$ = this.actions$.pipe(
    ofType<SendSolicitationMessageAction>(JobsActionTypes.SEND_SOLICITATION_MESSAGE),
    switchMap(({ payload }) => this.service.sendSolicitationMessage(payload.jobId, payload.solicitationId, payload.message).pipe(
      map(result => new SendSolicitationMessageCompleteAction({ solicitationId: payload.solicitationId, message: result })),
      catchError(e => this.errorService.handleError(new SendSolicitationMessageAction(payload), SendSolicitationMessageFailedAction, e)),
    )),
  );

  @Effect() getJobSettings$ = this.actions$.pipe(
    ofType<GetJobSettingsAction>(JobsActionTypes.GET_JOBS_SETTINGS),
    switchMap(action => this.service.getJobsSettings().pipe(
      map(result => new GetJobSettingsCompleteAction(result)),
      catchError(e => this.errorService.handleError(action, GetJobSettingsFailedAction, e)),
    )),
  );

  @Effect() updateJobSettings$ = this.actions$.pipe(
    ofType<UpdateJobSettingsAction>(JobsActionTypes.UPDATE_JOBS_SETTINGS),
    switchMap(action => this.service.updateJobsSettings(action.payload).pipe(
      map(result => new UpdateJobSettingsCompleteAction(result)),
      tap(() => this.snackbar.open(this.translate.instant('oca.settings_saved'), undefined, { duration: 5000 })),
      catchError(e => this.errorService.handleError(action, UpdateJobSettingsFailedAction, e)),
    )),
  );

  @Effect({ dispatch: false }) newSolicitationMessageReceived$ = this.actions$.pipe(
    ofType<NewJobSolicitationMessageReceivedAction>(JobsActionTypes.NEW_SOLICITATION_MESSAGE_RECEIVED),
    filter(action => !action.payload.solicitation.last_message.reply),  // Filter messages sent by ourselves
    tap(({ payload }) => {
      const msg = this.translate.instant('oca.new_job_message');
      const button = this.translate.instant('oca.View');
      this.snackbar.open(msg, button, { duration: 10000 }).onAction().subscribe(() => {
        this.router.navigateByUrl(`/jobs/${payload.jobId}/solicitations/${payload.solicitation.id}`);
      });
    }),
  );

  @Effect() onJobChanged$ = this.store.pipe(select(getCurrentJobId), filterNull()).pipe(
    distinctUntilChanged(),
    map(jobId => new GetJobOfferAction({ jobId })),
  );

  @Effect() onSolicitationIdChanged$ = combineLatest([
    this.store.pipe(select(getCurrentSolicitationId), filterNull()),
    this.store.pipe(select(getCurrentJobId), filterNull()),
  ]).pipe(
    distinctUntilChanged((previous, current) => previous[ 0 ] === current[ 0 ] && previous[ 1 ] === current[ 1 ]),
    map(([solicitationId, jobId]) => new GetSolicitationMessagesAction({ solicitationId, jobId })),
  );

  constructor(private actions$: Actions<JobsActions>,
              private store: Store<RootState>,
              private service: JobsService,
              private matDialog: MatDialog,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private errorService: ErrorService,
              private router: Router) {
  }

  private showSettingsDialog() {
    const config: MatDialogConfig<SimpleDialogData> = {
      data: {
        message: this.translate.instant('oca.you_havent_configured_job_notifications_yet'),
        ok: this.translate.instant('oca.Yes'), cancel: this.translate.instant('oca.No'),
      },
    };
    this.matDialog.open(SimpleDialogComponent, config).afterClosed().subscribe((dialogResult: SimpleDialogResult) => {
      if (dialogResult?.submitted) {
        this.router.navigateByUrl('/jobs/settings');
      }
    });
  }
}
