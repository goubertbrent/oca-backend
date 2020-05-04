import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { of, timer } from 'rxjs';
import { catchError, first, map, mergeMap, retryWhen, switchMap, take } from 'rxjs/operators';
import { ErrorService } from './errors/error.service';
import { transformErrorResponse } from './errors/errors';
import {
  GetAppsAction,
  GetAppsCompleteAction,
  GetAppsFailedAction,
  GetAppStatisticsAction,
  GetAppStatisticsCompleteAction,
  GetAppStatisticsFailedAction,
  GetBrandingSettingFailedAction,
  GetBrandingSettingsAction,
  GetBrandingSettingsCompleteAction,
  GetBudgetAction,
  GetBudgetCompleteAction,
  GetBudgetFailedAction,
  GetGlobalConfigAction,
  GetGlobalConfigCompleteAction,
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
  UpdateAvatarAction,
  UpdateAvatarCompleteAction,
  UpdateAvatarFailedAction, UpdateLogoAction, UpdateLogoCompleteAction, UpdateLogoFailedAction,
} from './shared.actions';
import { SharedService } from './shared.service';
import { getApps, getAppStatistics, getServiceIdentityInfo, getServiceMenu, SharedState } from './shared.state';

@Injectable({ providedIn: 'root' })
export class SharedEffects {

   getGlobalConfig$ = createEffect(() => this.actions$.pipe(
    ofType<GetGlobalConfigAction>(SharedActionTypes.GET_GLOBAL_CONFIG),
    take(1),
    switchMap(() => this.sharedService.getGlobalConstants().pipe(
      map(data => new GetGlobalConfigCompleteAction(data)),
      retryWhen(attempts => attempts.pipe(mergeMap(() => timer(2000)))),
    ))));

   getMenu$ = createEffect(() => this.actions$.pipe(
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
  ));

   getInfo$ = createEffect(() => this.actions$.pipe(
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
  ));

   getApps$ = createEffect(() => this.actions$.pipe(
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
  ));

   getAppStatistics$ = createEffect(() => this.actions$.pipe(
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
  ));

   getBudget$ = createEffect(() => this.actions$.pipe(
    ofType<GetBudgetAction>(SharedActionTypes.GET_BUDGET),
    switchMap(() => this.sharedService.getBudget().pipe(
      map(data => new GetBudgetCompleteAction(data)),
      catchError(err => of(new GetBudgetFailedAction(transformErrorResponse(err)))))),
  ));

   getSolutionSettings$ = createEffect(() => this.actions$.pipe(
    ofType<GetSolutionSettingsAction>(SharedActionTypes.GET_SOLUTION_SETTINGS),
    switchMap(() => this.sharedService.getSolutionSettings().pipe(
      map(data => new GetSolutionSettingsCompleteAction(data)),
      catchError(err => of(new GetSolutionSettingsFailedAction(transformErrorResponse(err))))),
    ),
  ));

   getBrandingSettings$ = createEffect(() => this.actions$.pipe(
    ofType<GetBrandingSettingsAction>(SharedActionTypes.GET_BRANDING_SETTINGS),
    switchMap(action => this.sharedService.getBrandingSettings().pipe(
      map(data => new GetBrandingSettingsCompleteAction(data)),
      catchError(err => this.errorService.handleError(action, GetBrandingSettingFailedAction, err))),
    ),
  ));

   updateAvatar$ = createEffect(() => this.actions$.pipe(
    ofType<UpdateAvatarAction>(SharedActionTypes.UPDATE_AVATAR),
    switchMap(action => this.sharedService.updateAvatar(action.payload.avatar_url).pipe(
      map(data => new UpdateAvatarCompleteAction(data)),
      catchError(err => this.errorService.handleError(action, UpdateAvatarFailedAction, err))),
    ),
  ));

   updateLogo$ = createEffect(() => this.actions$.pipe(
    ofType<UpdateLogoAction>(SharedActionTypes.UPDATE_LOGO),
    switchMap(action => this.sharedService.updateLogo(action.payload.logo_url).pipe(
      map(data => new UpdateLogoCompleteAction(data)),
      catchError(err => this.errorService.handleError(action, UpdateLogoFailedAction, err))),
    ),
  ));

  constructor(private actions$: Actions<SharedActions>,
              private store: Store<SharedState>,
              private errorService: ErrorService,
              private sharedService: SharedService) {
  }
}
