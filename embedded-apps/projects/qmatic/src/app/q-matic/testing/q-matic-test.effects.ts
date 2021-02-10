import { Injectable } from '@angular/core';
import { createEffect, ofType } from '@ngrx/effects';
import { of } from 'rxjs';
import { delay, map, switchMap, tap } from 'rxjs/operators';
import { QMaticRequiredField } from '../appointments';
import {
  CancelAppointmentAction,
  CancelAppointmentSuccessAction,
  ConfirmAppointmentAction,
  ConfirmAppointmentSuccessAction,
  GetAppointmentsAction,
  GetAppointmentsSuccessAction,
  GetBranchesAction,
  GetBranchesSuccessAction,
  GetDatesAction,
  GetDatesSuccessAction,
  GetServicesAction,
  GetServicesSuccessAction,
  GetSettingsSuccessAction,
  GetTimesAction,
  GetTimesSuccessAction,
  QMaticActionTypes,
  ReserveDateAction,
  ReserveDateSuccessAction,
} from '../q-matic-actions';
import { QMaticEffects } from '../q-matic.effects';
import {
  confirmReservationResult,
  getAppointmentsResult,
  getBranchesResult,
  getDatesResult,
  getServicesResult,
  getTimesResult,
  reserveDateResult,
} from './data';

function randint(min: number, max: number): number {
  return Math.round(Math.random() * (max - min)) + min;
}

@Injectable()
export class QMaticTestEffects extends QMaticEffects {
  getAppointments$ = createEffect(() => this.actions$.pipe(
    ofType<GetAppointmentsAction>(QMaticActionTypes.GET_APPOINTMENTS),
    delay(randint(50, 500)),  // artificial network delay
    switchMap(() => of(new GetAppointmentsSuccessAction(getAppointmentsResult)),
    )));

  getServices$ = createEffect(() => this.actions$.pipe(
    ofType<GetServicesAction>(QMaticActionTypes.GET_SERVICES),
    delay(randint(50, 500)),
    switchMap(() => of(new GetServicesSuccessAction(getServicesResult))),
  ));

  getBranches$ = createEffect(() => this.actions$.pipe(
    ofType<GetBranchesAction>(QMaticActionTypes.GET_BRANCHES),
    delay(randint(50, 500)),
    switchMap(() => of(new GetBranchesSuccessAction(getBranchesResult)),
    )));

  getDates$ = createEffect(() => this.actions$.pipe(
    ofType<GetDatesAction>(QMaticActionTypes.GET_DATES),
    delay(randint(50, 500)),
    switchMap(() => of(new GetDatesSuccessAction(getDatesResult)),
    )));

  getTimes$ = createEffect(() => this.actions$.pipe(
    ofType<GetTimesAction>(QMaticActionTypes.GET_TIMES),
    delay(randint(50, 500)),
    switchMap(() => of(new GetTimesSuccessAction(getTimesResult)),
    )));

  reserveDate$ = createEffect(() => this.actions$.pipe(
    ofType<ReserveDateAction>(QMaticActionTypes.RESERVE_DATE),
    delay(randint(50, 500)),
    switchMap(action => of(new ReserveDateSuccessAction(reserveDateResult)).pipe(
      tap(result => this.store.dispatch(new ConfirmAppointmentAction({
        reservation_id: result.payload.publicId,
        notes: action.payload.notes,
        title: action.payload.title,
        customer: action.payload.customer,
      }))),
    )),
  ));

  confirmAppointment$ = createEffect(() => this.actions$.pipe(
    ofType<ConfirmAppointmentAction>(QMaticActionTypes.CONFIRM_APPOINTMENT),
    switchMap(action => of(new ConfirmAppointmentSuccessAction(confirmReservationResult)).pipe(
      tap(() => this.router.navigate(['/appointments'])),
    ))));

  cancelAppointment$ = createEffect(() => this.actions$.pipe(
    ofType<CancelAppointmentAction>(QMaticActionTypes.CANCEL_APPOINTMENT),
    switchMap(action => of(new CancelAppointmentSuccessAction(action.payload)),
    )));

  getSettings$ = createEffect(() => of({}).pipe(
    map(() => new GetSettingsSuccessAction({
      required_fields: [QMaticRequiredField.PHONE_NUMBER, QMaticRequiredField.EMAIL],
      show_product_info: true,
    })),
  ));
}
