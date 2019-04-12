import { Injectable } from '@angular/core';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { of } from 'rxjs';
import { catchError, first, map, switchMap } from 'rxjs/operators';
import {
  GetAppStatisticsAction,
  GetAppStatisticsCompleteAction,
  GetAppStatisticsFailedAction, GetBudgetCompleteAction, GetBudgetFailedAction,
  GetMenuAction,
  GetMenuCompleteAction,
  GetMenuFailedAction,
  GetServiceIdentityAction,
  GetServiceIdentityCompleteAction,
  GetServiceIdentityFailedAction,
  SharedActions,
  SharedActionTypes,
} from './shared.actions';
import { SharedService } from './shared.service';
import { getAppStats, getBudget, getInfo, getServiceMenu, SharedState } from './shared.state';

@Injectable({ providedIn: 'root' })
export class SharedEffects {
  @Effect() getServiceMenu$ = this.actions$.pipe(
    ofType<GetMenuAction>(SharedActionTypes.GET_MENU),
    switchMap(() => this.store.pipe(select(getServiceMenu), first())),
    switchMap(menu => {
      if (menu.success && menu.data) {
        return of(new GetMenuCompleteAction(menu.data));
      }
      return this.sharedService.getMenu().pipe(
        map(forms => new GetMenuCompleteAction(forms)),
        catchError(err => of(new GetMenuFailedAction(err))));
    }),
  );

  @Effect() getInfo$ = this.actions$.pipe(
    ofType<GetServiceIdentityAction>(SharedActionTypes.GET_SERVICE_IDENTITY),
    switchMap(() => this.store.pipe(select(getInfo), first())),
    switchMap(info => {
      if (info.success && info.data) {
        return of(new GetServiceIdentityCompleteAction(info.data));
      }
      return this.sharedService.getInfo().pipe(
        map(data => new GetServiceIdentityCompleteAction(data)),
        catchError(err => of(new GetServiceIdentityFailedAction(err))));
    }));

  @Effect() getAppStatistics$ = this.actions$.pipe(
    ofType<GetAppStatisticsAction>(SharedActionTypes.GET_APP_STATISTICS),
    switchMap(() => this.store.pipe(select(getAppStats), first())),
    switchMap(storeData => {
      if (storeData.success && storeData.data) {
        return of(new GetAppStatisticsCompleteAction(storeData.data));
      }
      return this.sharedService.getAppStatistics().pipe(
        map(data => new GetAppStatisticsCompleteAction(data)),
        catchError(err => of(new GetAppStatisticsFailedAction(err))));
    }));

  @Effect() getBudget$= this.actions$.pipe(
    ofType<GetAppStatisticsAction>(SharedActionTypes.GET_BUDGET),
    switchMap(() => this.store.pipe(select(getBudget), first())),
    switchMap(storeData => {
      if (storeData.success && storeData.data) {
        return of(new GetBudgetCompleteAction(storeData.data));
      }
      return this.sharedService.getBudget().pipe(
        map(data => new GetBudgetCompleteAction(data)),
        catchError(err => of(new GetBudgetFailedAction(err))));
    }));

  constructor(private actions$: Actions<SharedActions>,
              private store: Store<SharedState>,
              private sharedService: SharedService) {
  }
}
