import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { ErrorService } from '../shared/errors/error.service';
import {
  GetAvailablePlaceTypesAction,
  GetAvailablePlaceTypesCompleteAction,
  GetAvailablePlaceTypesFailedAction, GetCountriesAction, GetCountriesCompleteAction, GetCountriesFailedAction,
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
      catchError(err => of(new GetServiceInfoFailedAction(err.error.error))))),
  ));

   showErrorDialog = createEffect(() => this.actions$.pipe(
    ofType<GetServiceInfoFailedAction>(SettingsActionTypes.GET_SERVICE_INFO_FAILED),
    tap(action => this.errorService.showErrorDialog(action.error)),
  ), { dispatch: false });

   updateServiceInfo = createEffect(() => this.actions$.pipe(
    ofType<UpdateServiceInfoAction>(SettingsActionTypes.UPDATE_SERVICE_INFO),
    switchMap(action => this.settingsService.updateServiceInfo(action.payload).pipe(
      map(result => new UpdateServiceInfoCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, UpdateServiceInfoFailedAction, err)))),
  ));

   getAvailablePlaceTypes$ = createEffect(() => this.actions$.pipe(
    ofType<GetAvailablePlaceTypesAction>(SettingsActionTypes.GET_AVAILABLE_PLACE_TYPES),
    switchMap(action => this.settingsService.getAvailablePlaceTypes().pipe(
      map(result => new GetAvailablePlaceTypesCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetAvailablePlaceTypesFailedAction, err)))),
  ));

   getCountries$ = createEffect(() => this.actions$.pipe(
    ofType<GetCountriesAction>(SettingsActionTypes.GET_COUNTRIES),
    switchMap(action => this.settingsService.getCountries().pipe(
      map(result => new GetCountriesCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetCountriesFailedAction, err)))),
  ));

  constructor(private actions$: Actions<SettingsActions>,
              private store: Store<SettingsState>,
              private errorService: ErrorService,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private settingsService: SettingsService) {
  }
}
