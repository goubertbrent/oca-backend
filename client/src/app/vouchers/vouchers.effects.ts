import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { ErrorService } from '../shared/errors/error.service';
import {
  ExportVoucherServicesAction,
  ExportVoucherServicesFailedAction,
  ExportVoucherServicesSuccessAction,
  GetServicesAction,
  GetServicesFailedAction,
  GetServicesSuccessAction,
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
    switchMap(action => this.service.getServices(action.payload.organizationType, action.payload.cursor, action.payload.pageSize).pipe(
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

  constructor(private actions$: Actions<VouchersActions>,
              private errorService: ErrorService,
              private service: VouchersService) {

  }

}
