import { Injectable } from '@angular/core';
import { createEffect, ofType } from '@ngrx/effects';
import { of } from 'rxjs';
import { delay, switchMap } from 'rxjs/operators';
import {
  loadDynamicFields,
  loadDynamicFieldsSuccess,
  loadLocations,
  loadLocationsSuccess,
  loadProducts,
  loadProductsSuccess,
  loadTimeslots,
  loadTimeslotsOnDay,
  loadTimeslotsOnDaySuccess,
  loadTimeslotsSuccess,
} from '../timeblockr.actions';
import { TimeblockrEffects } from '../timeblockr.effects';
import { dynamicFields, locations, products, timeslots, timeslotsOnDay } from './data';

function randint(min: number, max: number): number {
  return Math.round(Math.random() * (max - min)) + min;
}

@Injectable({providedIn: 'root'})
export class TimeblockrTestEffects extends TimeblockrEffects {

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
    delay(randint(50, 500)),  // artificial network delay
    switchMap(() => of(loadProductsSuccess({ data: products })),
    )));

  loadLocations$ = createEffect(() => this.actions$.pipe(
    ofType(loadLocations),
    delay(randint(50, 500)),  // artificial network delay
    switchMap(() => of(loadLocationsSuccess({ data: locations })),
    )));

  loadTimeslots$ = createEffect(() => this.actions$.pipe(
    ofType(loadTimeslots),
    delay(randint(50, 500)),  // artificial network delay
    switchMap(() => of(loadTimeslotsSuccess({ data: timeslots.PeriodOptions.map(p => ({ date: p.Date })) })),
    )));

  loadTimeslotOnDaysOnDay$ = createEffect(() => this.actions$.pipe(
    ofType(loadTimeslotsOnDay),
    delay(randint(50, 500)),  // artificial network delay
    switchMap(() => of(loadTimeslotsOnDaySuccess({ data: timeslotsOnDay.SlotOptions.map(s => ({ date: s.Date })) })),
    )));

  loadDynamicFields$ = createEffect(() => this.actions$.pipe(
    ofType(loadDynamicFields),
    delay(randint(50, 500)),  // artificial network delay
    switchMap(() => of(loadDynamicFieldsSuccess({ data: dynamicFields })),
    )));

}
