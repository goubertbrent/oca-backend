import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { ErrorService } from '@oca/web-shared';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import {
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
  VouchersActions,
  VouchersActionTypes,
} from './vouchers.actions';
import { VouchersService } from './vouchers.service';


@Injectable()
export class VouchersEffects {

  loadServices$ = createEffect(() => this.actions$.pipe(
    ofType<GetServicesAction>(VouchersActionTypes.GET_SERVICES),
    switchMap(action => this.service.getServices().pipe(
      map(result => new GetServicesSuccessAction(result)),
      catchError(err => this.errorService.handleError(action, GetServicesFailedAction, err)))),
  ));

  whitelistVoucherSerivce$ = createEffect(() => this.actions$.pipe(
    ofType<WhitelistVoucherServiceAction>(VouchersActionTypes.WHITELIST_VOUCHER_SERVICE),
    switchMap(action => this.service.whitelistVoucherService(action.payload.id, action.payload.email, action.payload.accepted).pipe(
      map(result => new WhitelistVoucherServiceSuccessAction({
        id: action.payload.id,
        email: action.payload.email,
        service: result,
      })),
      catchError(err => this.errorService.handleError(action, WhitelistVoucherServiceFailedAction, err)))),
  ));

  getCirkloSettings$ = createEffect(() => this.actions$.pipe(
    ofType<GetCirkloSettingsAction>(VouchersActionTypes.GET_CIRKLO_SETTINGS),
    switchMap(action => this.service.getCirkloSettings().pipe(
      map(result => new GetCirkloSettingsCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetCirkloSettingsFailedAction, err)))),
  ));

  saveCirkloSettings$ = createEffect(() => this.actions$.pipe(
    ofType<SaveCirkloSettingsAction>(VouchersActionTypes.SAVE_CIRKLO_SETTINGS),
    switchMap(action => this.service.saveCirkloSettings(action.payload).pipe(
      map(result => new SaveCirkloSettingsCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, SaveCirkloSettingsFailedAction, err)))),
  ));

  constructor(private actions$: Actions<VouchersActions>,
              private errorService: ErrorService,
              private service: VouchersService) {

  }

}
