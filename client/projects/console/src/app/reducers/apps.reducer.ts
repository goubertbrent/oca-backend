import { insertItem, removeItem, updateItem } from '../ngrx';
import { apiRequestInitial, apiRequestLoading, apiRequestSuccess } from '../../../framework/client/rpc';
import { AppsActions, AppsActionTypes } from '../actions';
import { App, GitStatus } from '../interfaces';
import { IAppsState, initialAppsState } from '../states';

export function appsReducer(state: IAppsState = initialAppsState, action: AppsActions): IAppsState {
  switch (action.type) {
    case AppsActionTypes.SEARCH_APPS:
      return {
        ...state,
        appsSearchParameters: action.payload,
      };
    case AppsActionTypes.SEARCH_APPS_INIT:
      return {
        ...state,
        appsStatus: apiRequestLoading,
      };
    case AppsActionTypes.SEARCH_APPS_COMPLETE:
      return {
        ...state,
        apps: action.payload,
        appsStatus: apiRequestSuccess,
      };
    case AppsActionTypes.SEARCH_APPS_FAILED:
      return {
        ...state,
        appsStatus: action.payload,
      };
    case AppsActionTypes.GET_APP:
      return {
        ...state,
        app: null,
      };
    case AppsActionTypes.GET_APPS:
      return {
        ...state,
        apps: [],
        appsStatus: apiRequestLoading,
      };
    case AppsActionTypes.GET_APPS_COMPLETE:
      return {
        ...state,
        apps: action.payload,
        appsStatus: apiRequestSuccess,
      };
    case AppsActionTypes.GET_APPS_FAILED:
      return {
        ...state,
        appsStatus: action.payload,
      };
    case AppsActionTypes.GET_PRODUCTION_APPS:
      return {
        ...state,
        productionApps: [],
        productionAppsStatus: apiRequestLoading,
      };
    case AppsActionTypes.GET_PRODUCTION_APPS_COMPLETE:
      return {
        ...state,
        productionApps: action.payload,
        productionAppsStatus: apiRequestSuccess,
      };
    case AppsActionTypes.GET_PRODUCTION_APPS_FAILED:
      return {
        ...state,
        productionAppsStatus: action.payload,
      };
    case AppsActionTypes.UPDATE_APP:
      return {
        ...state,
        updateAppStatus: apiRequestLoading,
      };
    case AppsActionTypes.UPDATE_APP_COMPLETE:
      const loadedApps = (state.apps as App[]).filter((a: App) => a.id !== (action.payload as App).id);
      return {
        ...state,
        app: action.payload,
        apps: [ ...loadedApps, action.payload ],
        updateAppStatus: apiRequestSuccess,
      };
    case AppsActionTypes.UPDATE_APP_FAILED:
      return {
        ...state,
        updateAppStatus: action.payload,
      };
    case AppsActionTypes.PATCH_APP:
      return {
        ...state,
        patchAppStatus: apiRequestLoading,
      };
    case AppsActionTypes.PATCH_APP_COMPLETE:
      return {
        ...state,
        app: action.payload.app,
        apps: updateItem(state.apps, action.payload.app, 'app_id'),
        rogerthatApp: action.payload.rogerthat_app,
        patchAppStatus: apiRequestSuccess,
      };
    case AppsActionTypes.PATCH_APP_FAILED:
      return {
        ...state,
        patchAppStatus: action.payload,
      };
    case AppsActionTypes.GET_APP_COMPLETE:
      return {
        ...state,
        app: action.payload,
      };
    case AppsActionTypes.GET_BUILDS:
      return { ...state, builds: [] };
    case AppsActionTypes.GET_BUILDS_COMPLETE:
      return { ...state, builds: action.payload };
    case AppsActionTypes.CREATE_BUILD:
      return {
        ...state,
        createBuildStatus: apiRequestLoading,
      };
    case AppsActionTypes.CREATE_BUILD_COMPLETE:
      return {
        ...state,
        builds: [ action.payload, ...state.builds ],
        createBuildStatus: apiRequestSuccess,
      };
    case AppsActionTypes.CREATE_BUILD_FAILED:
      return {
        ...state,
        createBuildStatus: action.payload,
      };
    case AppsActionTypes.CLEAR_BUILD:
      return {
        ...state,
        createBuildStatus: initialAppsState.createBuildStatus,
      };
    case AppsActionTypes.INIT_STORE_LISTING:
      return {
        ...state,
        updateAppStatus: initialAppsState.updateAppStatus,
      };
    case AppsActionTypes.GET_ROGERTHAT_APP:
      return {
        ...state,
        rogerthatApp: null,
      };
    case AppsActionTypes.GET_ROGERTHAT_APP_COMPLETE:
      return {
        ...state,
        rogerthatApp: action.payload,
      };
    case AppsActionTypes.UPDATE_ROGERTHAT_APP:
      return {
        ...state,
        rogerthatAppStatus: apiRequestLoading,
      };
    case AppsActionTypes.UPDATE_ROGERTHAT_APP_COMPLETE:
      return {
        ...state,
        rogerthatApp: action.payload,
        rogerthatAppStatus: apiRequestSuccess,
      };
    case AppsActionTypes.UPDATE_ROGERTHAT_APP_FAILED:
      return {
        ...state,
        rogerthatAppStatus: action.payload,
      };
    case AppsActionTypes.CLEAR_APP:
      return {
        ...state,
        app: initialAppsState.app,
        createAppStatus: initialAppsState.createAppStatus,
      };
    case AppsActionTypes.CREATE_APP:
      return { ...state, createAppStatus: apiRequestLoading };
    case AppsActionTypes.CREATE_APP_COMPLETE:
      return {
        ...state,
        app: action.payload,
        apps: insertItem(state.apps, action.payload),
        createAppStatus: apiRequestSuccess,
      };
    case AppsActionTypes.CREATE_APP_FAILED:
      return { ...state, createAppStatus: action.payload };
    case AppsActionTypes.GET_QR_CODE_TEMPLATES:
      return {
        ...state,
        qrCodeTemplates: [],
        qrCodeTemplatesStatus: apiRequestLoading,
        createQrCodeTemplatesStatus: apiRequestInitial,
      };
    case AppsActionTypes.GET_QR_CODE_TEMPLATES_COMPLETE:
      return {
        ...state,
        qrCodeTemplates: action.payload,
        qrCodeTemplatesStatus: apiRequestSuccess,
      };

    case AppsActionTypes.ADD_QR_CODE_TEMPLATE:
      return {
        ...state,
        createQrCodeTemplatesStatus: apiRequestLoading,
      };
    case AppsActionTypes.ADD_QR_CODE_TEMPLATE_COMPLETE:
      return {
        ...state,
        qrCodeTemplates: insertItem(state.qrCodeTemplates, action.payload),
        createQrCodeTemplatesStatus: apiRequestSuccess,
      };
    case AppsActionTypes.ADD_QR_CODE_TEMPLATE_FAILED:
      return {
        ...state,
        createQrCodeTemplatesStatus: action.payload,
      };
    case AppsActionTypes.REMOVE_QR_CODE_TEMPLATE:
      return {
        ...state,
        qrCodeTemplatesStatus: apiRequestLoading,
      };
    case AppsActionTypes.REMOVE_QR_CODE_TEMPLATE_COMPLETE:
      return {
        ...state,
        qrCodeTemplates: removeItem(state.qrCodeTemplates, action.payload, 'key_name'),
        qrCodeTemplatesStatus: apiRequestSuccess,
      };
    case AppsActionTypes.GET_QR_CODE_TEMPLATES_FAILED:
    case AppsActionTypes.REMOVE_QR_CODE_TEMPLATE_FAILED:
      return {
        ...state,
        qrCodeTemplatesStatus: action.payload,
      };
    case AppsActionTypes.GET_APP_ASSETS:
      return {
        ...state,
        appAssets: [],
        appAssetStatus: apiRequestLoading,
      };
    case AppsActionTypes.GET_APP_ASSETS_COMPLETE:
      return {
        ...state,
        appAssets: action.payload,
        appAssetStatus: apiRequestSuccess,
      };
    case AppsActionTypes.GET_APP_ASSETS_FAILED:
      return {
        ...state,
        appAssetStatus: action.payload,
      };
    case AppsActionTypes.CLEAR_APP_ASSET:
      return {
        ...state,
        appAssetStatus: initialAppsState.appAssetStatus,
      };
    case AppsActionTypes.CREATE_APP_ASSET:
      return {
        ...state,
        appAssetStatus: apiRequestLoading,
      };
    case AppsActionTypes.CREATE_APP_ASSET_COMPLETE:
      return {
        ...state,
        appAssets: updateItem(state.appAssets, action.payload, 'kind'),
        appAssetStatus: apiRequestSuccess,
      };
    case AppsActionTypes.REMOVE_APP_ASSET:
      return {
        ...state,
        appAssetStatus: apiRequestLoading,
      };
    case AppsActionTypes.REMOVE_APP_ASSET_COMPLETE:
      return {
        ...state,
        appAssets: removeItem(state.appAssets, action.payload, 'kind'),
        appAssetStatus: apiRequestSuccess,
      };
    case AppsActionTypes.REMOVE_APP_ASSET_FAILED:
    case AppsActionTypes.CREATE_APP_ASSET_FAILED:
      return {
        ...state,
        appAssetStatus: action.payload,
      };
    case AppsActionTypes.GET_DEFAULT_BRANDINGS:
      return {
        ...state,
        defaultBrandings: [],
        defaultBrandingsStatus: apiRequestLoading,
      };
    case AppsActionTypes.GET_DEFAULT_BRANDINGS_COMPLETE:
      return {
        ...state,
        defaultBrandings: action.payload,
        defaultBrandingsStatus: apiRequestSuccess,
      };
    case AppsActionTypes.GET_DEFAULT_BRANDINGS_FAILED:
      return {
        ...state,
        defaultBrandingsStatus: action.payload,
      };
    case AppsActionTypes.CREATE_DEFAULT_BRANDING:
      return {
        ...state,
        defaultBrandingEditStatus: apiRequestLoading,
      };
    case AppsActionTypes.CREATE_DEFAULT_BRANDING_COMPLETE:
      return {
        ...state,
        defaultBrandings: insertItem(state.defaultBrandings, action.payload),
        defaultBrandingEditStatus: apiRequestSuccess,
      };
    case AppsActionTypes.REMOVE_DEFAULT_BRANDING:
      return {
        ...state,
        defaultBrandingEditStatus: apiRequestLoading,
      };
    case AppsActionTypes.REMOVE_DEFAULT_BRANDING_COMPLETE:
      return {
        ...state,
        defaultBrandings: removeItem(state.defaultBrandings, action.payload, 'branding_type'),
        defaultBrandingEditStatus: apiRequestSuccess,
      };
    case AppsActionTypes.REMOVE_DEFAULT_BRANDING_FAILED:
    case AppsActionTypes.CREATE_DEFAULT_BRANDING_FAILED:
      return {
        ...state,
        defaultBrandingEditStatus: action.payload,
      };
    case AppsActionTypes.GET_COLORS:
      return {
        ...state,
        appColors: null,
        appColorsStatus: apiRequestLoading,
      };
    case AppsActionTypes.GET_COLORS_COMPLETE:
      return {
        ...state,
        appColors: action.payload,
        appColorsStatus: apiRequestSuccess,
      };
    case AppsActionTypes.GET_COLORS_FAILED:
      return {
        ...state,
        appColorsStatus: action.payload,
      };
    case AppsActionTypes.UPDATE_COLORS:
      return {
        ...state,
        appColorsStatus: apiRequestLoading,
      };
    case AppsActionTypes.UPDATE_COLORS_COMPLETE:
      return {
        ...state,
        appColors: action.payload,
        appColorsStatus: apiRequestSuccess,
        app: { ...state.app as App, git_status: GitStatus.DRAFT },
      };
    case AppsActionTypes.UPDATE_COLORS_FAILED:
      return {
        ...state,
        appColorsStatus: action.payload,
      };
    case AppsActionTypes.GET_SIDEBAR:
      return {
        ...state,
        appSidebar: null,
        appSidebarStatus: apiRequestLoading,
      };
    case AppsActionTypes.GET_SIDEBAR_COMPLETE:
      return {
        ...state,
        appSidebar: action.payload,
        appSidebarStatus: apiRequestSuccess,
      };
    case AppsActionTypes.GET_SIDEBAR_FAILED:
      return {
        ...state,
        appSidebarStatus: action.payload,
      };
    case AppsActionTypes.UPDATE_SIDEBAR:
      return {
        ...state,
        appSidebarStatus: apiRequestLoading,
      };
    case AppsActionTypes.UPDATE_SIDEBAR_COMPLETE:
      return {
        ...state,
        appSidebar: action.payload,
        appSidebarStatus: apiRequestSuccess,
        app: { ...state.app as App, git_status: GitStatus.DRAFT },
      };
    case AppsActionTypes.UPDATE_SIDEBAR_FAILED:
      return {
        ...state,
        appSidebarStatus: action.payload,
      };
    case AppsActionTypes.GET_IMAGES:
      return {
        ...state,
        images: [],
        imagesStatus: apiRequestLoading,
        generateImagesStatus: apiRequestInitial,
      };
    case AppsActionTypes.GET_IMAGES_COMPLETE:
      return {
        ...state,
        images: action.payload,
        imagesStatus: apiRequestSuccess,
      };
    case AppsActionTypes.GET_IMAGES_FAILED:
      return {
        ...state,
        imagesStatus: action.payload,
      };
    case AppsActionTypes.GET_IMAGE:
      return {
        ...state,
        image: initialAppsState.image,
        imageStatus: apiRequestLoading,
      };
    case AppsActionTypes.GET_IMAGE_COMPLETE:
      return {
        ...state,
        image: action.payload,
        imageStatus: apiRequestSuccess,
      };
    case AppsActionTypes.UPDATE_IMAGE:
      return {
        ...state,
        imageStatus: apiRequestLoading,
        app: { ...state.app as App, git_status: GitStatus.DRAFT },
      };
    case AppsActionTypes.UPDATE_IMAGE_COMPLETE:
      return {
        ...state,
        images: action.payload,
        imageStatus: apiRequestSuccess,
        app: { ...state.app as App, git_status: GitStatus.DRAFT },
      };
    case AppsActionTypes.UPDATE_IMAGE_FAILED:
      return {
        ...state,
        imageStatus: action.payload,
      };
    case AppsActionTypes.GENERATE_IMAGES:
      return {
        ...state,
        generateImagesStatus: apiRequestLoading,
        app: { ...state.app as App, git_status: GitStatus.DRAFT },
      };
    case AppsActionTypes.GENERATE_IMAGES_COMPLETE:
      return {
        ...state,
        generateImagesStatus: apiRequestSuccess,
        app: { ...state.app as App, git_status: GitStatus.DRAFT },
      };
    case AppsActionTypes.GENERATE_IMAGES_FAILED:
      return {
        ...state,
        generateImagesStatus: action.payload,
      };
    case AppsActionTypes.REMOVE_IMAGE_COMPLETE:
      return {
        ...state,
        images: updateItem(state.images, action.payload, 'type'),
      };
    case AppsActionTypes.SAVE_CHANGES:
      return {
        ...state,
        saveChangesStatus: apiRequestLoading,
      };
    case AppsActionTypes.SAVE_CHANGES_COMPLETE:
      return {
        ...state,
        app: { ...state.app as App, git_status: GitStatus.CLEAN },
      };
    case AppsActionTypes.SAVE_CHANGES_FAILED:
      return {
        ...state,
        saveChangesStatus: action.payload,
      };
    case AppsActionTypes.REVERT_CHANGES:
      return {
        ...state,
        revertChangesStatus: apiRequestLoading,
      };
    case AppsActionTypes.REVERT_CHANGES_COMPLETE:
      return {
        ...state,
        app: { ...state.app as App, git_status: GitStatus.CLEAN },
        revertChangesStatus: apiRequestSuccess,
      };
    case AppsActionTypes.REVERT_CHANGES_FAILED:
      return {
        ...state,
        revertChangesStatus: action.payload,
      };
    case AppsActionTypes.GET_BUILD_SETTINGS:
      return {
        ...state,
        buildSettings: initialAppsState.buildSettings,
        getBuildSettingsStatus: apiRequestLoading,
      };
    case AppsActionTypes.GET_BUILD_SETTINGS_COMPLETE:
      return {
        ...state,
        buildSettings: action.payload,
        getBuildSettingsStatus: apiRequestSuccess,
      };
    case AppsActionTypes.GET_BUILD_SETTINGS_FAILED:
      return {
        ...state,
        getBuildSettingsStatus: action.payload,
      };
    case AppsActionTypes.UPDATE_BUILD_SETTINGS:
      return {
        ...state,
        updateBuildSettingsStatus: apiRequestLoading,
      };
    case AppsActionTypes.UPDATE_BUILD_SETTINGS_COMPLETE:
      return {
        ...state,
        buildSettings: action.payload,
        updateBuildSettingsStatus: apiRequestSuccess,
        app: { ...state.app as App, git_status: GitStatus.DRAFT },
      };
    case AppsActionTypes.UPDATE_BUILD_SETTINGS_FAILED:
      return {
        ...state,
        updateBuildSettingsStatus: action.payload,
      };
    case AppsActionTypes.GET_APP_SETTINGS:
      return {
        ...state,
        appSettings: initialAppsState.appSettings,
        getAppSettingsStatus: apiRequestLoading,
      };
    case AppsActionTypes.GET_APP_SETTINGS_COMPLETE:
      return {
        ...state,
        appSettings: action.payload,
        getAppSettingsStatus: apiRequestSuccess,
      };
    case AppsActionTypes.GET_APP_SETTINGS_FAILED:
      return {
        ...state,
        getAppSettingsStatus: action.payload,
      };
    case AppsActionTypes.UPDATE_APP_SETTINGS:
      return {
        ...state,
        updateAppSettingsStatus: apiRequestLoading,
      };
    case AppsActionTypes.UPDATE_APP_SETTINGS_COMPLETE:
      return {
        ...state,
        appSettings: action.payload,
        updateAppSettingsStatus: apiRequestSuccess,
      };
    case AppsActionTypes.UPDATE_APP_SETTINGS_FAILED:
      return {
        ...state,
        updateAppSettingsStatus: action.payload,
      };
    case AppsActionTypes.SAVE_APP_SETTINGS_FIREBASE_IOS:
      return {
        ...state,
        saveAppSettingsFirebaseIosStatus: apiRequestLoading,
      };
    case AppsActionTypes.SAVE_APP_SETTINGS_FIREBASE_IOS_COMPLETE:
      return {
        ...state,
        appSettings: action.payload,
        saveAppSettingsFirebaseIosStatus: apiRequestSuccess,
      };
    case AppsActionTypes.SAVE_APP_SETTINGS_FIREBASE_IOS_FAILED:
      return {
        ...state,
        saveAppSettingsFirebaseIosStatus: action.payload,
      };
    case AppsActionTypes.UPDATE_FIREBASE_SETTINGS_IOS:
      return {
        ...state,
        updateFirebaseSettingsIosStatus: apiRequestLoading,
      };
    case AppsActionTypes.UPDATE_FIREBASE_SETTINGS_IOS_COMPLETE:
      return {
        ...state,
        updateFirebaseSettingsIosStatus: apiRequestSuccess,
      };
    case AppsActionTypes.UPDATE_FIREBASE_SETTINGS_IOS_FAILED:
      return {
        ...state,
        updateFirebaseSettingsIosStatus: action.payload,
      };
    case AppsActionTypes.UPDATE_FACEBOOK:
      return {
        ...state,
        updateFacebookStatus: apiRequestLoading,
      };
    case AppsActionTypes.UPDATE_FACEBOOK_COMPLETE:
      return {
        ...state,
        updateFacebookStatus: apiRequestSuccess,
      };
    case AppsActionTypes.UPDATE_FACEBOOK_FAILED:
      return {
        ...state,
        updateFacebookStatus: action.payload,
      };
    case AppsActionTypes.REQUEST_FACEBOOK_REVIEW:
      return {
        ...state,
        requestFacebookReviewStatus: apiRequestLoading,
      };
    case AppsActionTypes.REQUEST_FACEBOOK_REVIEW_COMPLETE:
      return {
        ...state,
        requestFacebookReviewStatus: apiRequestSuccess,
      };
    case AppsActionTypes.REQUEST_FACEBOOK_REVIEW_FAILED:
      return {
        ...state,
        requestFacebookReviewStatus: action.payload,
      };
    case AppsActionTypes.GET_APP_METADATA:
      return {
        ...state,
        appMetaData: initialAppsState.appMetaData,
        appMetaDataStatus: apiRequestLoading,
      };
    case AppsActionTypes.GET_APP_METADATA_COMPLETE:
      return {
        ...state,
        appMetaData: action.payload,
        appMetaDataStatus: apiRequestSuccess,
      };
    case AppsActionTypes.GET_APP_METADATA_FAILED:
      return {
        ...state,
        appMetaDataStatus: action.payload,
      };
    case AppsActionTypes.UPDATE_APP_METADATA:
      return {
        ...state,
        updateAppMetaDataStatus: apiRequestLoading,
      };
    case AppsActionTypes.UPDATE_APP_METADATA_COMPLETE:
      return {
        ...state,
        appMetaData: updateItem(state.appMetaData, action.payload, 'language'),
        updateAppMetaDataStatus: apiRequestSuccess,
      };
    case AppsActionTypes.UPDATE_APP_METADATA_FAILED:
      return {
        ...state,
        updateAppMetaDataStatus: action.payload,
      };
    case AppsActionTypes.GET_METADATA_DEFAULTS:
      return {
        ...state,
        appMetaDataStatus: apiRequestLoading,
      };
    case AppsActionTypes.GET_METADATA_DEFAULTS_COMPLETE:
      return {
        ...state,
        defaultMetaData: action.payload,
        appMetaDataStatus: apiRequestSuccess,
      };
    case AppsActionTypes.GET_METADATA_DEFAULTS_FAILED:
      return {
        ...state,
        appMetaDataStatus: action.payload,
      };
    case AppsActionTypes.BULK_UPDATE_APPS:
      return {
        ...state,
        bulkUpdateStatus: apiRequestLoading,
      };
    case AppsActionTypes.BULK_UPDATE_APPS_COMPLETE:
      return {
        ...state,
        bulkUpdateStatus: apiRequestSuccess,
      };
    case AppsActionTypes.BULK_UPDATE_APPS_FAILED:
      return {
        ...state,
        bulkUpdateStatus: action.payload,
      };
    case AppsActionTypes.CLEAR_BULK_UPDATE:
      return {
        ...state,
        bulkUpdateStatus: initialAppsState.bulkUpdateStatus,
      };
  }
  return state;
}
