import { Injectable } from '@angular/core';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { catchError, map, switchMap } from 'rxjs/operators';
import { handleApiError } from '../../../framework/client/rpc';
import * as actions from '../actions/developer-accounts.actions';
import { DeveloperAccountsService } from '../services';

@Injectable()
export class DeveloperAccountsEffects {
  @Effect() getDeveloperAccounts$ = this.actions$.pipe(
    ofType<actions.GetDeveloperAccountAction>(actions.DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNTS),
    switchMap(() => this.devAccountsService.getDeveloperAccounts().pipe(
      map(payload => new actions.GetDeveloperAccountsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetDeveloperAccountsFailedAction, error)),
    )));

  @Effect() addDeveloperAccount$ = this.actions$.pipe(
    ofType<actions.CreateDeveloperAccountAction>(actions.DeveloperAccountsActionTypes.CREATE_DEVELOPER_ACCOUNT),
    switchMap(value => this.devAccountsService.createDeveloperAccount(value.payload).pipe(
      map(payload => new actions.CreateDeveloperAccountCompleteAction(payload)),
      catchError(error => handleApiError(actions.CreateDeveloperAccountFailedAction, error)),
    )));

  @Effect() getDeveloperAccount$ = this.actions$.pipe(
    ofType<actions.GetDeveloperAccountAction>(actions.DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNT),
    switchMap(action => this.devAccountsService.getDeveloperAccount(action.payload.id).pipe(
      map(payload => new actions.GetDeveloperAccountCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetDeveloperAccountFailedAction, error)),
    )));

  @Effect() updateDeveloperAccount$ = this.actions$.pipe(
    ofType<actions.UpdateDeveloperAccountAction>(actions.DeveloperAccountsActionTypes.UPDATE_DEVELOPER_ACCOUNT),
    switchMap(action => this.devAccountsService.updateDeveloperAccount(action.payload).pipe(
      map(payload => new actions.UpdateDeveloperAccountCompleteAction(payload)),
      catchError(error => handleApiError(actions.UpdateDeveloperAccountFailedAction, error)),
    )));

  @Effect() removeDeveloperAccount$ = this.actions$.pipe(
    ofType<actions.RemoveDeveloperAccountAction>(actions.DeveloperAccountsActionTypes.REMOVE_DEVELOPER_ACCOUNT),
    switchMap(action => this.devAccountsService.removeDeveloperAccount(action.payload).pipe(
      map(payload => new actions.RemoveDeveloperAccountCompleteAction(payload)),
      catchError(error => handleApiError(actions.RemoveDeveloperAccountFailedAction, error)),
    )));

  constructor(private actions$: Actions<actions.DeveloperAccountsActions>,
              private store: Store,
              private devAccountsService: DeveloperAccountsService) {
  }
}
