import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController } from '@ionic/angular';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { AppState } from '../reducers';
import { RogerthatService } from '../rogerthat/rogerthat.service';
import { Appointment, ListAppointments, ListBranches, ListDates, ListServices, ListTimes } from './appointments';
import {
  CancelAppointmentAction,
  CancelAppointmentFailedAction,
  CancelAppointmentSuccessAction,
  ConfirmAppointmentAction,
  ConfirmAppointmentFailedAction,
  ConfirmAppointmentSuccessAction,
  CreateIcalAction,
  CreateIcalFailedAction,
  CreateIcalSuccessAction,
  GetAppointmentsAction,
  GetAppointmentsFailedAction,
  GetAppointmentsSuccessAction,
  GetBranchesAction,
  GetBranchesFailedAction,
  GetBranchesSuccessAction,
  GetDatesAction,
  GetDatesFailedAction,
  GetDatesSuccessAction,
  GetServicesAction,
  GetServicesFailedAction,
  GetServicesSuccessAction,
  GetTimesAction,
  GetTimesFailedAction,
  GetTimesSuccessAction,
  QMaticActions,
  QMaticActionTypes,
  ReserveDateAction,
  ReserveDateFailedAction,
  ReserveDateSuccessAction,
} from './q-matic-actions';

const ApiCalls = {
  APPOINTMENTS: 'integrations.qmatic.appointments',
  SERVICES: 'integrations.qmatic.services',
  BRANCHES: 'integrations.qmatic.branches',
  DATES: 'integrations.qmatic.dates',
  TIMES: 'integrations.qmatic.times',
  RESERVE: 'integrations.qmatic.reserve',
  CONFIRM: 'integrations.qmatic.confirm',
  DELETE: 'integrations.qmatic.delete',
  CREATE_ICAL: 'integrations.qmatic.create_ical',
};

@Injectable()
export class QMaticEffects {
  @Effect() getAppointments$ = this.actions$.pipe(
    ofType<GetAppointmentsAction>(QMaticActionTypes.GET_APPOINTMENTS),
    switchMap(action => this.rogerthatService.apiCall<ListAppointments>(ApiCalls.APPOINTMENTS).pipe(
      map(result => new GetAppointmentsSuccessAction(result)),
      catchError(err => {
        this.showErrorDialog(action, err);
        return of(new GetAppointmentsFailedAction(err));
      })),
    ));

  @Effect() getServices$ = this.actions$.pipe(
    ofType<GetServicesAction>(QMaticActionTypes.GET_SERVICES),
    switchMap(action => this.rogerthatService.apiCall<ListServices>(ApiCalls.SERVICES).pipe(
      map(result => new GetServicesSuccessAction(result)),
      catchError(err => {
        this.showErrorDialog(action, err);
        return of(new GetServicesFailedAction(err));
      })),
    ));

  @Effect() getBranches$ = this.actions$.pipe(
    ofType<GetBranchesAction>(QMaticActionTypes.GET_BRANCHES),
    switchMap(action => this.rogerthatService.apiCall<ListBranches>(ApiCalls.BRANCHES, action.payload).pipe(
      map(result => new GetBranchesSuccessAction(result)),
      catchError(err => {
        this.showErrorDialog(action, err);
        return of(new GetBranchesFailedAction(err));
      })),
    ));

  @Effect() getDates$ = this.actions$.pipe(
    ofType<GetDatesAction>(QMaticActionTypes.GET_DATES),
    switchMap(action => this.rogerthatService.apiCall<ListDates>(ApiCalls.DATES, action.payload).pipe(
      map(result => new GetDatesSuccessAction(result)),
      catchError(err => {
        this.showErrorDialog(action, err);
        return of(new GetDatesFailedAction(err));
      })),
    ));

  @Effect() getTimes$ = this.actions$.pipe(
    ofType<GetTimesAction>(QMaticActionTypes.GET_TIMES),
    switchMap(action => this.rogerthatService.apiCall<ListTimes>(ApiCalls.TIMES, action.payload).pipe(
      map(result => new GetTimesSuccessAction(result)),
      catchError(err => {
        this.showErrorDialog(action, err);
        return of(new GetTimesFailedAction(err));
      })),
    ));

  @Effect() reserveDate$ = this.actions$.pipe(
    ofType<ReserveDateAction>(QMaticActionTypes.RESERVE_DATE),
    switchMap(action => this.rogerthatService.apiCall<Appointment>(ApiCalls.RESERVE, {
        service_id: action.payload.service_id,
        branch_id: action.payload.branch_id,
        date: action.payload.date,
        time: action.payload.time,
      }).pipe(
      map(result => new ReserveDateSuccessAction(result)),
      tap(result => this.store.dispatch(new ConfirmAppointmentAction({
        reservation_id: result.payload.publicId,
        notes: action.payload.notes,
        title: action.payload.title,
        customer: action.payload.customer,
      }))),
      catchError(err => {
        this.showErrorDialog(action, err);
        return of(new ReserveDateFailedAction(err));
      })),
    ));

  @Effect() confirmAppointment$ = this.actions$.pipe(
    ofType<ConfirmAppointmentAction>(QMaticActionTypes.CONFIRM_APPOINTMENT),
    switchMap(action => this.rogerthatService.apiCall<Appointment>(ApiCalls.CONFIRM, action.payload).pipe(
      map(result => new ConfirmAppointmentSuccessAction(result)),
      tap(() => this.router.navigate(['/q-matic', 'appointments'])),
      catchError(err => {
        this.showErrorDialog(action, err);
        return of(new ConfirmAppointmentFailedAction(err));
      })),
    ));

  @Effect() cancelAppointment$ = this.actions$.pipe(
    ofType<CancelAppointmentAction>(QMaticActionTypes.CANCEL_APPOINTMENT),
    switchMap(action => this.rogerthatService.apiCall<null>(ApiCalls.DELETE, action.payload).pipe(
      map(() => new CancelAppointmentSuccessAction(action.payload)),
      catchError(err => {
        this.showErrorDialog(action, err);
        return of(new CancelAppointmentFailedAction(err));
      })),
    ));

  @Effect() createIcal$ = this.actions$.pipe(
    ofType<CreateIcalAction>(QMaticActionTypes.CREATE_ICAL),
    switchMap(action => this.rogerthatService.apiCall<{ message: string }>(ApiCalls.CREATE_ICAL, action.payload).pipe(
      map(result => new CreateIcalSuccessAction(result)),
      tap(result => {
        this.showDialog(result.payload.message);
      }),
      catchError(err => {
        this.showErrorDialog(action, err);
        return of(new CreateIcalFailedAction(err));
      })),
    ));

  constructor(private actions$: Actions<QMaticActions>,
              private store: Store<AppState>,
              private alertController: AlertController,
              private translate: TranslateService,
              private router: Router,
              private rogerthatService: RogerthatService) {
  }

  private async showDialog(message: string) {
    const dialog = await this.alertController.create({
      message, buttons: [
        { text: this.translate.instant('app.oca.close') },
      ],
    });
    await dialog.present();
  }

  private async showErrorDialog(failedAction: QMaticActions, error: any) {
    let errorMessage: string;
    if (typeof error === 'string') {
      errorMessage = error;
    } else {
      errorMessage = this.translate.instant('app.oca.unknown_error');
    }
    const top = await this.alertController.getTop();
    if (top) {
      await top.dismiss();
    }
    const dialog = await this.alertController.create({
      header: this.translate.instant('app.oca.error'),
      message: errorMessage,
      buttons: [
        {
          text: this.translate.instant('app.oca.close'),
          role: 'cancel',
        },
        {
          text: this.translate.instant('app.oca.retry'),
          handler: () => {
            this.store.dispatch(failedAction);
          },
        },
      ],
    });
    await dialog.present();
  }
}
