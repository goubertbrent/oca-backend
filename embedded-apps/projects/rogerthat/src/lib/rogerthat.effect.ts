import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import {
  GetNewsStreamItemsAction,
  GetNewsStreamItemsCompleteAction,
  GetNewsStreamItemsFailedAction,
  RogerthatActions,
  RogerthatActionTypes,
  ScanQrCodeAction,
  ScanQrCodeFailedAction,
  ScanQrCodeStartedAction,
} from './rogerthat.actions';
import { RogerthatService } from './rogerthat.service';

@Injectable()
export class RogerthatEffects {

   scanQrCode$ = createEffect(() => this.actions$.pipe(
    ofType<ScanQrCodeAction>(RogerthatActionTypes.SCAN_QR_CODE),
    switchMap(action => this.rogerthatService.startScanningQrCode(action.payload).pipe(
      // Actual result is dispatched in rogerthatService via rogerthat.callbacks.qrCodeScanned
      map(() => new ScanQrCodeStartedAction()),
      catchError(err => of(new ScanQrCodeFailedAction(err.message)))),
    )));

   getNewsStreamItems = createEffect(() => this.actions$.pipe(
    ofType<GetNewsStreamItemsAction>(RogerthatActionTypes.GET_NEWS_STREAM_ITEMS),
    switchMap(action => this.rogerthatService.getNewsStreamItems(action.payload).pipe(
      map(result => new GetNewsStreamItemsCompleteAction(result)),
      catchError(err => of(new GetNewsStreamItemsFailedAction(err.message)))),
    )));

  constructor(private actions$: Actions<RogerthatActions>,
              private rogerthatService: RogerthatService) {
  }
}
