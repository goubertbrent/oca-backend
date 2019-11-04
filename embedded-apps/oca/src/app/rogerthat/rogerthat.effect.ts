import { Injectable } from '@angular/core';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import {
  RogerthatActions,
  RogerthatActionTypes,
  ScanQrCodeAction,
  ScanQrCodeFailedAction,
  ScanQrCodeStartedAction,
} from './rogerthat.actions';
import { RogerthatService } from './rogerthat.service';

@Injectable()
export class RogerthatEffects {

  @Effect() scanQrCode$ = this.actions$.pipe(
    ofType<ScanQrCodeAction>(RogerthatActionTypes.SCAN_QR_CODE),
    switchMap(action => this.rogerthatService.startScanningQrCode(action.payload).pipe(
      // Actual result is dispatched in rogerthatService via rogerthat.callbacks.qrCodeScanned
      map(() => new ScanQrCodeStartedAction()),
      catchError(err => of(new ScanQrCodeFailedAction(err.message)))),
    ));


  constructor(private actions$: Actions<RogerthatActions>,
              private rogerthatService: RogerthatService) {
  }
}
