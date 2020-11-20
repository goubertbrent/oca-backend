import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { ErrorService } from '@oca/web-shared';
import { catchError, distinctUntilChanged, map, switchMap } from 'rxjs/operators';
import {
  GetCirkloCities,
  GetCirkloCitiesComplete,
  GetCirkloCitiesFailed,
  GetCirkloSettingsAction,
  GetCirkloSettingsCompleteAction,
  GetCirkloSettingsFailedAction,
  GetServicesAction,
  GetServicesFailedAction,
  GetServicesSuccessAction,
  SaveCirkloSettingsAction,
  SaveCirkloSettingsCompleteAction,
  SaveCirkloSettingsFailedAction,
  WhitelistVoucherServiceAction,
  WhitelistVoucherServiceFailedAction,
  WhitelistVoucherServiceSuccessAction,
} from './vouchers.actions';
import { VouchersService } from './vouchers.service';


@Injectable()
export class VouchersEffects {

  loadServices$ = createEffect(() => this.actions$.pipe(
    ofType(GetServicesAction),
    switchMap(action => this.service.getServices().pipe(
      map(result => GetServicesSuccessAction({ payload: result })),
      catchError(err => this.errorService.handleError(action, GetServicesFailedAction, err)))),
  ));

  whitelistVoucherService$ = createEffect(() => this.actions$.pipe(
    ofType(WhitelistVoucherServiceAction),
    switchMap(action => this.service.whitelistVoucherService(action.id, action.email, action.accepted).pipe(
      map(result => WhitelistVoucherServiceSuccessAction({
        id: action.id,
        email: action.email,
        service: result,
      })),
      catchError(err => this.errorService.handleError(action, WhitelistVoucherServiceFailedAction, err)))),
  ));

  getCirkloSettings$ = createEffect(() => this.actions$.pipe(
    ofType(GetCirkloSettingsAction),
    switchMap(action => this.service.getCirkloSettings().pipe(
      map(result => GetCirkloSettingsCompleteAction({ payload: result })),
      catchError(err => this.errorService.handleError(action, GetCirkloSettingsFailedAction, err)))),
  ));

  saveCirkloSettings$ = createEffect(() => this.actions$.pipe(
    ofType(SaveCirkloSettingsAction),
    switchMap(action => this.service.saveCirkloSettings(action.payload).pipe(
      map(result => SaveCirkloSettingsCompleteAction({ payload: result })),
      catchError(err => this.errorService.handleError(action, SaveCirkloSettingsFailedAction, err)))),
  ));

  getCirkloCities$ = createEffect(() => this.actions$.pipe(
    ofType(GetCirkloCities),
    distinctUntilChanged((action1, action2) => action1.staging === action2.staging),
    switchMap(action => this.service.getCirkloCities(action.staging).pipe(
      map(result => GetCirkloCitiesComplete({ cities: result })),
      catchError(err => this.errorService.handleError(action, GetCirkloCitiesFailed, err)))),
  ));

  constructor(private actions$: Actions,
              private errorService: ErrorService,
              private service: VouchersService) {

  }

}
