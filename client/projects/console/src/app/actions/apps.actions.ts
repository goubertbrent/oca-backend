import { Action } from '@ngrx/store';
import { ApiRequestStatus } from '../../../framework/client/rpc';
import {
  App,
  AppAsset,
  AppColors,
  AppDetailPayload,
  AppImageInfo,
  AppMetaData,
  AppSearchParameters,
  AppSearchResult,
  AppSettings,
  AppSidebar,
  Build,
  BuildSettings,
  BulkUpdatePayload,
  CreateAppPayload,
  CreateBuildPayload,
  CreateDefaultBrandingPayload,
  DefaultBranding,
  EditAppAssetPayload,
  GenerateImagesPayload,
  PatchAppCompletePayload,
  PatchAppPayload,
  QrCodeTemplate,
  RogerthatApp,
  SaveChangesPayload,
  UpdateAppImagePayload,
} from '../interfaces';

export const enum AppsActionTypes {
  SEARCH_APPS = '[RCC:apps] Search apps',
  SEARCH_APPS_INIT = '[RCC:apps] Search apps started',
  SEARCH_APPS_COMPLETE = '[RCC:apps] Search apps complete',
  SEARCH_APPS_FAILED = '[RCC:apps] Search apps failed',
  CLEAR_APP = '[RCC:apps] Clear app',
  GET_APP = '[RCC:apps] Get app',
  GET_APP_COMPLETE = '[RCC:apps] Get app complete',
  GET_APP_FAILED = '[RCC:apps] Get app failed',
  GET_APPS = '[RCC:apps] Get apps',
  GET_PRODUCTION_APPS = '[RCC:apps] Get production apps',
  GET_PRODUCTION_APPS_COMPLETE = '[RCC:apps] Get production apps complete',
  GET_PRODUCTION_APPS_FAILED = '[RCC:apps] Get apps production failed',
  GET_APPS_COMPLETE = '[RCC:apps] Get apps complete',
  GET_APPS_FAILED = '[RCC:apps] Get apps failed',
  CREATE_APP = '[RCC:apps] Create app',
  CREATE_APP_COMPLETE = '[RCC:apps] Create app complete',
  CREATE_APP_FAILED = '[RCC:apps] Create app failed',
  UPDATE_APP = '[RCC:apps] Update app',
  UPDATE_APP_COMPLETE = '[RCC:apps] Update app complete',
  UPDATE_APP_FAILED = '[RCC:apps] Update app failed',
  PATCH_APP = '[RCC:apps] Patch app',
  PATCH_APP_COMPLETE = '[RCC:apps] Patch app complete',
  PATCH_APP_FAILED = '[RCC:apps] Patch app failed',
  DELETE_APP = '[RCC:apps] Delete app',
  DELETE_APP_COMPLETE = '[RCC:apps] Delete app complete',
  DELETE_APP_FAILED = '[RCC:apps] Delete app failed',
  GET_BUILDS = '[RCC:apps] Get builds',
  GET_BUILDS_COMPLETE = '[RCC:apps] Get builds complete',
  GET_BUILDS_FAILED = '[RCC:apps] Get builds failed',
  CREATE_BUILD = '[RCC:apps] Create build',
  CREATE_BUILD_COMPLETE = '[RCC:apps] Create build complete',
  CREATE_BUILD_FAILED = '[RCC:apps] Create build failed',
  CLEAR_BUILD = '[RCC:apps] Clear build',
  INIT_STORE_LISTING = '[RCC:apps] Init store listing',
  GET_ROGERTHAT_APP = '[RCC:apps] Get rogerthat app',
  GET_ROGERTHAT_APP_COMPLETE = '[RCC:apps] Get rogerthat app complete',
  GET_ROGERTHAT_APP_FAILED = '[RCC:apps] Get rogerthat app failed',
  UPDATE_ROGERTHAT_APP = '[RCC:apps] Update rogerthat app',
  UPDATE_ROGERTHAT_APP_COMPLETE = '[RCC:apps] Update rogerthat app complete',
  UPDATE_ROGERTHAT_APP_FAILED = '[RCC:apps] Update rogerthat app failed',
  GET_QR_CODE_TEMPLATES = '[RCC:apps] Get app qr code templates',
  GET_QR_CODE_TEMPLATES_COMPLETE = '[RCC:apps] Get app qr code templates complete',
  GET_QR_CODE_TEMPLATES_FAILED = '[RCC:apps] Get app qr code templates failed',
  ADD_QR_CODE_TEMPLATE = '[RCC:apps] Add app qr code templates',
  ADD_QR_CODE_TEMPLATE_COMPLETE = '[RCC:apps] Add app qr code templates complete',
  ADD_QR_CODE_TEMPLATE_FAILED = '[RCC:apps] Add app qr code templates failed',
  REMOVE_QR_CODE_TEMPLATE = '[RCC:apps] Remove app qr code templates',
  REMOVE_QR_CODE_TEMPLATE_COMPLETE = '[RCC:apps] Remove app qr code templates complete',
  REMOVE_QR_CODE_TEMPLATE_FAILED = '[RCC:apps] Remove app qr code templates failed',
  CREATE_DEFAULT_QR_CODE_TEMPLATE = '[RCC:apps] Create default QR code template',
  CREATE_DEFAULT_QR_CODE_TEMPLATE_COMPLETE = '[RCC:apps] Create default QR code template complete',
  CREATE_DEFAULT_QR_CODE_TEMPLATE_FAILED = '[RCC:apps] Create default QR code template failed',
  GET_APP_ASSETS = '[RCC:apps] Get app assets',
  GET_APP_ASSETS_COMPLETE = '[RCC:apps] Get app assets complete',
  GET_APP_ASSETS_FAILED = '[RCC:apps] Get app assets failed',
  CLEAR_APP_ASSET = '[RCC:apps] Clear app asset',
  CREATE_APP_ASSET = '[RCC:apps] Create app asset',
  CREATE_APP_ASSET_COMPLETE = '[RCC:apps] Create app asset complete',
  CREATE_APP_ASSET_FAILED = '[RCC:apps] Create app asset failed',
  REMOVE_APP_ASSET = '[RCC:apps] Remove app asset',
  REMOVE_APP_ASSET_COMPLETE = '[RCC:apps] Remove app asset complete',
  REMOVE_APP_ASSET_FAILED = '[RCC:apps] Remove app asset failed',
  GET_DEFAULT_BRANDINGS = '[RCC:apps] Get default brandings',
  GET_DEFAULT_BRANDINGS_COMPLETE = '[RCC:apps] Get default brandings complete',
  GET_DEFAULT_BRANDINGS_FAILED = '[RCC:apps] Get default brandings failed',
  CREATE_DEFAULT_BRANDING = '[RCC:apps] Create default branding',
  CREATE_DEFAULT_BRANDING_COMPLETE = '[RCC:apps] Create default branding complete',
  CREATE_DEFAULT_BRANDING_FAILED = '[RCC:apps] Create default branding failed',
  REMOVE_DEFAULT_BRANDING = '[RCC:apps] Remove default branding',
  REMOVE_DEFAULT_BRANDING_COMPLETE = '[RCC:apps] Remove default branding complete',
  REMOVE_DEFAULT_BRANDING_FAILED = '[RCC:apps] Remove default branding failed',
  GET_COLORS = '[RCC:apps] Get colors',
  GET_COLORS_COMPLETE = '[RCC:apps] Get colors complete',
  GET_COLORS_FAILED = '[RCC:apps] Get colors failed',
  UPDATE_COLORS = '[RCC:apps] Update colors',
  UPDATE_COLORS_COMPLETE = '[RCC:apps] Update colors complete',
  UPDATE_COLORS_FAILED = '[RCC:apps] Update colors failed',
  GET_SIDEBAR = '[RCC:apps] Get sidebar',
  GET_SIDEBAR_COMPLETE = '[RCC:apps] Get sidebar complete',
  GET_SIDEBAR_FAILED = '[RCC:apps] Get sidebar failed',
  UPDATE_SIDEBAR = '[RCC:apps] Update sidebar',
  UPDATE_SIDEBAR_COMPLETE = '[RCC:apps] Update sidebar complete',
  UPDATE_SIDEBAR_FAILED = '[RCC:apps] Update sidebar failed',
  GET_IMAGES = '[RCC:apps] Get images',
  GET_IMAGES_COMPLETE = '[RCC:apps] Get images complete',
  GET_IMAGES_FAILED = '[RCC:apps] Get images failed',
  GET_IMAGE = '[RCC:apps] Get image',
  GET_IMAGE_COMPLETE = '[RCC:apps] Get image complete',
  GET_IMAGE_FAILED = '[RCC:apps] Get image failed',
  UPDATE_IMAGE = '[RCC:apps] Update image',
  UPDATE_IMAGE_COMPLETE = '[RCC:apps] Update image complete',
  UPDATE_IMAGE_FAILED = '[RCC:apps] Update image failed',
  GENERATE_IMAGES = '[RCC:apps] Generate images',
  GENERATE_IMAGES_COMPLETE = '[RCC:apps] Generate images complete',
  GENERATE_IMAGES_FAILED = '[RCC:apps] Generate images failed',
  REMOVE_IMAGE = '[RCC:apps] Delete image',
  REMOVE_IMAGE_COMPLETE = '[RCC:apps] Delete image complete',
  REMOVE_IMAGE_FAILED = '[RCC:apps] Delete image failed',
  SAVE_CHANGES = '[RCC:apps] Save changes',
  SAVE_CHANGES_COMPLETE = '[RCC:apps] Save changes complete',
  SAVE_CHANGES_FAILED = '[RCC:apps] Save changes failed',
  REVERT_CHANGES = '[RCC:apps] Revert changes',
  REVERT_CHANGES_COMPLETE = '[RCC:apps] Revert changes complete',
  REVERT_CHANGES_FAILED = '[RCC:apps] Revert changes failed',
  GET_BUILD_SETTINGS = '[RCC:apps] Get build settings',
  GET_BUILD_SETTINGS_COMPLETE = '[RCC:apps] Get build settings complete',
  GET_BUILD_SETTINGS_FAILED = '[RCC:apps] Get build settings failed',
  UPDATE_BUILD_SETTINGS = '[RCC:apps] Update build settings',
  UPDATE_BUILD_SETTINGS_COMPLETE = '[RCC:apps] Update build settings complete',
  UPDATE_BUILD_SETTINGS_FAILED = '[RCC:apps] Update build settings failed',
  GET_APP_SETTINGS = '[RCC:apps] Get app settings',
  GET_APP_SETTINGS_COMPLETE = '[RCC:apps] Get app settings complete',
  GET_APP_SETTINGS_FAILED = '[RCC:apps] Get app settings failed',
  UPDATE_APP_SETTINGS = '[RCC:apps] Update app settings',
  UPDATE_APP_SETTINGS_COMPLETE = '[RCC:apps] Update app settings complete',
  UPDATE_APP_SETTINGS_FAILED = '[RCC:apps] Update app settings failed',
  SAVE_APP_SETTINGS_FIREBASE_IOS = '[RCC:apps] Save app settings firebase ios',
  SAVE_APP_SETTINGS_FIREBASE_IOS_COMPLETE = '[RCC:apps] Save app settings firebase ios complete',
  SAVE_APP_SETTINGS_FIREBASE_IOS_FAILED = '[RCC:apps] Save app settings firebase ios failed',
  UPDATE_FIREBASE_SETTINGS_IOS = '[RCC:apps] Update firebase settings ios',
  UPDATE_FIREBASE_SETTINGS_IOS_COMPLETE = '[RCC:apps] Update firebase settings ios complete',
  UPDATE_FIREBASE_SETTINGS_IOS_FAILED = '[RCC:apps] Update firebase settings ios failed',
  SAVE_APP_APNS_IOS = '[RCC:apps] Save app apns ios',
  SAVE_APP_APNS_IOS_COMPLETE = '[RCC:apps] Save app apns ios complete',
  SAVE_APP_APNS_IOS_FAILED = '[RCC:apps] Save app apns ios failed',
  UPDATE_FACEBOOK = '[RCC:apps] Update facebook',
  UPDATE_FACEBOOK_COMPLETE = '[RCC:apps] Update facebook complete',
  UPDATE_FACEBOOK_FAILED = '[RCC:apps] Update facebook failed',
  REQUEST_FACEBOOK_REVIEW = '[RCC:apps] Request facebook review',
  REQUEST_FACEBOOK_REVIEW_COMPLETE = '[RCC:apps] Request facebook review complete',
  REQUEST_FACEBOOK_REVIEW_FAILED = '[RCC:apps] Request facebook review failed',
  GET_APP_METADATA = '[RCC:apps] Get app meta data',
  GET_APP_METADATA_COMPLETE = '[RCC:apps] Get app meta data complete',
  GET_APP_METADATA_FAILED = '[RCC:apps] Get app meta data failed',
  UPDATE_APP_METADATA = '[RCC:apps] Update app meta data',
  UPDATE_APP_METADATA_COMPLETE = '[RCC:apps] Update app meta data complete',
  UPDATE_APP_METADATA_FAILED = '[RCC:apps] Update app meta data failed',
  GET_METADATA_DEFAULTS = '[RCC:apps] Get meta data defaults',
  GET_METADATA_DEFAULTS_COMPLETE = '[RCC:apps] Get meta data defaults complete',
  GET_METADATA_DEFAULTS_FAILED = '[RCC:apps] Get meta data defaults failed',
  BULK_UPDATE_APPS = '[RCC:apps] Bulk update apps',
  BULK_UPDATE_APPS_COMPLETE = '[RCC:apps] Bulk update apps complete',
  BULK_UPDATE_APPS_FAILED = '[RCC:apps] Bulk update apps failed',
  CLEAR_BULK_UPDATE = '[RCC:apps] Clear bulk update',
}

export class SearchAppsAction implements Action {
  readonly type = AppsActionTypes.SEARCH_APPS;

  constructor(public payload: AppSearchParameters) {
  }
}

export class SearchAppsInitAction implements Action {
  readonly type = AppsActionTypes.SEARCH_APPS_INIT;
}

export class SearchAppsCompleteAction implements Action {
  readonly type = AppsActionTypes.SEARCH_APPS_COMPLETE;

  constructor(public payload: Array<AppSearchResult>) {
  }
}

export class SearchAppsFailedAction implements Action {
  readonly type = AppsActionTypes.SEARCH_APPS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class ClearAppAction implements Action {
  readonly type = AppsActionTypes.CLEAR_APP;
}

export class GetAppAction implements Action {
  readonly type = AppsActionTypes.GET_APP;

  constructor(public payload: string) {
  }
}

export class GetAppCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_APP_COMPLETE;

  constructor(public payload: App) {
  }
}

export class GetAppFailedAction implements Action {
  readonly type = AppsActionTypes.GET_APP_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetAppsAction implements Action {
  readonly type = AppsActionTypes.GET_APPS;
}

export class GetAppsCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_APPS_COMPLETE;

  constructor(public payload: App[]) {
  }
}

export class GetAppsFailedAction implements Action {
  readonly type = AppsActionTypes.GET_APPS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetProductionAppsAction implements Action {
  readonly type = AppsActionTypes.GET_PRODUCTION_APPS;
}

export class GetProductionAppsCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_PRODUCTION_APPS_COMPLETE;

  constructor(public payload: App[]) {
  }
}

export class GetProductionAppsFailedAction implements Action {
  readonly type = AppsActionTypes.GET_PRODUCTION_APPS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class CreateAppAction implements Action {
  readonly type = AppsActionTypes.CREATE_APP;

  constructor(public payload: CreateAppPayload) {
  }
}

export class CreateAppCompleteAction implements Action {
  readonly type = AppsActionTypes.CREATE_APP_COMPLETE;

  constructor(public payload: App) {
  }
}

export class CreateAppFailedAction implements Action {
  readonly type = AppsActionTypes.CREATE_APP_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateAppAction implements Action {
  readonly type = AppsActionTypes.UPDATE_APP;

  constructor(public payload: App) {
  }
}

export class UpdateAppCompleteAction implements Action {
  readonly type = AppsActionTypes.UPDATE_APP_COMPLETE;

  constructor(public payload: App) {
  }
}

export class UpdateAppFailedAction implements Action {
  readonly type = AppsActionTypes.UPDATE_APP_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class PatchAppAction implements Action {
  readonly type = AppsActionTypes.PATCH_APP;

  constructor(public payload: PatchAppPayload) {
  }
}

export class PatchAppCompleteAction implements Action {
  readonly type = AppsActionTypes.PATCH_APP_COMPLETE;

  constructor(public payload: PatchAppCompletePayload) {
  }
}

export class PatchAppFailedAction implements Action {
  readonly type = AppsActionTypes.PATCH_APP_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class DeleteAppAction implements Action {
  readonly type = AppsActionTypes.DELETE_APP;

  constructor(public payload: App) {
  }
}

export class DeleteAppCompleteAction implements Action {
  readonly type = AppsActionTypes.DELETE_APP_COMPLETE;

  constructor(public payload: App) {
  }
}

export class DeleteAppFailedAction implements Action {
  readonly type = AppsActionTypes.DELETE_APP_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetBuildsAction implements Action {
  readonly type = AppsActionTypes.GET_BUILDS;

  constructor(public payload: string) {
  }
}

export class GetBuildsCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_BUILDS_COMPLETE;

  constructor(public payload: Array<Build>) {
  }
}

export class GetBuildsFailedAction implements Action {
  readonly type = AppsActionTypes.GET_BUILDS_FAILED;
}

export class CreateBuildAction implements Action {
  readonly type = AppsActionTypes.CREATE_BUILD;

  constructor(public payload: { app_id: string, data: CreateBuildPayload }) {
  }
}

export class CreateBuildCompleteAction implements Action {
  readonly type = AppsActionTypes.CREATE_BUILD_COMPLETE;

  constructor(public payload: Build) {
  }
}

export class CreateBuildFailedAction implements Action {
  readonly type = AppsActionTypes.CREATE_BUILD_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class ClearBuildAction implements Action {
  readonly type = AppsActionTypes.CLEAR_BUILD;
}

export class InitStoreListingAction implements Action {
  readonly type = AppsActionTypes.INIT_STORE_LISTING;
}


export class GetRogerthatAppAction implements Action {
  readonly type = AppsActionTypes.GET_ROGERTHAT_APP;

  constructor(public payload: AppDetailPayload) {
  }
}

export class GetRogerthatAppCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_ROGERTHAT_APP_COMPLETE;

  constructor(public payload: RogerthatApp) {
  }
}

export class GetRogerthatAppFailedAction implements Action {
  readonly type = AppsActionTypes.GET_ROGERTHAT_APP_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateRogerthatAppAction implements Action {
  readonly type = AppsActionTypes.UPDATE_ROGERTHAT_APP;

  constructor(public payload: RogerthatApp) {
  }
}

export class UpdateRogerthatAppCompleteAction implements Action {
  readonly type = AppsActionTypes.UPDATE_ROGERTHAT_APP_COMPLETE;

  constructor(public payload: RogerthatApp) {
  }
}

export class UpdateRogerthatAppFailedAction implements Action {
  readonly type = AppsActionTypes.UPDATE_ROGERTHAT_APP_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetQrCodeTemplatesAction implements Action {
  readonly type = AppsActionTypes.GET_QR_CODE_TEMPLATES;

  constructor(public payload: AppDetailPayload) {
  }
}

export class GetQrCodeTemplatesCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_QR_CODE_TEMPLATES_COMPLETE;

  constructor(public payload: QrCodeTemplate[]) {
  }
}

export class GetQrCodeTemplatesFailedAction implements Action {
  readonly type = AppsActionTypes.GET_QR_CODE_TEMPLATES_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class AddQrCodeTemplateAction implements Action {
  readonly type = AppsActionTypes.ADD_QR_CODE_TEMPLATE;

  constructor(public payload: {data: QrCodeTemplate, appId: string}) {
  }
}

export class AddQrCodeTemplateCompleteAction implements Action {
  readonly type = AppsActionTypes.ADD_QR_CODE_TEMPLATE_COMPLETE;

  constructor(public payload: QrCodeTemplate) {
  }
}

export class AddQrCodeTemplateFailedAction implements Action {
  readonly type = AppsActionTypes.ADD_QR_CODE_TEMPLATE_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class CreateDefaultQrCodeTemplateAction implements Action {
  readonly type = AppsActionTypes.CREATE_DEFAULT_QR_CODE_TEMPLATE;

  constructor(public payload: { appId: string, data: string }) {
  }
}

export class CreateDefaultQrCodeTemplateCompleteAction implements Action {
  readonly type = AppsActionTypes.CREATE_DEFAULT_QR_CODE_TEMPLATE_COMPLETE;

  constructor(public payload: QrCodeTemplate) {
  }
}

export class CreateDefaultQrCodeTemplateFailedAction implements Action {
  readonly type = AppsActionTypes.CREATE_DEFAULT_QR_CODE_TEMPLATE_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RemoveQrCodeTemplateAction implements Action {
  readonly type = AppsActionTypes.REMOVE_QR_CODE_TEMPLATE;

  constructor(public payload: { appId: string; data: QrCodeTemplate }) {
  }
}

export class RemoveQrCodeTemplateCompleteAction implements Action {
  readonly type = AppsActionTypes.REMOVE_QR_CODE_TEMPLATE_COMPLETE;

  constructor(public payload: QrCodeTemplate) {
  }
}

export class RemoveQrCodeTemplateFailedAction implements Action {
  readonly type = AppsActionTypes.REMOVE_QR_CODE_TEMPLATE_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetAppAssetsAction implements Action {
  readonly type = AppsActionTypes.GET_APP_ASSETS;

  constructor(public payload: AppDetailPayload) {
  }
}

export class GetAppAssetsCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_APP_ASSETS_COMPLETE;

  constructor(public payload: AppAsset[]) {
  }
}

export class ClearAppResourceAction implements Action {
  readonly type = AppsActionTypes.CLEAR_APP_ASSET;
}

export class GetAppAssetsFailedAction implements Action {
  readonly type = AppsActionTypes.GET_APP_ASSETS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class CreateAppAssetAction implements Action {
  readonly type = AppsActionTypes.CREATE_APP_ASSET;

  constructor(public payload: EditAppAssetPayload) {
  }
}

export class CreateAppAssetCompleteAction implements Action {
  readonly type = AppsActionTypes.CREATE_APP_ASSET_COMPLETE;

  constructor(public payload: AppAsset) {
  }
}


export class CreateAppAssetFailedAction implements Action {
  readonly type = AppsActionTypes.CREATE_APP_ASSET_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RemoveAppAssetAction implements Action {
  readonly type = AppsActionTypes.REMOVE_APP_ASSET;

  constructor(public payload: { appId: string, data: AppAsset }) {
  }
}

export class RemoveAppAssetCompleteAction implements Action {
  readonly type = AppsActionTypes.REMOVE_APP_ASSET_COMPLETE;

  constructor(public payload: AppAsset) {
  }
}


export class RemoveAppAssetFailedAction implements Action {
  readonly type = AppsActionTypes.REMOVE_APP_ASSET_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetDefaultBrandingsAction implements Action {
  readonly type = AppsActionTypes.GET_DEFAULT_BRANDINGS;

  constructor(public payload: AppDetailPayload) {
  }
}

export class GetDefaultBrandingsCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_DEFAULT_BRANDINGS_COMPLETE;

  constructor(public payload: DefaultBranding[]) {
  }
}


export class GetDefaultBrandingsFailedAction implements Action {
  readonly type = AppsActionTypes.GET_DEFAULT_BRANDINGS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class CreateDefaultBrandingAction implements Action {
  readonly type = AppsActionTypes.CREATE_DEFAULT_BRANDING;

  constructor(public payload: CreateDefaultBrandingPayload) {
  }
}

export class CreateDefaultBrandingCompleteAction implements Action {
  readonly type = AppsActionTypes.CREATE_DEFAULT_BRANDING_COMPLETE;

  constructor(public payload: DefaultBranding) {
  }
}


export class CreateDefaultBrandingFailedAction implements Action {
  readonly type = AppsActionTypes.CREATE_DEFAULT_BRANDING_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RemoveDefaultBrandingAction implements Action {
  readonly type = AppsActionTypes.REMOVE_DEFAULT_BRANDING;

  constructor(public payload: { appId: string, data: DefaultBranding }) {
  }
}

export class RemoveDefaultBrandingCompleteAction implements Action {
  readonly type = AppsActionTypes.REMOVE_DEFAULT_BRANDING_COMPLETE;

  constructor(public payload: DefaultBranding) {
  }
}

export class RemoveDefaultBrandingFailedAction implements Action {
  readonly type = AppsActionTypes.REMOVE_DEFAULT_BRANDING_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetAppColorsAction implements Action {
  readonly type = AppsActionTypes.GET_COLORS;
}

export class GetAppColorsCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_COLORS_COMPLETE;

  constructor(public payload: AppColors) {
  }
}

export class GetAppColorsFailedAction implements Action {
  readonly type = AppsActionTypes.GET_COLORS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateAppColorsAction implements Action {
  readonly type = AppsActionTypes.UPDATE_COLORS;

  constructor(public payload: AppColors) {
  }
}

export class UpdateAppColorsCompleteAction implements Action {
  readonly type = AppsActionTypes.UPDATE_COLORS_COMPLETE;

  constructor(public payload: AppColors) {
  }
}

export class UpdateAppColorsFailedAction implements Action {
  readonly type = AppsActionTypes.UPDATE_COLORS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetAppSidebarAction implements Action {
  readonly type = AppsActionTypes.GET_SIDEBAR;
}

export class GetAppSidebarCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_SIDEBAR_COMPLETE;

  constructor(public payload: AppSidebar) {
  }
}

export class GetAppSidebarFailedAction implements Action {
  readonly type = AppsActionTypes.GET_SIDEBAR_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateAppSidebarAction implements Action {
  readonly type = AppsActionTypes.UPDATE_SIDEBAR;

  constructor(public payload: AppSidebar) {
  }
}

export class UpdateAppSidebarCompleteAction implements Action {
  readonly type = AppsActionTypes.UPDATE_SIDEBAR_COMPLETE;

  constructor(public payload: AppSidebar) {
  }
}

export class UpdateAppSidebarFailedAction implements Action {
  readonly type = AppsActionTypes.UPDATE_SIDEBAR_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetAppImagesAction implements Action {
  readonly type = AppsActionTypes.GET_IMAGES;
}


export class GetAppImagesCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_IMAGES_COMPLETE;

  constructor(public payload: AppImageInfo[]) {
  }
}

export class GetAppImagesFailedAction implements Action {
  readonly type = AppsActionTypes.GET_IMAGES_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetAppImageAction implements Action {
  readonly type = AppsActionTypes.GET_IMAGE;

  constructor(public payload: string) {
  }
}

export class GetAppImageCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_IMAGE_COMPLETE;

  constructor(public payload: AppImageInfo) {
  }
}

export class GetAppImageFailedAction implements Action {
  readonly type = AppsActionTypes.GET_IMAGE_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateAppImageAction implements Action {
  readonly type = AppsActionTypes.UPDATE_IMAGE;

  constructor(public payload: UpdateAppImagePayload) {
  }
}

export class UpdateAppImageCompleteAction implements Action {
  readonly type = AppsActionTypes.UPDATE_IMAGE_COMPLETE;

  constructor(public payload: AppImageInfo[]) {
  }
}

export class UpdateAppImageFailedAction implements Action {
  readonly type = AppsActionTypes.UPDATE_IMAGE_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GenerateAppImagesAction implements Action {
  readonly type = AppsActionTypes.GENERATE_IMAGES;

  constructor(public payload: GenerateImagesPayload) {
  }
}

export class GenerateAppImagesCompleteAction implements Action {
  readonly type = AppsActionTypes.GENERATE_IMAGES_COMPLETE;

  constructor(public payload: AppImageInfo[]) {

  }
}

export class GenerateAppImagesFailedAction implements Action {
  readonly type = AppsActionTypes.GENERATE_IMAGES_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RemoveAppImageAction implements Action {
  readonly type = AppsActionTypes.REMOVE_IMAGE;

  constructor(public payload: AppImageInfo) {
  }
}

export class RemoveAppImageCompleteAction implements Action {
  readonly type = AppsActionTypes.REMOVE_IMAGE_COMPLETE;

  constructor(public payload: AppImageInfo) {
  }
}

export class RemoveAppImageFailedAction implements Action {
  readonly type = AppsActionTypes.REMOVE_IMAGE_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class SaveAppChangesAction implements Action {
  readonly type = AppsActionTypes.SAVE_CHANGES;

  constructor(public payload: SaveChangesPayload) {
  }
}

export class SaveAppChangesCompleteAction implements Action {
  readonly type = AppsActionTypes.SAVE_CHANGES_COMPLETE;
}

export class SaveAppChangesFailedAction implements Action {
  readonly type = AppsActionTypes.SAVE_CHANGES_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RevertAppChangesAction implements Action {
  readonly type = AppsActionTypes.REVERT_CHANGES;
}

export class RevertAppChangesCompleteAction implements Action {
  readonly type = AppsActionTypes.REVERT_CHANGES_COMPLETE;
}

export class RevertAppChangesFailedAction implements Action {
  readonly type = AppsActionTypes.REVERT_CHANGES_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetBuildSettingsAction implements Action {
  readonly type = AppsActionTypes.GET_BUILD_SETTINGS;
}

export class GetBuildSettingsCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_BUILD_SETTINGS_COMPLETE;

  constructor(public payload: BuildSettings) {
  }
}

export class GetBuildSettingsFailedAction implements Action {
  readonly type = AppsActionTypes.GET_BUILD_SETTINGS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateBuildSettingsAction implements Action {
  readonly type = AppsActionTypes.UPDATE_BUILD_SETTINGS;

  constructor(public payload: BuildSettings) {
  }
}

export class UpdateBuildSettingsCompleteAction implements Action {
  readonly type = AppsActionTypes.UPDATE_BUILD_SETTINGS_COMPLETE;

  constructor(public payload: BuildSettings) {
  }
}

export class UpdateBuildSettingsFailedAction implements Action {
  readonly type = AppsActionTypes.UPDATE_BUILD_SETTINGS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetAppSettingsAction implements Action {
  readonly type = AppsActionTypes.GET_APP_SETTINGS;

  constructor(public payload: AppDetailPayload) {
  }
}

export class GetAppSettingsCompleteAction implements Action {
  readonly type = AppsActionTypes.GET_APP_SETTINGS_COMPLETE;

  constructor(public payload: AppSettings) {
  }
}

export class GetAppSettingsFailedAction implements Action {
  readonly type = AppsActionTypes.GET_APP_SETTINGS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateAppSettingsAction implements Action {
  readonly type = AppsActionTypes.UPDATE_APP_SETTINGS;

  constructor(public payload: AppSettings) {
  }
}

export class UpdateAppSettingsCompleteAction implements Action {
  readonly type = AppsActionTypes.UPDATE_APP_SETTINGS_COMPLETE;

  constructor(public payload: AppSettings) {
  }
}

export class UpdateAppSettingsFailedAction implements Action {
  readonly type = AppsActionTypes.UPDATE_APP_SETTINGS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class SaveAppSettingsFirebaseIosAction implements Action {
  readonly type = AppsActionTypes.SAVE_APP_SETTINGS_FIREBASE_IOS;

  constructor(public payload: string) {
  }
}

export class SaveAppSettingsFirebaseIosCompleteAction implements Action {
  readonly type = AppsActionTypes.SAVE_APP_SETTINGS_FIREBASE_IOS_COMPLETE;

  constructor(public payload: AppSettings) {
  }
}

export class SaveAppSettingsFirebaseIosFailedAction implements Action {
  readonly type = AppsActionTypes.SAVE_APP_SETTINGS_FIREBASE_IOS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateFirebaseSettingsIosAction implements Action {
  readonly type = AppsActionTypes.UPDATE_FIREBASE_SETTINGS_IOS;

  constructor(public file: any) {
  }
}

export class UpdateFirebaseSettingsIosCompleteAction implements Action {
  readonly type = AppsActionTypes.UPDATE_FIREBASE_SETTINGS_IOS_COMPLETE;

  constructor() {
  }
}

export class UpdateFirebaseSettingsIosFailedAction implements Action {
  readonly type = AppsActionTypes.UPDATE_FIREBASE_SETTINGS_IOS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class SaveAppAPNsIosAction implements Action {
  readonly type = AppsActionTypes.SAVE_APP_APNS_IOS;

  constructor(public keyId: string, public payload: string) {
  }
}

export class SaveAppAPNsIosCompleteAction implements Action {
  readonly type = AppsActionTypes.SAVE_APP_APNS_IOS_COMPLETE;

  constructor(public payload: AppSettings) {
  }
}

export class SaveAppAPNsIosFailedAction implements Action {
  readonly type = AppsActionTypes.SAVE_APP_APNS_IOS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateFacebookAction implements Action {
  readonly type = AppsActionTypes.UPDATE_FACEBOOK;
}

export class UpdateFacebookCompleteAction implements Action {
  readonly type = AppsActionTypes.UPDATE_FACEBOOK_COMPLETE;
}

export class UpdateFacebookFailedAction implements Action {
  readonly type = AppsActionTypes.UPDATE_FACEBOOK_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RequestFacebookReviewAction implements Action {
  readonly type = AppsActionTypes.REQUEST_FACEBOOK_REVIEW;
}

export class RequestFacebookReviewCompleteAction implements Action {
  readonly type = AppsActionTypes.REQUEST_FACEBOOK_REVIEW_COMPLETE;
}

export class RequestFacebookReviewFailedAction implements Action {
  readonly type = AppsActionTypes.REQUEST_FACEBOOK_REVIEW_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetAppMetaDataAction {
  readonly type = AppsActionTypes.GET_APP_METADATA;

  constructor(public payload: string /* app_id */) {
  }
}

export class GetAppMetaDataCompleteAction {
  readonly type = AppsActionTypes.GET_APP_METADATA_COMPLETE;

  constructor(public payload: AppMetaData[]) {

  }
}

export class GetAppMetaDataFailedAction {
  readonly type = AppsActionTypes.GET_APP_METADATA_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateAppMetaDataAction {
  readonly type = AppsActionTypes.UPDATE_APP_METADATA;

  constructor(public payload: AppMetaData, public appId: string) {
  }
}

export class UpdateAppMetaDataCompleteAction {
  readonly type = AppsActionTypes.UPDATE_APP_METADATA_COMPLETE;

  constructor(public payload: AppMetaData) {

  }
}

export class UpdateAppMetaDataFailedAction {
  readonly type = AppsActionTypes.UPDATE_APP_METADATA_FAILED;

  constructor(public payload: ApiRequestStatus) {

  }
}

export class GetMetaDataDefaultsAction {
  readonly type = AppsActionTypes.GET_METADATA_DEFAULTS;

  constructor(public payload: number) {

  }
}

export class GetMetaDataDefaultsCompleteAction {
  readonly type = AppsActionTypes.GET_METADATA_DEFAULTS_COMPLETE;

  constructor(public payload: AppMetaData[]) {

  }
}

export class GetMetaDataDefaultsFailedAction {
  readonly type = AppsActionTypes.GET_METADATA_DEFAULTS_FAILED;

  constructor(public payload: ApiRequestStatus) {

  }
}

export class BulkUpdateAppsAction {
  readonly type = AppsActionTypes.BULK_UPDATE_APPS;

  constructor(public payload: BulkUpdatePayload) {

  }
}

export class BulkUpdateAppsCompleteAction {
  readonly type = AppsActionTypes.BULK_UPDATE_APPS_COMPLETE;
}

export class BulkUpdateAppsFailedAction {
  readonly type = AppsActionTypes.BULK_UPDATE_APPS_FAILED;

  constructor(public payload: ApiRequestStatus) {

  }
}

export class ClearBulkUpdateAction {
  readonly type = AppsActionTypes.CLEAR_BULK_UPDATE;
}

export type AppsActions
  = SearchAppsAction
  | SearchAppsInitAction
  | SearchAppsCompleteAction
  | SearchAppsFailedAction
  | ClearAppAction
  | GetAppAction
  | GetAppCompleteAction
  | GetAppFailedAction
  | GetAppsAction
  | GetAppsCompleteAction
  | GetAppsFailedAction
  | GetProductionAppsAction
  | GetProductionAppsCompleteAction
  | GetProductionAppsFailedAction
  | CreateAppAction
  | CreateAppCompleteAction
  | CreateAppFailedAction
  | UpdateAppAction
  | UpdateAppCompleteAction
  | UpdateAppFailedAction
  | PatchAppAction
  | PatchAppCompleteAction
  | PatchAppFailedAction
  | DeleteAppAction
  | DeleteAppCompleteAction
  | DeleteAppFailedAction
  | GetBuildsAction
  | GetBuildsCompleteAction
  | GetBuildsFailedAction
  | CreateBuildAction
  | CreateBuildCompleteAction
  | CreateBuildFailedAction
  | ClearBuildAction
  | InitStoreListingAction
  | GetRogerthatAppAction
  | GetRogerthatAppCompleteAction
  | GetRogerthatAppFailedAction
  | UpdateRogerthatAppAction
  | UpdateRogerthatAppCompleteAction
  | UpdateRogerthatAppFailedAction
  | GetQrCodeTemplatesAction
  | GetQrCodeTemplatesCompleteAction
  | GetQrCodeTemplatesFailedAction
  | AddQrCodeTemplateAction
  | AddQrCodeTemplateCompleteAction
  | AddQrCodeTemplateFailedAction
  | RemoveQrCodeTemplateAction
  | RemoveQrCodeTemplateCompleteAction
  | RemoveQrCodeTemplateFailedAction
  | GetAppAssetsAction
  | GetAppAssetsCompleteAction
  | GetAppAssetsFailedAction
  | ClearAppResourceAction
  | CreateAppAssetAction
  | CreateAppAssetCompleteAction
  | CreateAppAssetFailedAction
  | RemoveAppAssetAction
  | RemoveAppAssetCompleteAction
  | RemoveAppAssetFailedAction
  | GetDefaultBrandingsAction
  | GetDefaultBrandingsCompleteAction
  | GetDefaultBrandingsFailedAction
  | CreateDefaultBrandingAction
  | CreateDefaultBrandingCompleteAction
  | CreateDefaultBrandingFailedAction
  | RemoveDefaultBrandingAction
  | RemoveDefaultBrandingCompleteAction
  | RemoveDefaultBrandingFailedAction
  | GetAppColorsAction
  | GetAppColorsCompleteAction
  | GetAppColorsFailedAction
  | UpdateAppColorsAction
  | UpdateAppColorsCompleteAction
  | UpdateAppColorsFailedAction
  | GetAppSidebarAction
  | GetAppSidebarCompleteAction
  | GetAppSidebarFailedAction
  | UpdateAppSidebarAction
  | UpdateAppSidebarCompleteAction
  | UpdateAppSidebarFailedAction
  | GetAppImagesAction
  | GetAppImagesCompleteAction
  | GetAppImagesFailedAction
  | GetAppImageAction
  | GetAppImageCompleteAction
  | GetAppImageFailedAction
  | UpdateAppImageAction
  | UpdateAppImageCompleteAction
  | UpdateAppImageFailedAction
  | GenerateAppImagesAction
  | GenerateAppImagesCompleteAction
  | GenerateAppImagesFailedAction
  | RemoveAppImageAction
  | RemoveAppImageCompleteAction
  | RemoveAppImageFailedAction
  | SaveAppChangesAction
  | SaveAppChangesCompleteAction
  | SaveAppChangesFailedAction
  | RevertAppChangesAction
  | RevertAppChangesCompleteAction
  | RevertAppChangesFailedAction
  | GetBuildSettingsAction
  | GetBuildSettingsCompleteAction
  | GetBuildSettingsFailedAction
  | UpdateBuildSettingsAction
  | UpdateBuildSettingsCompleteAction
  | UpdateBuildSettingsFailedAction
  | GetAppSettingsAction
  | GetAppSettingsCompleteAction
  | GetAppSettingsFailedAction
  | UpdateAppSettingsAction
  | UpdateAppSettingsCompleteAction
  | UpdateAppSettingsFailedAction
  | SaveAppSettingsFirebaseIosAction
  | SaveAppSettingsFirebaseIosCompleteAction
  | SaveAppSettingsFirebaseIosFailedAction
  | UpdateFirebaseSettingsIosAction
  | UpdateFirebaseSettingsIosCompleteAction
  | UpdateFirebaseSettingsIosFailedAction
  | SaveAppAPNsIosAction
  | SaveAppAPNsIosCompleteAction
  | SaveAppAPNsIosFailedAction
  | UpdateFacebookAction
  | UpdateFacebookCompleteAction
  | UpdateFacebookFailedAction
  | RequestFacebookReviewAction
  | RequestFacebookReviewCompleteAction
  | RequestFacebookReviewFailedAction
  | GetAppMetaDataAction
  | GetAppMetaDataCompleteAction
  | GetAppMetaDataFailedAction
  | UpdateAppMetaDataAction
  | UpdateAppMetaDataCompleteAction
  | UpdateAppMetaDataFailedAction
  | GetMetaDataDefaultsAction
  | GetMetaDataDefaultsCompleteAction
  | GetMetaDataDefaultsFailedAction
  | BulkUpdateAppsAction
  | BulkUpdateAppsCompleteAction
  | BulkUpdateAppsFailedAction
  | ClearBulkUpdateAction;
