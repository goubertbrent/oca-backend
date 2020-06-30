import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { TranslateService } from '@ngx-translate/core';
import { RogerthatService } from '@oca/rogerthat';
import { of } from 'rxjs';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { ErrorService } from './error.service';
import { GetUserInformationResult, HoplrFeed, LookupNeighbourhoodResult, UserInformation } from './hoplr';
import {
  GetFeedAction,
  GetFeedFailedAction,
  GetFeedSuccessAction,
  GetUserInformationAction,
  GetUserInformationFailedAction,
  GetUserInformationSuccessAction,
  HoplrActionTypes,
  LoginAction,
  LoginFailedAction,
  LoginSuccessAction,
  LogoutAction,
  LogoutFailedAction,
  LogoutSuccessAction,
  LookupNeighbourhoodAction,
  LookupNeighbourhoodFailedAction,
  LookupNeighbourhoodSuccessAction,
  RegisterAction,
  RegisterFailedAction,
  RegisterSuccessAction,
} from './hoplr.actions';
import { HoplrService } from './hoplr.service';


export const enum ApiCalls {
  LOOKUP_NEIGHBOURHOOD = 'integrations.hoplr.lookup_neighbourhood',
  GET_USER_INFORMATION = 'integrations.hoplr.get_user_information',
  REGISTER = 'integrations.hoplr.register',
  LOGIN = 'integrations.hoplr.login',
  LOGOUT = 'integrations.hoplr.logout',
  GET_FEED = 'integrations.hoplr.get_feed',
}

@Injectable()
export class HoplrEffects {

  lookupNeighbourhood$ = createEffect(() => this.actions$.pipe(
    ofType<LookupNeighbourhoodAction>(HoplrActionTypes.LOOKUP_NEIGHBOURHOOD),
    switchMap(action => this.rogerthatService.apiCall<LookupNeighbourhoodResult>(ApiCalls.LOOKUP_NEIGHBOURHOOD, action.payload).pipe(
      map(payload => {
        if (payload.result.success) {
          return new LookupNeighbourhoodSuccessAction(payload);
        } else {
          let msg = payload.result.message;
          if (msg === 'place_not_found') {
            msg = this.translate.instant('app.hoplr.no_neighbourhood_found_for_your_address');
          }
          this.errorService.showErrorDialog(action, msg);
          return new LookupNeighbourhoodFailedAction(payload.result.message);
        }
      }),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new LookupNeighbourhoodFailedAction(err));
      })),
    ),
  ));

  getUserInfo$ = createEffect(() => this.actions$.pipe(
    ofType<GetUserInformationAction>(HoplrActionTypes.GET_USER_INFORMATION),
    switchMap(action => this.rogerthatService.apiCall<GetUserInformationResult>(ApiCalls.GET_USER_INFORMATION).pipe(
      map(payload => new GetUserInformationSuccessAction(payload)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetUserInformationFailedAction(err));
      })),
    ),
  ));

  register$ = createEffect(() => this.actions$.pipe(
    ofType<RegisterAction>(HoplrActionTypes.REGISTER),
    switchMap(action => this.rogerthatService.apiCall<GetUserInformationResult>(ApiCalls.REGISTER, action.payload).pipe(
      map(payload => new RegisterSuccessAction(payload)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new RegisterFailedAction(err));
      })),
    ),
  ));

  login$ = createEffect(() => this.actions$.pipe(
    ofType<LoginAction>(HoplrActionTypes.LOGIN),
    switchMap(action => this.rogerthatService.apiCall<GetUserInformationResult>(ApiCalls.LOGIN, action.payload).pipe(
      map(payload => new LoginSuccessAction(payload)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new LoginFailedAction(err));
      })),
    ),
  ));

  afterLogin$ = createEffect(() => this.actions$.pipe(
    ofType<RegisterSuccessAction | LoginSuccessAction>(HoplrActionTypes.LOGIN_SUCCESS, HoplrActionTypes.REGISTER_SUCCESS),
    tap(action => this.router.navigateByUrl('/feed')),
  ), { dispatch: false });

  logout$ = createEffect(() => this.actions$.pipe(
    ofType<LogoutAction>(HoplrActionTypes.LOGOUT),
    switchMap(action => this.rogerthatService.apiCall(ApiCalls.LOGOUT).pipe(
      map(payload => new LogoutSuccessAction()),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new LogoutFailedAction(err));
      })),
    ),
  ));

  afterLogout$ = createEffect(() => this.actions$.pipe(
    ofType<LogoutAction>(HoplrActionTypes.LOGOUT_SUCCESS),
    tap(() => this.router.navigateByUrl('/signin')),
  ), { dispatch: false });

  getFeed$ = createEffect(() => this.actions$.pipe(
    ofType<GetFeedAction>(HoplrActionTypes.GET_FEED),
    switchMap(action => this.rogerthatService.apiCall<HoplrFeed>(ApiCalls.GET_FEED, action.payload).pipe(
      map(payload => ({ ...payload, results: this.hoplrService.convertItems(payload.mediaBaseUrl, payload.results) })),
      map(payload => new GetFeedSuccessAction(payload)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetFeedFailedAction(err));
      })),
    ),
  ));

  constructor(protected actions$: Actions,
              protected errorService: ErrorService,
              private router: Router,
              private translate: TranslateService,
              protected hoplrService: HoplrService,
              protected rogerthatService: RogerthatService) {
  }

}
