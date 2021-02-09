import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { ErrorService } from '@oca/web-shared';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import {
  GetOpeningHoursAction,
  GetOpeningHoursCompleteAction,
  GetOpeningHoursFailedAction,
  GetServiceInfoAction,
  GetServiceInfoCompleteAction,
  GetServiceInfoFailedAction,
  SaveOpeningHoursAction,
  SaveOpeningHoursCompleteAction,
  SaveOpeningHoursFailedAction,
  SettingsActions,
  SettingsActionTypes,
  UpdateServiceInfoAction,
  UpdateServiceInfoCompleteAction,
  UpdateServiceInfoFailedAction,
} from './settings.actions';
import { SettingsService } from './settings.service';
import { SettingsState } from './settings.state';

@Injectable({ providedIn: 'root' })
export class SettingsEffects {
   getOpeningHours$ = createEffect(() => this.actions$.pipe(
    ofType<GetOpeningHoursAction>(SettingsActionTypes.GET_OPENING_HOURS),
    switchMap(action => this.settingsService.getOpeningHours().pipe(
      map(result => new GetOpeningHoursCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetOpeningHoursFailedAction, err)))),
  ));

   saveOpeningHours$ = createEffect(() => this.actions$.pipe(
    ofType<SaveOpeningHoursAction>(SettingsActionTypes.SAVE_OPENING_HOURS),
    switchMap(action => this.settingsService.saveOpeningHours(action.payload).pipe(
      map(result => new SaveOpeningHoursCompleteAction(result)),
      tap(() => this.snackbar.open(this.translate.instant('oca.openinghours_saved'), undefined, { duration: 5000 })),
      catchError(err => this.errorService.handleError(action, SaveOpeningHoursFailedAction, err)))),
  ));

   getServiceInfo = createEffect(() => this.actions$.pipe(
    ofType<GetServiceInfoAction>(SettingsActionTypes.GET_SERVICE_INFO),
    switchMap(action => this.settingsService.getServiceInfo().pipe(
      map(result => new GetServiceInfoCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetServiceInfoFailedAction, err)))),
  ));

   updateServiceInfo = createEffect(() => this.actions$.pipe(
    ofType<UpdateServiceInfoAction>(SettingsActionTypes.UPDATE_SERVICE_INFO),
    switchMap(action => this.settingsService.updateServiceInfo(action.payload).pipe(
      map(result => new UpdateServiceInfoCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, UpdateServiceInfoFailedAction, err)))),
  ));

  constructor(private actions$: Actions<SettingsActions>,
              private store: Store<SettingsState>,
              private errorService: ErrorService,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private settingsService: SettingsService) {
  }
}
