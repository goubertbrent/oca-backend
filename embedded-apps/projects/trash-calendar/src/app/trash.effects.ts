import { Injectable } from '@angular/core';
import { NavController } from '@ionic/angular';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { RogerthatService, SetUserDataAction } from '@oca/rogerthat';
import { of } from 'rxjs';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { ErrorService } from './error.service';
import { GetStreetsResult, SaveAddressRequest, SaveNotificationsRequest, TrashHouseNumber } from './trash';
import {
  GetHouseNumbers,
  GetHouseNumbersFailure,
  GetHouseNumbersSuccess,
  GetStreets,
  GetStreetsFailure,
  GetStreetsSuccess,
  SaveAddress,
  SaveAddressFailure,
  SaveAddressSuccess,
  SaveNotifications,
  SaveNotificationsFailure,
  SaveNotificationsSuccess,
  TrashActionTypes,
} from './trash.actions';


export const enum ApiCalls {
  GetStreets = 'trash.getStreets',
  GetHouseNumbers = 'trash.getStreetNumbers',
  SaveAddress = 'trash.setLocation',
  SaveNotifications = 'trash.setNotifications',
}

@Injectable()
export class TrashEffects {
  getStreets$ = createEffect(() => this.actions$.pipe(
    ofType<GetStreets>(TrashActionTypes.GetStreets),
    switchMap(action => this.rogerthatService.apiCall<GetStreetsResult>(ApiCalls.GetStreets).pipe(
      map(payload => new GetStreetsSuccess(payload)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetStreetsFailure(err));
      })),
    ),
  ));

  getHouseNumbers$ = createEffect(() => this.actions$.pipe(
    ofType<GetHouseNumbers>(TrashActionTypes.GetHouseNumbers),
    switchMap(action => this.rogerthatService.apiCall<TrashHouseNumber[]>(ApiCalls.GetHouseNumbers, action.payload).pipe(
      map(payload => new GetHouseNumbersSuccess(payload)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetHouseNumbersFailure(err));
      })),
    ),
  ));

  saveAddress$ = createEffect(() => this.actions$.pipe(
    ofType<SaveAddress>(TrashActionTypes.SaveAddress),
    switchMap(action => this.rogerthatService.apiCall<SaveAddressRequest>(ApiCalls.SaveAddress, action.payload).pipe(
      map(() => new SaveAddressSuccess()),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new SaveAddressFailure(err));
      })),
    ),
  ));

  afterAddressSaved$ = createEffect(() => this.actions$.pipe(
    ofType<SaveAddressSuccess>(TrashActionTypes.SaveAddressSuccess),
    tap(() => this.navController.back()),
  ), { dispatch: false });

  saveNotifications$ = createEffect(() => this.actions$.pipe(
    ofType<SaveNotifications>(TrashActionTypes.SaveNotifications),
    switchMap(action => this.rogerthatService.apiCall<SaveNotificationsRequest>(ApiCalls.SaveNotifications, action.payload).pipe(
      map(() => {
        const updated = { trash: { ...rogerthat.user.data.trash, notifications: action.payload.notifications } };
        rogerthat.user.put(updated);
        return new SaveNotificationsSuccess();
      }),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new SaveNotificationsFailure(err));
      })),
    ),
  ));

  afterNotificationsSaved$ = createEffect(() => this.actions$.pipe(
    ofType<SaveNotificationsSuccess>(TrashActionTypes.SaveNotificationsSuccess),
    map(() => {
      this.navController.back();
      // Take copy, otherwise ngrx selectors won't update
      return new SetUserDataAction({ ...rogerthat.user.data });
    }),
  ));

  constructor(protected actions$: Actions,
              protected navController: NavController,
              protected errorService: ErrorService,
              protected store: Store,
              protected rogerthatService: RogerthatService) {
  }

}
