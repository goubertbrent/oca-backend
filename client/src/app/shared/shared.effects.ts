import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { ErrorService } from '@oca/web-shared';
import { of, timer } from 'rxjs';
import { catchError, map, mergeMap, retryWhen, switchMap, take, tap } from 'rxjs/operators';
import { RootState } from '../reducers';
import { transformErrorResponse } from './errors/errors';
import {
  AddBudgetAction,
  AddBudgetCompleteAction,
  AddBudgetFailedAction,
  GetBrandingSettingFailedAction,
  GetBrandingSettingsAction,
  GetBrandingSettingsCompleteAction,
  GetBudgetAction,
  GetBudgetCompleteAction,
  GetBudgetFailedAction,
  GetGlobalConfigAction,
  GetGlobalConfigCompleteAction,
  GetSolutionSettingsAction,
  GetSolutionSettingsCompleteAction,
  GetSolutionSettingsFailedAction,
  SharedActions,
  SharedActionTypes,
  UpdateAvatarAction,
  UpdateAvatarCompleteAction,
  UpdateAvatarFailedAction,
  UpdateLogoAction,
  UpdateLogoCompleteAction,
  UpdateLogoFailedAction,
} from './shared.actions';
import { SharedService } from './shared.service';

@Injectable({ providedIn: 'root' })
export class SharedEffects {

   getGlobalConfig$ = createEffect(() => this.actions$.pipe(
    ofType<GetGlobalConfigAction>(SharedActionTypes.GET_GLOBAL_CONFIG),
    take(1),
    switchMap(() => this.sharedService.getGlobalConstants().pipe(
      map(data => new GetGlobalConfigCompleteAction(data)),
      retryWhen(attempts => attempts.pipe(mergeMap(() => timer(2000)))),
    ))));

  getBudget$ = createEffect(() => this.actions$.pipe(
    ofType<GetBudgetAction>(SharedActionTypes.GET_BUDGET),
    switchMap(() => this.sharedService.getBudget().pipe(
      map(data => new GetBudgetCompleteAction(data)),
      catchError(err => of(new GetBudgetFailedAction(transformErrorResponse(err)))))),
  ));

  addBudget$ = createEffect(() => this.actions$.pipe(
    ofType<AddBudgetAction>(SharedActionTypes.ADD_BUDGET),
    switchMap(action => this.sharedService.addBudget(action.payload.vat).pipe(
      map(data => new AddBudgetCompleteAction(data)),
      catchError(err => of(new AddBudgetFailedAction(transformErrorResponse(err))).pipe(
        tap(e => this.errorService.showErrorDialog(e.error.error))
      )))),
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
              private store: Store<RootState>,
              private errorService: ErrorService,
              private sharedService: SharedService) {
  }
}
