import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { RogerthatService } from '@oca/rogerthat';
import { of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { ErrorService } from './error.service';
import { TimeblockrDynamicField, TimeblockrLocation, TimeblockrProduct, TimeblockrDateSlot } from './timeblockr';
import {
  loadAppointments,
  loadAppointmentsFailure,
  loadAppointmentsSuccess, loadDynamicFields, loadDynamicFieldsFailure, loadDynamicFieldsSuccess,
  loadLocations,
  loadLocationsFailure,
  loadLocationsSuccess,
  loadProducts,
  loadProductsFailure,
  loadProductsSuccess,
  loadTimeslots,
  loadTimeslotsFailure,
  loadTimeslotsOnDay,
  loadTimeslotsOnDayFailure,
  loadTimeslotsOnDaySuccess,
  loadTimeslotsSuccess,
} from './timeblockr.actions';

export const enum TimeblockrApiMethod {
  GET_APPOINTMENTS = 'integrations.timeblockr.get_appointments',
  GET_PRODUCTS = 'integrations.timeblockr.get_products',
  GET_LOCATIONS = 'integrations.timeblockr.get_locations',
  GET_TIMESLOTS = 'integrations.timeblockr.get_timeslots',
  GET_DYNAMIC_FIELDS = 'integrations.timeblockr.get_dynamic_fields',
  BOOK_APPOINTMENT = 'integrations.timeblockr.book_appointment',
}

@Injectable({providedIn: 'root'})
export class TimeblockrEffects {

  // loadAppointments$ = createEffect(() => this.actions$.pipe(
  //   ofType(loadAppointments),
  //   switchMap(action => this.rogerthatService.apiCall(TimeblockrApiMethod.GET_APPOINTMENTS).pipe(
  //     map(data => loadAppointmentsSuccess({ data })),
  //     catchError(err => {
  //       this.errorService.showErrorDialog(action, err);
  //       return of(loadAppointmentsFailure({error: err}));
  //     }),
  //   ))));

  loadProducts$ = createEffect(() => this.actions$.pipe(
    ofType(loadProducts),
    switchMap(action => this.rogerthatService.apiCall<TimeblockrProduct[]>(TimeblockrApiMethod.GET_PRODUCTS, action.data).pipe(
      map(data => loadProductsSuccess({ data })),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(loadProductsFailure({error: err}));
      }),
    ))));

  loadLocations$ = createEffect(() => this.actions$.pipe(
    ofType(loadLocations),
    switchMap(action => this.rogerthatService.apiCall<TimeblockrLocation[]>(TimeblockrApiMethod.GET_LOCATIONS).pipe(
      map(data => loadLocationsSuccess({ data })),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(loadLocationsFailure({error: err}));
      }),
    ))));

  loadTimeslots$ = createEffect(() => this.actions$.pipe(
    ofType(loadTimeslots),
    switchMap(action => this.rogerthatService.apiCall<TimeblockrDateSlot[]>(TimeblockrApiMethod.GET_TIMESLOTS, action.data).pipe(
      map(data => loadTimeslotsSuccess({ data })),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(loadTimeslotsFailure({error: err}));
      }),
    ))));

  loadTimeslotOnDaysOnDay$ = createEffect(() => this.actions$.pipe(
    ofType(loadTimeslotsOnDay),
    switchMap(action => this.rogerthatService.apiCall<TimeblockrDateSlot[]>(TimeblockrApiMethod.GET_TIMESLOTS, action.data).pipe(
      map(data => loadTimeslotsOnDaySuccess({ data })),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(loadTimeslotsOnDayFailure({error: err}));
      }),
    ))));

  loadDynamicFields$ = createEffect(() => this.actions$.pipe(
    ofType(loadDynamicFields),
    switchMap(action => this.rogerthatService.apiCall<TimeblockrDynamicField[]>(TimeblockrApiMethod.GET_DYNAMIC_FIELDS, action.data).pipe(
      map(data => loadDynamicFieldsSuccess({ data })),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(loadDynamicFieldsFailure({error: err}));
      }),
    ))));

  constructor(protected actions$: Actions,
              private rogerthatService: RogerthatService,
              private errorService: ErrorService) {
  }

}
