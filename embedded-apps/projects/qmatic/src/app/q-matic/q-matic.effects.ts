import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController } from '@ionic/angular';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { RogerthatService } from '@oca/rogerthat';
import { of } from 'rxjs';
import { catchError, map, skipWhile, switchMap, take, tap, withLatestFrom } from 'rxjs/operators';
import { ErrorService } from '../error.service';
import { QMState } from '../reducers';
import { Appointment, ListAppointments, ListBranches, ListDates, ListServices, ListTimes, QmaticClientSettings } from './appointments';
import {
  CancelAppointmentAction,
  CancelAppointmentFailedAction,
  CancelAppointmentSuccessAction,
  ConfirmAppointmentAction,
  ConfirmAppointmentFailedAction,
  ConfirmAppointmentSuccessAction,
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
  GetSettingsAction,
  GetSettingsFailedAction,
  GetSettingsSuccessAction,
  GetTimesAction,
  GetTimesFailedAction,
  GetTimesSuccessAction,
  QMaticActions,
  QMaticActionTypes,
  ReserveDateAction,
  ReserveDateFailedAction,
  ReserveDateSuccessAction,
} from './q-matic-actions';
import { getClientSettings } from './q-matic.state';

export const ApiCalls = {
  APPOINTMENTS: 'integrations.qmatic.appointments',
  SERVICES: 'integrations.qmatic.services',
  BRANCHES: 'integrations.qmatic.branches',
  DATES: 'integrations.qmatic.dates',
  TIMES: 'integrations.qmatic.times',
  RESERVE: 'integrations.qmatic.reserve',
  CONFIRM: 'integrations.qmatic.confirm',
  DELETE: 'integrations.qmatic.delete',
  GET_SETTINGS: 'integrations.qmatic.settings',
};

@Injectable()
export class QMaticEffects {
   getAppointments$ = createEffect(() => this.actions$.pipe(
    ofType<GetAppointmentsAction>(QMaticActionTypes.GET_APPOINTMENTS),
    switchMap(action => this.rogerthatService.apiCall<ListAppointments>(ApiCalls.APPOINTMENTS).pipe(
      map(result => new GetAppointmentsSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetAppointmentsFailedAction(err));
      })),
    )));

   getServices$ = createEffect(() => this.actions$.pipe(
    ofType<GetServicesAction>(QMaticActionTypes.GET_SERVICES),
    switchMap(action => this.rogerthatService.apiCall<ListServices>(ApiCalls.SERVICES, action.payload).pipe(
      map(result => new GetServicesSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetServicesFailedAction(err));
      })),
    )));

   getBranches$ = createEffect(() => this.actions$.pipe(
    ofType<GetBranchesAction>(QMaticActionTypes.GET_BRANCHES),
    switchMap(action => this.rogerthatService.apiCall<ListBranches>(ApiCalls.BRANCHES, action.payload).pipe(
      map(result => new GetBranchesSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetBranchesFailedAction(err));
      })),
    )));

   getDates$ = createEffect(() => this.actions$.pipe(
    ofType<GetDatesAction>(QMaticActionTypes.GET_DATES),
    switchMap(action => this.rogerthatService.apiCall<ListDates>(ApiCalls.DATES, action.payload).pipe(
      map(result => new GetDatesSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetDatesFailedAction(err));
      })),
    )));

   getTimes$ = createEffect(() => this.actions$.pipe(
    ofType<GetTimesAction>(QMaticActionTypes.GET_TIMES),
    switchMap(action => this.rogerthatService.apiCall<ListTimes>(ApiCalls.TIMES, action.payload).pipe(
      map(result => new GetTimesSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetTimesFailedAction(err));
      })),
    )));

   reserveDate$ = createEffect(() => this.actions$.pipe(
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
        this.errorService.showErrorDialog(action, err);
        return of(new ReserveDateFailedAction(err));
      })),
    )));

   confirmAppointment$ = createEffect(() => this.actions$.pipe(
    ofType<ConfirmAppointmentAction>(QMaticActionTypes.CONFIRM_APPOINTMENT),
    switchMap(action => this.rogerthatService.apiCall<Appointment>(ApiCalls.CONFIRM, action.payload).pipe(
      map(result => new ConfirmAppointmentSuccessAction(result)),
      tap(() => this.router.navigate(['/appointments'])),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new ConfirmAppointmentFailedAction(err));
      })),
    )));

   cancelAppointment$ = createEffect(() => this.actions$.pipe(
    ofType<CancelAppointmentAction>(QMaticActionTypes.CANCEL_APPOINTMENT),
    switchMap(action => this.rogerthatService.apiCall<null>(ApiCalls.DELETE, action.payload).pipe(
      map(() => new CancelAppointmentSuccessAction(action.payload)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new CancelAppointmentFailedAction(err));
      })),
    )));

  getSettings$ = createEffect(() => this.actions$.pipe(
    ofType<GetSettingsAction>(QMaticActionTypes.GET_SETTINGS),
    withLatestFrom(this.store.pipe(select(getClientSettings))),
    skipWhile(([, settings]) => settings !== null),
    switchMap(([action]) => this.rogerthatService.apiCall<QmaticClientSettings>(ApiCalls.GET_SETTINGS).pipe(
      map(result => new GetSettingsSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetSettingsFailedAction(err));
      })),
    )));

  constructor(protected actions$: Actions<QMaticActions>,
              protected store: Store<QMState>,
              protected alertController: AlertController,
              protected translate: TranslateService,
              protected router: Router,
              protected rogerthatService: RogerthatService,
              protected errorService: ErrorService) {
  }

  private async showDialog(message: string) {
    const dialog = await this.alertController.create({
      message, buttons: [
        { text: this.translate.instant('app.qm.close') },
      ],
    });
    await dialog.present();
  }
}
