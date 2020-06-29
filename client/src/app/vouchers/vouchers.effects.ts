import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { ErrorService } from '../shared/errors/error.service';
import {
  ExportVoucherServicesAction,
  ExportVoucherServicesFailedAction,
  ExportVoucherServicesSuccessAction,
  GetCirkloSettingsAction,
  GetCirkloSettingsCompleteAction,
  GetCirkloSettingsFailedAction,
  GetServicesAction,
  GetServicesFailedAction,
  GetServicesSuccessAction,
  SaveCirkloSettingsAction,
  SaveCirkloSettingsCompleteAction,
  SaveCirkloSettingsFailedAction,
  SaveVoucherSettingsAction,
  SaveVoucherSettingsFailedAction,
  SaveVoucherSettingsSuccessAction,
  VouchersActions,
  VouchersActionTypes,
} from './vouchers.actions';
import { VouchersService } from './vouchers.service';


@Injectable()
export class VouchersEffects {

  loadServices$ = createEffect(() => this.actions$.pipe(
    ofType<GetServicesAction>(VouchersActionTypes.GET_SERVICES),
    switchMap(action => this.service.getServices(action.payload.organizationType, action.payload.cursor, action.payload.pageSize,
      action.payload.sort).pipe(
      map(result => new GetServicesSuccessAction(result)),
      catchError(err => this.errorService.handleError(action, GetServicesFailedAction, err)))),
  ));

  saveVoucherProvider$ = createEffect(() => this.actions$.pipe(
    ofType<SaveVoucherSettingsAction>(VouchersActionTypes.SAVE_VOUCHER_PROVIDER),
    switchMap(action => this.service.saveProvider(action.payload.serviceEmail, action.payload.providers).pipe(
      map(result => new SaveVoucherSettingsSuccessAction({
        serviceEmail: action.payload.serviceEmail,
        service: result,
      })),
      catchError(err => this.errorService.handleError(action, SaveVoucherSettingsFailedAction, err)))),
  ));

  exportServices$ = createEffect(() => this.actions$.pipe(
    ofType<ExportVoucherServicesAction>(VouchersActionTypes.EXPORT_VOUCHER_SERVICES),
    switchMap(action => this.service.exportServices().pipe(
      map(result => new ExportVoucherServicesSuccessAction(result)),
      tap(result => window.open(result.payload.url)),
      catchError(err => this.errorService.handleError(action, ExportVoucherServicesFailedAction, err)))),
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
