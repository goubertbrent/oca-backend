import { Injectable } from '@angular/core';
import { AlertController } from '@ionic/angular';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { from, of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { RogerthatService } from '@oca/rogerthat';
import { AddVoucherResponse, CirkloMerchantsList, CirkloVouchersList, VoucherTransactionsList } from './cirklo';
import {
  AddVoucherAction,
  AddVoucherFailedAction,
  AddVoucherSuccessAction,
  CirkloActionTypes,
  ConfirmDeleteVoucherAction,
  ConfirmDeleteVoucherCancelledAction,
  DeleteVoucherAction,
  DeleteVoucherFailedAction,
  DeleteVoucherSuccessAction,
  GetMerchantsAction,
  GetMerchantsCompleteAction,
  GetMerchantsFailedAction,
  GetVoucherTransactionsAction,
  GetVoucherTransactionsCompleteAction,
  LoadVouchersAction,
  LoadVouchersFailedAction,
  LoadVouchersSuccessAction,
} from './cirklo.actions';
import { ErrorService } from './error.service';

const ApiCalls = {
  GET_VOUCHERS: 'integrations.cirklo.getvouchers',
  ADD_VOUCHER: 'integrations.cirklo.addvoucher',
  DELETE_VOUCHER: 'integrations.cirklo.deletevoucher',
  GET_TRANSACTIONS: 'integrations.cirklo.gettransactions',
  GET_MERCHANTS: 'integrations.cirklo.getmerchants',
};

const CONFIRM_ROLE = 'confirm';

@Injectable()
export class CirkloEffects {

  loadVouchers$ = createEffect(() => this.actions$.pipe(
    ofType<LoadVouchersAction>(CirkloActionTypes.GET_VOUCHERS),
    switchMap(action => this.rogerthatService.apiCall<CirkloVouchersList>(ApiCalls.GET_VOUCHERS).pipe(
      map(payload => new LoadVouchersSuccessAction(payload)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new LoadVouchersFailedAction(err));
      })),
    ),
  ));

  addVoucher$ = createEffect(() => this.actions$.pipe(
    ofType<AddVoucherAction>(CirkloActionTypes.ADD_VOUCHER),
    switchMap(action => this.rogerthatService.apiCall<AddVoucherResponse>(ApiCalls.ADD_VOUCHER, action.payload).pipe(
      map(payload => new AddVoucherSuccessAction(payload)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new AddVoucherFailedAction(err));
      })),
    ),
  ));

  deleteConfirm$ = createEffect(() => this.actions$.pipe(
    ofType<ConfirmDeleteVoucherAction>(CirkloActionTypes.CONFIRM_DELETE_VOUCHER),
    switchMap(({ payload }) => from(this.showConfirmDialog(this.translate.instant('app.cirklo.confirm_delete_voucher'))).pipe(
      switchMap(promise => from(promise.onDidDismiss())),
      switchMap(result => {
        if (result.role === CONFIRM_ROLE) {
          return of(new DeleteVoucherAction(payload));
        } else {
          return of(new ConfirmDeleteVoucherCancelledAction(payload));
        }
      }),
      ),
    ),
  ));

  deleteVoucher$ = createEffect(() => this.actions$.pipe(
    ofType<DeleteVoucherAction>(CirkloActionTypes.DELETE_VOUCHER),
    switchMap(action => this.rogerthatService.apiCall(ApiCalls.DELETE_VOUCHER, action.payload).pipe(
      map(() => new DeleteVoucherSuccessAction(action.payload)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new DeleteVoucherFailedAction(err));
      })),
    ),
  ));

  getTransactions$ = createEffect(() => this.actions$.pipe(
    ofType<GetVoucherTransactionsAction>(CirkloActionTypes.GET_VOUCHER_TRANSACTIONS),
    switchMap(action => this.rogerthatService.apiCall<VoucherTransactionsList>(ApiCalls.GET_TRANSACTIONS, action.payload).pipe(
      map(result => new GetVoucherTransactionsCompleteAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetVoucherTransactionsCompleteAction(err));
      })),
    ),
  ));

  getMerchants$ = createEffect(() => this.actions$.pipe(
    ofType<GetMerchantsAction>(CirkloActionTypes.GET_MERCHANTS),
    switchMap(action => this.rogerthatService.apiCall<CirkloMerchantsList>(ApiCalls.GET_MERCHANTS, action.payload).pipe(
      map(result => new GetMerchantsCompleteAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetMerchantsFailedAction(err));
      })),
    ),
  ));

  constructor(protected actions$: Actions,
              private store: Store,
              private errorService: ErrorService,
              private translate: TranslateService,
              private alertController: AlertController,
              private rogerthatService: RogerthatService) {
  }

  private async showConfirmDialog(message: string) {
    const alert = await this.alertController.create({
      header: this.translate.instant('app.cirklo.confirmation'),
      message,
      buttons: [{
        text: this.translate.instant('app.cirklo.yes'),
        role: CONFIRM_ROLE,
      }, {
        text: this.translate.instant('app.cirklo.no'),
        role: 'cancel',
      }],
    });
    await alert.present();
    return alert;
  }

}
