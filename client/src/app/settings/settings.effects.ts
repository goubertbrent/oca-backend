import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { ErrorService } from '../shared/errors/error.service';
import {
  GetAvailablePlaceTypesAction,
  GetAvailablePlaceTypesCompleteAction,
  GetAvailablePlaceTypesFailedAction,
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
  @Effect() getOpeningHours$ = this.actions$.pipe(
    ofType<GetOpeningHoursAction>(SettingsActionTypes.GET_OPENING_HOURS),
    switchMap(action => this.settingsService.getOpeningHours().pipe(
      map(result => new GetOpeningHoursCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetOpeningHoursFailedAction, err)))),
  );

  @Effect() saveOpeningHours$ = this.actions$.pipe(
    ofType<SaveOpeningHoursAction>(SettingsActionTypes.SAVE_OPENING_HOURS),
    switchMap(action => this.settingsService.saveOpeningHours(action.payload).pipe(
      map(result => new SaveOpeningHoursCompleteAction(result)),
      tap(() => this.snackbar.open(this.translate.instant('oca.openinghours_saved'), undefined, { duration: 5000 })),
      catchError(err => this.errorService.handleError(action, SaveOpeningHoursFailedAction, err)))),
  );

  @Effect() getServiceInfo = this.actions$.pipe(
    ofType<GetServiceInfoAction>(SettingsActionTypes.GET_SERVICE_INFO),
    switchMap(action => this.settingsService.getServiceInfo().pipe(
      map(result => new GetServiceInfoCompleteAction(result)),
      catchError(err => of(new GetServiceInfoFailedAction(err))))),
  );

  @Effect({ dispatch: false }) showErrorDialog = this.actions$.pipe(
    ofType<GetServiceInfoFailedAction>(SettingsActionTypes.UPDATE_SERVICE_INFO_FAILED),
    tap(action => this.errorService.showErrorDialog(action.error)),
  );

  @Effect() updateServiceInfo = this.actions$.pipe(
    ofType<UpdateServiceInfoAction>(SettingsActionTypes.UPDATE_SERVICE_INFO),
    switchMap(action => this.settingsService.updateServiceInfo(action.payload).pipe(
      map(result => new UpdateServiceInfoCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, UpdateServiceInfoFailedAction, err)))),
  );

  @Effect() getAvailablePlaceTypes$ = this.actions$.pipe(
    ofType<GetAvailablePlaceTypesAction>(SettingsActionTypes.GET_AVAILABLE_PLACE_TYPES),
    switchMap(action => this.settingsService.getAvailablePlaceTypes().pipe(
      map(result => new GetAvailablePlaceTypesCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetAvailablePlaceTypesFailedAction, err)))),
  );

  constructor(private actions$: Actions<SettingsActions>,
              private store: Store<SettingsState>,
              private errorService: ErrorService,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private settingsService: SettingsService) {
  }
}