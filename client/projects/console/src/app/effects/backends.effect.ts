import { Injectable } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { handleApiError } from '../../../framework/client/rpc';
import { BackendsActionTypes } from '../actions';
import * as actions from '../actions/backends.actions';
import { AppsService, RogerthatBackendsService } from '../services';

@Injectable()
export class BackendsEffects {

  @Effect() getBackendRogerthatApps$ = this.actions$.pipe(
    ofType<actions.GetBackendRogerthatAppsAction>(BackendsActionTypes.GET_ROGERTHAT_APPS),
    switchMap(() => this.appsService.getRogerthatApps().pipe(
      map(payload => new actions.GetBackendRogerthatAppsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetBackendRogerthatAppsFailedAction, error)),
    )));

  @Effect() setDefaultApp$ = this.actions$.pipe(
    ofType<actions.SetDefaultRogerthatAppAction>(BackendsActionTypes.SET_DEFAULT_ROGERTHAT_APP),
    switchMap(action => this.appsService.setDefaultApp(action.payload).pipe(
      map(result => new actions.SetDefaultRogerthatAppCompleteAction(result)),
      catchError(error => handleApiError(actions.SetDefaultRogerthatAppFailedAction, error)),
    )));

  @Effect() getBackendAppAssets$ = this.actions$.pipe(
    ofType<actions.GetBackendAppAssetsAction>(BackendsActionTypes.GET_APP_ASSETS),
    switchMap(() => this.appsService.getBackendAppAssets().pipe(
      map(payload => new actions.GetBackendAppAssetsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetBackendAppAssetsFailedAction, error)),
    )));

  @Effect() getBackendAppAsset$ = this.actions$.pipe(
    ofType<actions.GetBackendAppAssetAction>(BackendsActionTypes.GET_APP_ASSET),
    switchMap(action => this.appsService.getBackendAppAsset(action.payload).pipe(
      map(payload => new actions.GetBackendAppAssetCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetBackendAppAssetFailedAction, error)),
    )));

  @Effect() createBackendAppAsset$ = this.actions$.pipe(
    ofType<actions.CreateBackendAppAssetAction>(BackendsActionTypes.CREATE_APP_ASSET),
    switchMap(action => this.appsService.createBackendAppAsset(action.payload).pipe(
      map(payload => new actions.CreateBackendAppAssetCompleteAction(payload)),
      catchError(error => handleApiError(actions.CreateBackendAppAssetFailedAction, error)),
    )));

  @Effect() updateBackendAppAsset$ = this.actions$.pipe(
    ofType<actions.UpdateBackendAppAssetAction>(BackendsActionTypes.UPDATE_APP_ASSET),
    switchMap(action => this.appsService.updateBackendAppAsset(action.payload).pipe(
      map(payload => new actions.UpdateBackendAppAssetCompleteAction(payload)),
      catchError(error => handleApiError(actions.UpdateBackendAppAssetFailedAction, error)),
    )));

  @Effect() removeBackendAppAsset$ = this.actions$.pipe(
    ofType<actions.RemoveBackendAppAssetAction>(BackendsActionTypes.REMOVE_APP_ASSET),
    switchMap(action => this.appsService.removeBackendAppAsset(action.payload).pipe(
      map(payload => new actions.RemoveBackendAppAssetCompleteAction(payload)),
      catchError(error => handleApiError(actions.RemoveBackendAppAssetFailedAction, error)),
    )));

  @Effect() getBackendBrandings$ = this.actions$.pipe(
    ofType<actions.GetBackendBrandingsAction>(BackendsActionTypes.GET_BRANDINGS),
    switchMap(() => this.appsService.getBackendBrandings().pipe(
      map(payload => new actions.GetBackendBrandingsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetBackendBrandingsFailedAction, error)),
    )));

  @Effect() getBackendBranding$ = this.actions$.pipe(
    ofType<actions.GetBackendBrandingAction>(BackendsActionTypes.GET_BRANDING),
    switchMap(action => this.appsService.getBackendBranding(action.payload).pipe(
      map(payload => new actions.GetBackendBrandingCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetBackendBrandingFailedAction, error)),
    )));

  @Effect() createBackendBranding$ = this.actions$.pipe(
    ofType<actions.CreateBackendBrandingAction>(BackendsActionTypes.CREATE_BRANDING),
    switchMap(action => this.appsService.createGlobalBackendBranding(action.payload).pipe(
      map(payload => new actions.CreateBackendBrandingCompleteAction(payload)),
      catchError(error => handleApiError(actions.CreateBackendBrandingFailedAction, error)),
    )));

  @Effect() updateBackendBranding$ = this.actions$.pipe(
    ofType<actions.UpdateBackendBrandingAction>(BackendsActionTypes.UPDATE_BRANDING),
    switchMap(action => this.appsService.updateBackendBranding(action.payload).pipe(
      map(payload => new actions.UpdateBackendBrandingCompleteAction(payload)),
      catchError(error => handleApiError(actions.UpdateBackendBrandingFailedAction, error)),
    )));

  @Effect() removeBackendBranding$ = this.actions$.pipe(
    ofType<actions.RemoveBackendBrandingAction>(BackendsActionTypes.REMOVE_BRANDING),
    switchMap(action => this.appsService.removeBackendBranding(action.payload).pipe(
      map(payload => new actions.RemoveBackendBrandingCompleteAction(payload)),
      catchError(error => handleApiError(actions.RemoveBackendBrandingFailedAction, error)),
    )));

  @Effect() getPaymentProviders$ = this.actions$.pipe(
    ofType<actions.GetPaymentProvidersAction>(BackendsActionTypes.GET_PAYMENT_PROVIDERS),
    switchMap(() => this.backendService.getPaymentProviders().pipe(
      map(payload => new actions.GetPaymentProvidersCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetPaymentProvidersFailedAction, error)),
    )));

  @Effect() getPaymentProvider$ = this.actions$.pipe(
    ofType<actions.GetPaymentProviderAction>(BackendsActionTypes.GET_PAYMENT_PROVIDER),
    switchMap(action => this.backendService.getPaymentProvider(action.payload).pipe(
      map(payload => new actions.GetPaymentProviderCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetPaymentProviderFailedAction, error)),
    )));

  @Effect() createPaymentProvider$ = this.actions$.pipe(
    ofType<actions.CreatePaymentProviderAction>(BackendsActionTypes.CREATE_PAYMENT_PROVIDER),
    switchMap(action => this.backendService.createPaymentProvider(action.payload).pipe(
      map(payload => new actions.CreatePaymentProviderCompleteAction(payload)),
      catchError(error => handleApiError(actions.CreatePaymentProviderFailedAction, error)),
    )));

  @Effect() updatePaymentProvider$ = this.actions$.pipe(
    ofType<actions.UpdatePaymentProviderAction>(BackendsActionTypes.UPDATE_PAYMENT_PROVIDER),
    switchMap(action => this.backendService.updatePaymentProvider(action.payload).pipe(
      map(payload => new actions.UpdatePaymentProviderCompleteAction(payload)),
      catchError(error => handleApiError(actions.UpdatePaymentProviderFailedAction, error)),
    )));

  @Effect() removePaymentProvider$ = this.actions$.pipe(
    ofType<actions.RemovePaymentProviderAction>(BackendsActionTypes.REMOVE_PAYMENT_PROVIDER),
    switchMap(action => this.backendService.removePaymentProvider(action.payload).pipe(
      map(payload => new actions.RemovePaymentProviderCompleteAction(payload)),
      catchError(error => handleApiError(actions.RemovePaymentProviderFailedAction, error)),
    )));

  @Effect() listEmbeddedApps$ = this.actions$.pipe(
    ofType<actions.ListEmbeddedAppsAction>(BackendsActionTypes.LIST_EMBEDDED_APPS),
    switchMap(action => this.backendService.listEmbeddedApps(action.tag).pipe(
      map(payload => new actions.ListEmbeddedAppsCompleteAction(payload)),
      catchError(error => handleApiError(actions.ListEmbeddedAppsFailedAction, error)),
    )));

  @Effect() getEmbeddedApp$ = this.actions$.pipe(
    ofType<actions.GetEmbeddedAppAction>(BackendsActionTypes.GET_EMBEDDED_APP),
    switchMap(action => this.backendService.getEmbeddedApp(action.payload).pipe(
      map(payload => new actions.GetEmbeddedAppCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetEmbeddedAppFailedAction, error)),
    )));

  @Effect() createEmbeddedApp$ = this.actions$.pipe(
    ofType<actions.CreateEmbeddedAppAction>(BackendsActionTypes.CREATE_EMBEDDED_APP),
    switchMap(action => this.backendService.createEmbeddedApp(action.payload).pipe(
      map(payload => new actions.CreateEmbeddedAppCompleteAction(payload)),
      catchError(error => handleApiError(actions.CreateEmbeddedAppFailedAction, error)),
    )));

  @Effect() updateEmbeddedApp$ = this.actions$.pipe(
    ofType<actions.UpdateEmbeddedAppAction>(BackendsActionTypes.UPDATE_EMBEDDED_APP),
    switchMap(action => this.backendService.updateEmbeddedApp(action.payload).pipe(
      map(payload => new actions.UpdateEmbeddedAppCompleteAction(payload)),
      catchError(error => handleApiError(actions.UpdateEmbeddedAppFailedAction, error)),
    )));

  @Effect() removeEmbeddedApp$ = this.actions$.pipe(
    ofType<actions.RemoveEmbeddedAppAction>(BackendsActionTypes.REMOVE_EMBEDDED_APP),
    switchMap(action => this.backendService.removeEmbeddedApp(action.payload).pipe(
      map(payload => new actions.RemoveEmbeddedAppCompleteAction(payload)),
      catchError(error => handleApiError(actions.RemoveEmbeddedAppFailedAction, error)),
    )));

  @Effect() listFirebaseProjects$ = this.actions$.pipe(
    ofType<actions.ListFirebaseProjectsAction>(BackendsActionTypes.LIST_FIREBASE_PROJECTS),
    switchMap(() => this.backendService.listFirebaseProjects().pipe(
      map(payload => new actions.ListFirebaseProjectsCompleteAction(payload)),
      catchError(error => handleApiError(actions.ListFirebaseProjectsFailedAction, error)),
    )));

  @Effect() createFirebaseProject$ = this.actions$.pipe(
    ofType<actions.CreateFirebaseProjectAction>(BackendsActionTypes.CREATE_FIREBASE_PROJECT),
    switchMap(action => this.backendService.createFirebaseProject(action.payload).pipe(
      map(payload => new actions.CreateFirebaseProjectCompleteAction(payload)),
      tap(() => this.router.navigate(['/firebase-projects'])),
      catchError(error => handleApiError(actions.CreateFirebaseProjectFailedAction, error)),
    )));

  constructor(private actions$: Actions,
              private route: ActivatedRoute,
              private router: Router,
              private backendService: RogerthatBackendsService,
              private appsService: AppsService) {
  }
}
