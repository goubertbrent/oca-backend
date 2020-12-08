import { apiRequestInitial, ApiRequestStatus } from '../../../framework/client/rpc';
import {
  App,
  AppAsset,
  AppColors,
  AppImageInfo,
  AppMetaData,
  AppSearchParameters,
  AppSettings,
  AppSidebar,
  Build,
  BuildSettings,
  DefaultBranding,
  QrCodeTemplate,
  RogerthatApp,
} from '../interfaces';

export interface IAppsState {
  apps: Partial<App>[];
  appsStatus: ApiRequestStatus;
  appsSearchParameters: AppSearchParameters;
  app: App | null;
  builds: Build[];
  createBuildStatus: ApiRequestStatus;
  updateAppStatus: ApiRequestStatus;
  patchAppStatus: ApiRequestStatus;
  rogerthatApp: RogerthatApp | null;
  rogerthatAppStatus: ApiRequestStatus;
  createAppStatus: ApiRequestStatus;
  qrCodeTemplates: QrCodeTemplate[];
  qrCodeTemplatesStatus: ApiRequestStatus;
  createQrCodeTemplatesStatus: ApiRequestStatus;
  appAssets: AppAsset[];
  appAssetStatus: ApiRequestStatus;
  defaultBrandings: DefaultBranding[];
  defaultBrandingsStatus: ApiRequestStatus;
  defaultBrandingEditStatus: ApiRequestStatus;
  appColors: AppColors | null;
  appColorsStatus: ApiRequestStatus;
  appSidebar: AppSidebar | null;
  appSidebarStatus: ApiRequestStatus;
  images: AppImageInfo[];
  imagesStatus: ApiRequestStatus;
  image: AppImageInfo | null;
  imageStatus: ApiRequestStatus;
  saveChangesStatus: ApiRequestStatus;
  revertChangesStatus: ApiRequestStatus;
  buildSettings: BuildSettings | null;
  getBuildSettingsStatus: ApiRequestStatus;
  updateBuildSettingsStatus: ApiRequestStatus;
  appSettings: AppSettings | null;
  getAppSettingsStatus: ApiRequestStatus;
  updateAppSettingsStatus: ApiRequestStatus;
  saveAppSettingsFirebaseIosStatus: ApiRequestStatus;
  updateFirebaseSettingsIosStatus: ApiRequestStatus;
  saveAppAPNsIosStatus: ApiRequestStatus;
  updateFacebookStatus: ApiRequestStatus;
  requestFacebookReviewStatus: ApiRequestStatus;
  appMetaData: AppMetaData[];
  appMetaDataStatus: ApiRequestStatus;
  updateAppMetaDataStatus: ApiRequestStatus;
  defaultMetaData: AppMetaData[];
  bulkUpdateStatus: ApiRequestStatus;
  generateImagesStatus: ApiRequestStatus;
  productionApps: Partial<App>[];
  productionAppsStatus: ApiRequestStatus;
}

export const initialAppsState: IAppsState = {
  apps: [],
  appsStatus: apiRequestInitial,
  appsSearchParameters: {},
  app: null,
  builds: [],
  createBuildStatus: apiRequestInitial,
  updateAppStatus: apiRequestInitial,
  patchAppStatus: apiRequestInitial,
  rogerthatApp: null,
  rogerthatAppStatus: apiRequestInitial,
  createAppStatus: apiRequestInitial,
  qrCodeTemplates: [],
  qrCodeTemplatesStatus: apiRequestInitial,
  createQrCodeTemplatesStatus: apiRequestInitial,
  appAssets: [],
  appAssetStatus: apiRequestInitial,
  defaultBrandings: [],
  defaultBrandingsStatus: apiRequestInitial,
  defaultBrandingEditStatus: apiRequestInitial,
  appColors: null,
  appColorsStatus: apiRequestInitial,
  appSidebar: null,
  appSidebarStatus: apiRequestInitial,
  images: [],
  imagesStatus: apiRequestInitial,
  image: null,
  imageStatus: apiRequestInitial,
  saveChangesStatus: apiRequestInitial,
  revertChangesStatus: apiRequestInitial,
  buildSettings: null,
  getBuildSettingsStatus: apiRequestInitial,
  updateBuildSettingsStatus: apiRequestInitial,
  appSettings: null,
  getAppSettingsStatus: apiRequestInitial,
  updateAppSettingsStatus: apiRequestInitial,
  saveAppSettingsFirebaseIosStatus: apiRequestInitial,
  updateFirebaseSettingsIosStatus: apiRequestInitial,
  saveAppAPNsIosStatus: apiRequestInitial,
  updateFacebookStatus: apiRequestInitial,
  requestFacebookReviewStatus: apiRequestInitial,
  appMetaData: [],
  appMetaDataStatus: apiRequestInitial,
  updateAppMetaDataStatus: apiRequestInitial,
  defaultMetaData: [],
  bulkUpdateStatus: apiRequestInitial,
  generateImagesStatus: apiRequestInitial,
  productionApps: [],
  productionAppsStatus: apiRequestInitial,
};
