import { apiRequestInitial, ApiRequestStatus } from '../../../framework/client/rpc';
import { AppAsset, DefaultBranding, PaymentProvider, RogerthatApp } from '../interfaces';
import { EmbeddedApp } from '../interfaces/embedded-apps';
import { FirebaseProject } from '../interfaces/firebase-projects';

export interface IBackendsState {
  apps: RogerthatApp[];
  appAssets: AppAsset[];
  appAssetsStatus: ApiRequestStatus;
  appAsset: AppAsset | null;
  appAssetStatus: ApiRequestStatus;
  appAssetEditStatus: ApiRequestStatus;
  brandings: DefaultBranding[];
  brandingsStatus: ApiRequestStatus;
  branding: DefaultBranding | null;
  brandingEditStatus: ApiRequestStatus;
  paymentProviders: PaymentProvider[];
  paymentProvidersStatus: ApiRequestStatus;
  paymentProvider: PaymentProvider | null;
  paymentProviderEditStatus: ApiRequestStatus;
  embeddedApp: EmbeddedApp | null;
  getEmbeddedAppStatus: ApiRequestStatus;
  createEmbeddedAppStatus: ApiRequestStatus;
  updateEmbeddedAppStatus: ApiRequestStatus;
  deleteEmbeddedAppStatus: ApiRequestStatus;
  embeddedApps: EmbeddedApp[];
  listEmbeddedAppsStatus: ApiRequestStatus;
  firebaseProjects: FirebaseProject[];
  listFirebaseProjectsStatus: ApiRequestStatus;
  createFirebaseProjectStatus: ApiRequestStatus;
}

export const initialBackendsState: IBackendsState = {
  apps: [],
  appAssets: [],
  appAssetsStatus: apiRequestInitial,
  appAsset: null,
  appAssetStatus: apiRequestInitial,
  appAssetEditStatus: apiRequestInitial,
  brandings: [],
  brandingsStatus: apiRequestInitial,
  branding: null,
  brandingEditStatus: apiRequestInitial,
  paymentProviders: [],
  paymentProvidersStatus: apiRequestInitial,
  paymentProvider: null,
  paymentProviderEditStatus: apiRequestInitial,
  embeddedApp: null,
  getEmbeddedAppStatus: apiRequestInitial,
  createEmbeddedAppStatus: apiRequestInitial,
  updateEmbeddedAppStatus: apiRequestInitial,
  deleteEmbeddedAppStatus: apiRequestInitial,
  embeddedApps: [],
  listEmbeddedAppsStatus: apiRequestInitial,
  firebaseProjects: [],
  listFirebaseProjectsStatus: apiRequestInitial,
  createFirebaseProjectStatus: apiRequestInitial,
};
