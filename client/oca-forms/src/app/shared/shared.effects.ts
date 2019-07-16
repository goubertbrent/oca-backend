import { Injectable } from '@angular/core';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { of } from 'rxjs';
import { catchError, first, map, switchMap } from 'rxjs/operators';
import { transformErrorResponse } from './errors/errors';
import {
  GetAppsAction,
  GetAppsCompleteAction,
  GetAppsFailedAction,
  GetAppStatisticsAction,
  GetAppStatisticsCompleteAction,
  GetAppStatisticsFailedAction, GetBrandingSettingFailedAction, GetBrandingSettingsAction, GetBrandingSettingsCompleteAction,
  GetBudgetAction,
  GetBudgetCompleteAction,
  GetBudgetFailedAction,
  GetInfoAction,
  GetInfoCompleteAction,
  GetInfoFailedAction,
  GetMenuAction,
  GetMenuCompleteAction,
  GetMenuFailedAction,
  GetSolutionSettingsAction,
  GetSolutionSettingsCompleteAction,
  GetSolutionSettingsFailedAction,
  SharedActions,
  SharedActionTypes,
} from './shared.actions';
import { SharedService } from './shared.service';
import { getApps, getAppStatistics, getServiceIdentityInfo, getServiceMenu, SharedState } from './shared.state';

@Injectable({ providedIn: 'root' })
export class SharedEffects {
  @Effect() getMenu$ = this.actions$.pipe(
    ofType<GetMenuAction>(SharedActionTypes.GET_MENU),
    switchMap(() => this.store.pipe(select(getServiceMenu), first())),
    switchMap(menu => {
      if (menu.success && menu.data) {
        return of(new GetMenuCompleteAction(menu.data));
      }
      return this.sharedService.getMenu().pipe(
        map(forms => new GetMenuCompleteAction(forms)),
        catchError(err => of(new GetMenuFailedAction(transformErrorResponse(err)))));
    }),
  );

  @Effect() getInfo$ = this.actions$.pipe(
    ofType<GetInfoAction>(SharedActionTypes.GET_INFO),
    switchMap(() => this.store.pipe(select(getServiceIdentityInfo), first())),
    switchMap(info => {
      if (info.success && info.data) {
        return of(new GetInfoCompleteAction(info.data));
      }
      return this.sharedService.getServiceIdentityInfo().pipe(
        map(data => new GetInfoCompleteAction(data)),
        catchError(err => of(new GetInfoFailedAction(transformErrorResponse(err)))));
    }),
  );

  @Effect() getApps$ = this.actions$.pipe(
    ofType<GetAppsAction>(SharedActionTypes.GET_APPS),
    switchMap(() => this.store.pipe(select(getApps), first())),
    switchMap(apps => {
      if (apps.success && apps.data && apps.data.length) {
        return of(new GetAppsCompleteAction(apps.data));
      }
      return this.sharedService.getApps().pipe(
        map(data => new GetAppsCompleteAction(data)),
        catchError(err => of(new GetAppsFailedAction(transformErrorResponse(err)))));
    }),
  );

  @Effect() getAppStatistics$ = this.actions$.pipe(
    ofType<GetAppStatisticsAction>(SharedActionTypes.GET_APP_STATISTICS),
    switchMap(() => this.store.pipe(select(getAppStatistics), first())),
    switchMap(apps => {
      if (Object.keys(apps).length) {
        return of(new GetAppStatisticsCompleteAction(Object.values(apps)));
      }
      return this.sharedService.getAppStatistics().pipe(
        map(data => new GetAppStatisticsCompleteAction(data)),
        catchError(err => of(new GetAppStatisticsFailedAction(transformErrorResponse(err)))));
    }),
  );

  @Effect() getBudget$ = this.actions$.pipe(
    ofType<GetBudgetAction>(SharedActionTypes.GET_BUDGET),
    switchMap(() => this.sharedService.getBudget().pipe(
      map(data => new GetBudgetCompleteAction(data)),
      catchError(err => of(new GetBudgetFailedAction(transformErrorResponse(err)))))),
  );

  @Effect() getSolutionSettings$ = this.actions$.pipe(
    ofType<GetSolutionSettingsAction>(SharedActionTypes.GET_SOLUTION_SETTINGS),
    switchMap(() => this.sharedService.getSolutionSettings().pipe(
      map(data => new GetSolutionSettingsCompleteAction(data)),
      catchError(err => of(new GetSolutionSettingsFailedAction(transformErrorResponse(err))))),
    ),
  );

  @Effect() getBrandingSettings$ = this.actions$.pipe(
    ofType<GetBrandingSettingsAction>(SharedActionTypes.GET_BRANDING_SETTINGS),
    switchMap(() => this.sharedService.getBrandingSettings().pipe(
      map(data => new GetBrandingSettingsCompleteAction(data)),
      catchError(err => of(new GetBrandingSettingFailedAction(transformErrorResponse(err))))),
    ),
  );

  constructor(private actions$: Actions<SharedActions>,
              private store: Store<SharedState>,
              private sharedService: SharedService) {
  }
}
