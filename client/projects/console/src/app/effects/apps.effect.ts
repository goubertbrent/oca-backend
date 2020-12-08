import { Injectable } from '@angular/core';
import { ActivatedRoute, ActivatedRouteSnapshot, Router } from '@angular/router';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { auditTime, catchError, map, switchMap, tap, withLatestFrom } from 'rxjs/operators';
import { handleApiError } from '../../../framework/client/rpc';
import { AppsActionTypes } from '../actions';
import * as actions from '../actions/apps.actions';
import { getApp } from '../console.state';
import { filterNull } from '../ngrx';
import { AppsService } from '../services';

@Injectable()
export class AppsEffects {

  @Effect() searchApps$ = this.actions$.pipe(
    ofType<actions.SearchAppsAction>(AppsActionTypes.SEARCH_APPS),
    auditTime(400), // ensures the function is not called more than once every 400 ms
    tap(() => this.store.dispatch(new actions.SearchAppsInitAction())), // For the loading spinner
    switchMap(value => this.appsService.searchApps(value.payload).pipe(
      map(payload => new actions.SearchAppsCompleteAction(payload)),
      catchError(error => handleApiError(actions.SearchAppsFailedAction, error)),
    )));

  @Effect() getApp$ = this.actions$.pipe(
    ofType<actions.GetAppAction>(AppsActionTypes.GET_APP),
    switchMap(value => this.appsService.getApp(value.payload).pipe(
      map(payload => new actions.GetAppCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetAppFailedAction, error)),
    )));

  @Effect() getApps$ = this.actions$.pipe(
    ofType<actions.GetAppsAction>(AppsActionTypes.GET_APPS),
    switchMap(() => this.appsService.getApps().pipe(
      map(payload => new actions.GetAppsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetAppsFailedAction, error)),
    )));

  @Effect() getProductionApps$ = this.actions$.pipe(
    ofType<actions.GetProductionAppsAction>(AppsActionTypes.GET_PRODUCTION_APPS),
    switchMap(() => this.appsService.getProductionApps().pipe(
      map(payload => new actions.GetProductionAppsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetProductionAppsFailedAction, error)),
    )));

  @Effect() createApp$ = this.actions$.pipe(
    ofType<actions.CreateAppAction>(AppsActionTypes.CREATE_APP),
    switchMap(value => this.appsService.createApp(value.payload).pipe(
      map(payload => new actions.CreateAppCompleteAction(payload)),
      tap(action => this.router.navigateByUrl(`/apps/${action.payload.app_id}`)),
      catchError(error => handleApiError(actions.CreateAppFailedAction, error)),
    )));

  @Effect() updateApp$ = this.actions$.pipe(
    ofType<actions.UpdateAppAction>(AppsActionTypes.UPDATE_APP),
    switchMap(value => this.appsService.updateApp(value.payload).pipe(
      map(payload => new actions.UpdateAppCompleteAction(payload)),
      catchError(error => handleApiError(actions.UpdateAppFailedAction, error)),
    )));

  @Effect() patchApp$ = this.actions$.pipe(
    ofType<actions.PatchAppAction>(AppsActionTypes.PATCH_APP),
    withLatestFrom(this.store.select(getApp).pipe(filterNull())),
    switchMap(([action, app]) => this.appsService.patchApp(app.app_id, app.backend_server, action.payload).pipe(
      map(payload => new actions.PatchAppCompleteAction(payload)),
      catchError(error => handleApiError(actions.PatchAppFailedAction, error)),
    )));

  @Effect() getBuilds$ = this.actions$.pipe(
    ofType<actions.GetBuildsAction>(AppsActionTypes.GET_BUILDS),
    switchMap(value => this.appsService.getBuilds(value.payload).pipe(
      map(payload => new actions.GetBuildsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetBuildsFailedAction, error)),
    )));

  @Effect() createBuild$ = this.actions$.pipe(
    ofType<actions.CreateBuildAction>(AppsActionTypes.CREATE_BUILD),
    switchMap(action => this.appsService.createBuild(action.payload.app_id, action.payload.data).pipe(
      map(payload => new actions.CreateBuildCompleteAction(payload)),
      catchError(error => handleApiError(actions.CreateBuildFailedAction, error)),
    )));

  // Waits until 'getApp' has returned a value (so when the app info from app-configurator is fetched)
  @Effect() getRogerthatApp = this.actions$.pipe(
    ofType<actions.GetRogerthatAppAction>(AppsActionTypes.GET_ROGERTHAT_APP),
    switchMap(action => this.appsService.getRogerthatApp(action.payload.appId).pipe(
      map(payload => new actions.GetRogerthatAppCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetRogerthatAppFailedAction, error)),
    )));

  @Effect() updateRogerthatApp = this.actions$.pipe(
    ofType<actions.UpdateRogerthatAppAction>(AppsActionTypes.UPDATE_ROGERTHAT_APP),
    switchMap(action => {
      return this.appsService.updateRogerthatApp(action.payload).pipe(
        map(payload => new actions.UpdateRogerthatAppCompleteAction(payload)),
        catchError(error => handleApiError(actions.UpdateRogerthatAppFailedAction, error)),
      );
    }));

  @Effect() getQrCodeTemplates = this.actions$.pipe(
    ofType<actions.GetQrCodeTemplatesAction>(AppsActionTypes.GET_QR_CODE_TEMPLATES),
    switchMap(value => this.appsService.getQrCodeTemplates(value.payload.appId).pipe(
      map(payload => new actions.GetQrCodeTemplatesCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetQrCodeTemplatesFailedAction, error)),
    )));

  @Effect() addQrCodeTemplate = this.actions$.pipe(
    ofType<actions.AddQrCodeTemplateAction>(AppsActionTypes.ADD_QR_CODE_TEMPLATE),
    switchMap(value => this.appsService.addQrCodeTemplate(value.payload.appId, value.payload.data).pipe(
      map(payload => new actions.AddQrCodeTemplateCompleteAction(payload)),
      catchError(error => handleApiError(actions.AddQrCodeTemplateFailedAction, error)),
    )));

  @Effect() createDefaultQrCodeTemplate = this.actions$.pipe(
    ofType<actions.CreateDefaultQrCodeTemplateAction>(AppsActionTypes.CREATE_DEFAULT_QR_CODE_TEMPLATE),
    switchMap(value => this.appsService.createDefaultQrCodeTemplate(value.payload.appId, value.payload.data).pipe(
      map(payload => new actions.CreateDefaultQrCodeTemplateCompleteAction(payload)),
      catchError(error => handleApiError(actions.CreateDefaultQrCodeTemplateFailedAction, error)),
    )));

  @Effect() removeQrCodeTemplate = this.actions$.pipe(
    ofType<actions.RemoveQrCodeTemplateAction>(AppsActionTypes.REMOVE_QR_CODE_TEMPLATE),
    switchMap(value => this.appsService.removeQrCodeTemplate(value.payload.appId, value.payload.data).pipe(
      map(payload => new actions.RemoveQrCodeTemplateCompleteAction(payload)),
      catchError(error => handleApiError(actions.RemoveQrCodeTemplateFailedAction, error)),
    )));

  @Effect() getAppAssets = this.actions$.pipe(
    ofType<actions.GetAppAssetsAction>(AppsActionTypes.GET_APP_ASSETS),
    switchMap(value => this.appsService.getAppAssets(value.payload).pipe(
      map(payload => new actions.GetAppAssetsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetAppAssetsFailedAction, error)),
    )));

  @Effect() createAppAsset = this.actions$.pipe(
    ofType<actions.CreateAppAssetAction>(AppsActionTypes.CREATE_APP_ASSET),
    switchMap(action => this.appsService.createAppAsset(action.payload, this.getAppId()).pipe(
      map(payload => new actions.CreateAppAssetCompleteAction(payload)),
      catchError(error => handleApiError(actions.CreateAppAssetFailedAction, error)),
    )));

  @Effect() removeAppAsset = this.actions$.pipe(
    ofType<actions.RemoveAppAssetAction>(AppsActionTypes.REMOVE_APP_ASSET),
    switchMap(value => this.appsService.removeAppAsset(value.payload.appId, value.payload.data).pipe(
      map(payload => new actions.RemoveAppAssetCompleteAction(payload)),
      catchError(error => handleApiError(actions.RemoveAppAssetFailedAction, error)),
    )));

  @Effect() getDefaultBrandings = this.actions$.pipe(
    ofType<actions.GetDefaultBrandingsAction>(AppsActionTypes.GET_DEFAULT_BRANDINGS),
    switchMap(value => this.appsService.getDefaultBrandings(value.payload.appId).pipe(
      map(payload => new actions.GetDefaultBrandingsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetDefaultBrandingsFailedAction, error)),
    )));

  @Effect() createDefaultBranding = this.actions$.pipe(
    ofType<actions.CreateDefaultBrandingAction>(AppsActionTypes.CREATE_DEFAULT_BRANDING),
    switchMap(action => this.appsService.createBackendBranding(this.getAppId(), action.payload).pipe(
      map(payload => new actions.CreateDefaultBrandingCompleteAction(payload)),
      catchError(error => handleApiError(actions.CreateDefaultBrandingFailedAction, error)),
    )));

  @Effect() removeDefaultBranding = this.actions$.pipe(
    ofType<actions.RemoveDefaultBrandingAction>(AppsActionTypes.REMOVE_DEFAULT_BRANDING),
    switchMap(value => this.appsService.removeDefaultBranding(value.payload.appId, value.payload.data).pipe(
      map(payload => new actions.RemoveDefaultBrandingCompleteAction(payload)),
      catchError(error => handleApiError(actions.RemoveDefaultBrandingFailedAction, error)),
    )));

  @Effect() getAppColors$ = this.actions$.pipe(
    ofType<actions.GetAppColorsAction>(AppsActionTypes.GET_COLORS),
    switchMap(() => this.appsService.getColors(this.getAppId()).pipe(
      map(payload => new actions.GetAppColorsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetAppColorsFailedAction, error)),
    )));

  @Effect() updateAppColors$ = this.actions$.pipe(
    ofType<actions.UpdateAppColorsAction>(AppsActionTypes.UPDATE_COLORS),
    switchMap(action => this.appsService.updateColors(this.getAppId(), action.payload).pipe(
      map(payload => new actions.UpdateAppColorsCompleteAction(payload)),
      catchError(error => handleApiError(actions.UpdateAppColorsFailedAction, error)),
    )));

  @Effect() getAppSidebar$ = this.actions$.pipe(
    ofType<actions.GetAppSidebarAction>(AppsActionTypes.GET_SIDEBAR),
    switchMap(() => this.appsService.getSidebar(this.getAppId()).pipe(
      map(payload => new actions.GetAppSidebarCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetAppSidebarFailedAction, error)),
    )));

  @Effect() updateAppSidebar$ = this.actions$.pipe(
    ofType<actions.UpdateAppSidebarAction>(AppsActionTypes.UPDATE_SIDEBAR),
    switchMap(action => this.appsService.updateSidebar(this.getAppId(), action.payload).pipe(
      map(payload => new actions.UpdateAppSidebarCompleteAction(payload)),
      catchError(error => handleApiError(actions.UpdateAppSidebarFailedAction, error)),
    )));

  @Effect() getAppImages$ = this.actions$.pipe(
    ofType<actions.GetAppImagesAction>(AppsActionTypes.GET_IMAGES),
    switchMap(() => this.appsService.getImages(this.getAppId()).pipe(
      map(payload => new actions.GetAppImagesCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetAppImagesFailedAction, error)),
    )));

  @Effect() getAppImage$ = this.actions$.pipe(
    ofType<actions.GetAppImageAction>(AppsActionTypes.GET_IMAGE),
    switchMap(action => this.appsService.getImage(this.getAppId(), action.payload).pipe(
      map(payload => new actions.GetAppImageCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetAppImageFailedAction, error)),
    )));

  @Effect() updateAppImage$ = this.actions$.pipe(
    ofType<actions.UpdateAppImageAction>(AppsActionTypes.UPDATE_IMAGE),
    switchMap(action => this.appsService.updateImage(this.getAppId(), action.payload).pipe(
      map(payload => new actions.UpdateAppImageCompleteAction(payload)),
      catchError(error => handleApiError(actions.UpdateAppImageFailedAction, error)),
    )));

  @Effect() generateAppImages$ = this.actions$.pipe(
    ofType<actions.GenerateAppImagesAction>(AppsActionTypes.GENERATE_IMAGES),
    switchMap(action => this.appsService.generateImages(this.getAppId(), action.payload).pipe(
      map(payload => new actions.GenerateAppImagesCompleteAction(payload)),
      catchError(error => handleApiError(actions.GenerateAppImagesFailedAction, error)),
    )));

  @Effect() removeAppImage$ = this.actions$.pipe(
    ofType<actions.RemoveAppImageAction>(AppsActionTypes.REMOVE_IMAGE),
    switchMap(action => this.appsService.removeImage(this.getAppId(), action.payload).pipe(
      map(payload => new actions.RemoveAppImageCompleteAction(payload)),
      catchError(error => handleApiError(actions.RemoveAppImageFailedAction, error)),
    )));

  @Effect() saveChanges$ = this.actions$.pipe(
    ofType<actions.SaveAppChangesAction>(AppsActionTypes.SAVE_CHANGES),
    switchMap(action => this.appsService.saveChanges(this.getAppId(), action.payload).pipe(
      map(() => new actions.SaveAppChangesCompleteAction()),
      catchError(error => handleApiError(actions.SaveAppChangesFailedAction, error)),
    )));

  @Effect() revertChanges$ = this.actions$.pipe(
    ofType<actions.RevertAppChangesAction>(AppsActionTypes.REVERT_CHANGES),
    switchMap(() => this.appsService.revertChanges(this.getAppId()).pipe(
      map(() => new actions.RevertAppChangesCompleteAction()),
      catchError(error => handleApiError(actions.RevertAppChangesFailedAction, error)),
    )));

  @Effect() getBuildSettings$ = this.actions$.pipe(
    ofType<actions.GetBuildSettingsAction>(AppsActionTypes.GET_BUILD_SETTINGS),
    switchMap(() => this.appsService.getBuildSettings(this.getAppId()).pipe(
      map(payload => new actions.GetBuildSettingsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetBuildSettingsFailedAction, error)),
    )));

  @Effect() updateBuildSettings$ = this.actions$.pipe(
    ofType<actions.UpdateBuildSettingsAction>(AppsActionTypes.UPDATE_BUILD_SETTINGS),
    switchMap(action => this.appsService.updateBuildSettings(this.getAppId(), action.payload).pipe(
      map(payload => new actions.UpdateBuildSettingsCompleteAction(payload)),
      catchError(error => handleApiError(actions.UpdateBuildSettingsFailedAction, error)),
    )));

  @Effect() getAppSettings$ = this.actions$.pipe(
    ofType<actions.GetAppSettingsAction>(AppsActionTypes.GET_APP_SETTINGS),
    switchMap(action => this.appsService.getAppSettings(action.payload).pipe(
      map(payload => new actions.GetAppSettingsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetAppSettingsFailedAction, error)),
    )));

  @Effect() updateAppSettings$ = this.actions$.pipe(
    ofType<actions.UpdateAppSettingsAction>(AppsActionTypes.UPDATE_APP_SETTINGS),
    switchMap(action => this.appsService.updateAppSettings(this.getAppId(), action.payload).pipe(
      map(payload => new actions.UpdateAppSettingsCompleteAction(payload)),
      catchError(error => handleApiError(actions.UpdateAppSettingsFailedAction, error)),
    )));

  @Effect() saveAppSettingsFirebaseIos$ = this.actions$.pipe(
    ofType<actions.SaveAppSettingsFirebaseIosAction>(AppsActionTypes.SAVE_APP_SETTINGS_FIREBASE_IOS),
    switchMap(action => this.appsService.saveAppSettingsFirebaseIos(this.getAppId(), action.payload).pipe(
      map(payload => new actions.SaveAppSettingsFirebaseIosCompleteAction(payload)),
      catchError(error => handleApiError(actions.SaveAppSettingsFirebaseIosFailedAction, error)),
    )));

  @Effect() updateFirebaseSettingsIos$ = this.actions$.pipe(
    ofType<actions.UpdateFirebaseSettingsIosAction>(AppsActionTypes.UPDATE_FIREBASE_SETTINGS_IOS),
    switchMap(action => {
      const appId = this.getAppId();
      return this.appsService.updateFirebaseSettingsIos(appId, action.file).pipe(
        map(payload => new actions.UpdateFirebaseSettingsIosCompleteAction()),
        tap(() => this.router.navigate(['/apps', appId, 'settings', 'app-settings'])),
        catchError(error => handleApiError(actions.UpdateFirebaseSettingsIosFailedAction, error)),
      );
    }));

  @Effect() autoUpdateFirebaseSettingsIos$ = this.actions$.pipe(
    ofType<actions.SaveAppSettingsFirebaseIosAction>(AppsActionTypes.SAVE_APP_SETTINGS_FIREBASE_IOS),
    map(action => new actions.UpdateFirebaseSettingsIosAction(action.payload)),
  );

  @Effect() saveAppAPNsIos$ = this.actions$.pipe(
    ofType<actions.SaveAppAPNsIosAction>(AppsActionTypes.SAVE_APP_APNS_IOS),
    switchMap(action => {
    	const appId = this.getAppId();
    	return this.appsService.saveAppAPNsIos(appId, action.keyId, action.payload).pipe(
    	  map(payload => new actions.SaveAppAPNsIosCompleteAction(payload)),
    	  tap(() => this.router.navigate(['/apps', appId, 'settings', 'app-settings'])),
    	  catchError(error => handleApiError(actions.SaveAppAPNsIosFailedAction, error)),
    	);
    }));

  @Effect() updateFacebook$ = this.actions$.pipe(
    ofType<actions.UpdateFacebookAction>(AppsActionTypes.UPDATE_FACEBOOK),
    switchMap(() => this.appsService.updateFacebook(this.getAppId()).pipe(
      map(() => new actions.UpdateFacebookCompleteAction()),
      catchError(error => handleApiError(actions.UpdateFacebookFailedAction, error)),
    )));

  @Effect() requestFacebookReview$ = this.actions$.pipe(
    ofType<actions.RequestFacebookReviewAction>(AppsActionTypes.REQUEST_FACEBOOK_REVIEW),
    switchMap(() => this.appsService.requestFacebookReview(this.getAppId()).pipe(
      map(() => new actions.RequestFacebookReviewCompleteAction()),
      catchError(error => handleApiError(actions.RequestFacebookReviewFailedAction, error)),
    )));

  @Effect() getAppMetaData = this.actions$.pipe(
    ofType<actions.GetAppMetaDataAction>(AppsActionTypes.GET_APP_METADATA),
    switchMap(value => this.appsService.getAppMetaData(value.payload).pipe(
      map(payload => new actions.GetAppMetaDataCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetAppMetaDataFailedAction, error)),
    )));

  @Effect() updateAppMetaData = this.actions$.pipe(
    ofType<actions.UpdateAppMetaDataAction>(AppsActionTypes.UPDATE_APP_METADATA),
    switchMap(value => this.appsService.updateAppMetaData(value.payload, value.appId).pipe(
      map(payload => new actions.UpdateAppMetaDataCompleteAction(payload)),
      catchError(error => handleApiError(actions.UpdateAppMetaDataFailedAction, error)),
    )));

  @Effect() getMetaDataDefaults = this.actions$.pipe(
    ofType<actions.GetMetaDataDefaultsAction>(AppsActionTypes.GET_METADATA_DEFAULTS),
    switchMap(value => this.appsService.getMetaDataDefaults(value.payload).pipe(
      map(payload => new actions.GetMetaDataDefaultsCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetMetaDataDefaultsFailedAction, error)),
    )));

  @Effect() bulkUpdateApps = this.actions$.pipe(
    ofType<actions.BulkUpdateAppsAction>(AppsActionTypes.BULK_UPDATE_APPS),
    switchMap(value => this.appsService.bulkUpdateApps(value.payload).pipe(
      map(() => new actions.BulkUpdateAppsCompleteAction()),
      catchError(error => handleApiError(actions.BulkUpdateAppsFailedAction, error)),
    )));

  constructor(private store: Store,
              private actions$: Actions,
              private router: Router,
              private route: ActivatedRoute,
              private appsService: AppsService) {
  }

  private getAppId() {
    return (this.route.snapshot.firstChild as ActivatedRouteSnapshot).params.appId;
  }
}
