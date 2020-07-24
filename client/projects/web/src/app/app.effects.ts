import { Injectable } from '@angular/core';
import { Router, RoutesRecognized } from '@angular/router';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { ErrorService } from '@oca/web-shared';
import { of } from 'rxjs';
import { catchError, map, switchMap, withLatestFrom } from 'rxjs/operators';
import { AppActions, AppActionTypes, GetAppInfo, GetAppInfoFailure, GetAppInfoSuccess } from './app.actions';
import { RootState } from './app.reducer';
import { getAppInfo } from './app.selectors';
import { AppService } from './app.service';
import { maybeDispatch } from './initial-state';


@Injectable()
export class AppEffects {
  getAppInfo$ = createEffect(() => this.actions$.pipe(
    ofType<GetAppInfo>(AppActionTypes.GetAppInfo),
    withLatestFrom(this.store.pipe(select(getAppInfo))),
    switchMap(([action, appInfo]) => {
      if (appInfo) {
        return of(new GetAppInfoSuccess({ data: appInfo }));
      }
      return this.service.getAppInfo(action.payload.appUrlName).pipe(
        map(data => new GetAppInfoSuccess({ data })),
        catchError(err => this.errorService.handleError(action, GetAppInfoFailure, err)),
      );
    }),
  ));

  constructor(private actions$: Actions<AppActions>,
              private router: Router,
              private store: Store<RootState>,
              private errorService: ErrorService,
              private service: AppService) {
    this.router.events.subscribe(val => {
      if (val instanceof RoutesRecognized) {
        const appUrlName = val.state.root.firstChild?.params.cityUrlName as string | undefined;
        if (appUrlName) {
          maybeDispatch(store, getAppInfo, item => item?.url_name === appUrlName, new GetAppInfo({ appUrlName }));
        }
      }
    });
  }

}
