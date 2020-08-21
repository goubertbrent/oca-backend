import { Action } from '@ngrx/store';
import { ApiRequestStatus } from '../../../framework/client/rpc';
import {
  AppAsset,
  CreateDefaultBrandingPayload,
  DefaultBranding,
  EditAppAssetPayload,
  EmbeddedApp,
  EmbeddedAppTag,
  FirebaseProject,
  PaymentProvider,
  RogerthatApp,
  SaveEmbeddedApp,
} from '../interfaces';

export const enum BackendsActionTypes {
  GET_ROGERTHAT_APPS = '[RCC:backends] Get backend rogerthat apps',
  GET_ROGERTHAT_APPS_COMPLETE = '[RCC:backends] Get backend rogerthat apps complete',
  GET_ROGERTHAT_APPS_FAILED = '[RCC:backends] Get backend rogerthat apps failed',
  SET_DEFAULT_ROGERTHAT_APP = '[RCC:backends] Set default rogerthat app',
  SET_DEFAULT_ROGERTHAT_APP_COMPLETE = '[RCC:backends] Set default rogerthat app complete',
  SET_DEFAULT_ROGERTHAT_APP_FAILED = '[RCC:backends] Set default rogerthat app failed',
  CLEAR_APP_ASSET = '[RCC:backends] Clear app asset',
  GET_APP_ASSETS = '[RCC:backends] Get app assets',
  GET_APP_ASSETS_COMPLETE = '[RCC:backends] Get app assets complete',
  GET_APP_ASSETS_FAILED = '[RCC:backends] Get app assets failed',
  GET_APP_ASSET = '[RCC:backends] Get app asset',
  GET_APP_ASSET_COMPLETE = '[RCC:backends] Get app asset complete',
  GET_APP_ASSET_FAILED = '[RCC:backends] Get app asset failed',
  CREATE_APP_ASSET = '[RCC:backends] Create app asset',
  CREATE_APP_ASSET_COMPLETE = '[RCC:backends] Create app asset complete',
  CREATE_APP_ASSET_FAILED = '[RCC:backends] Create app asset failed',
  UPDATE_APP_ASSET = '[RCC:backends] Update app asset',
  UPDATE_APP_ASSET_COMPLETE = '[RCC:backends] Update app asset complete',
  UPDATE_APP_ASSET_FAILED = '[RCC:backends] Update app asset failed',
  REMOVE_APP_ASSET = '[RCC:backends] Remove app asset',
  REMOVE_APP_ASSET_COMPLETE = '[RCC:backends] Remove app asset complete',
  REMOVE_APP_ASSET_FAILED = '[RCC:backends] Remove app asset failed',
  GET_BRANDINGS = '[RCC:backends] Get brandings',
  GET_BRANDINGS_COMPLETE = '[RCC:backends] Get brandings complete',
  GET_BRANDINGS_FAILED = '[RCC:backends] Get brandings failed',
  CLEAR_BRANDING = '[RCC:backends] Clear branding',
  GET_BRANDING = '[RCC:backends] Get branding',
  GET_BRANDING_COMPLETE = '[RCC:backends] Get branding complete',
  GET_BRANDING_FAILED = '[RCC:backends] Get branding failed',
  CREATE_BRANDING = '[RCC:backends] Create branding',
  CREATE_BRANDING_COMPLETE = '[RCC:backends] Create branding complete',
  CREATE_BRANDING_FAILED = '[RCC:backends] Create branding failed',
  UPDATE_BRANDING = '[RCC:backends] Update branding',
  UPDATE_BRANDING_COMPLETE = '[RCC:backends] Update branding complete',
  UPDATE_BRANDING_FAILED = '[RCC:backends] Update branding failed',
  REMOVE_BRANDING = '[RCC:backends] Remove branding',
  REMOVE_BRANDING_COMPLETE = '[RCC:backends] Remove branding complete',
  REMOVE_BRANDING_FAILED = '[RCC:backends] Remove branding failed',
  GET_PAYMENT_PROVIDERS = '[RCC:backends] Get payment providers',
  GET_PAYMENT_PROVIDERS_COMPLETE = '[RCC:backends] Get payment providers complete',
  GET_PAYMENT_PROVIDERS_FAILED = '[RCC:backends] Get payment providers failed',
  CLEAR_PAYMENT_PROVIDER = '[RCC:backends] Clear payment providers',
  GET_PAYMENT_PROVIDER = '[RCC:backends] Get payment provider',
  GET_PAYMENT_PROVIDER_COMPLETE = '[RCC:backends] Get payment provider complete',
  GET_PAYMENT_PROVIDER_FAILED = '[RCC:backends] Get payment provider failed',
  CREATE_PAYMENT_PROVIDER = '[RCC:backends] Create payment provider',
  CREATE_PAYMENT_PROVIDER_COMPLETE = '[RCC:backends] Create payment provider complete',
  CREATE_PAYMENT_PROVIDER_FAILED = '[RCC:backends] Create payment provider failed',
  UPDATE_PAYMENT_PROVIDER = '[RCC:backends] Update payment provider',
  UPDATE_PAYMENT_PROVIDER_COMPLETE = '[RCC:backends] Update payment provider complete',
  UPDATE_PAYMENT_PROVIDER_FAILED = '[RCC:backends] Update payment provider failed',
  REMOVE_PAYMENT_PROVIDER = '[RCC:backends] Delete payment provider',
  REMOVE_PAYMENT_PROVIDER_COMPLETE = '[RCC:backends] Delete payment provider complete',
  REMOVE_PAYMENT_PROVIDER_FAILED = '[RCC:backends] Delete payment provider failed',
  LIST_EMBEDDED_APPS = '[RCC:backends] List embedded apps',
  LIST_EMBEDDED_APPS_COMPLETE = '[RCC:backends] List embedded apps complete',
  LIST_EMBEDDED_APPS_FAILED = '[RCC:backends] List embedded apps failed',
  GET_EMBEDDED_APP = '[RCC:backends] Get embedded app',
  GET_EMBEDDED_APP_COMPLETE = '[RCC:backends] Get embedded app complete',
  GET_EMBEDDED_APP_FAILED = '[RCC:backends] Get embedded app failed',
  CREATE_EMBEDDED_APP = '[RCC:backends] Create embedded app',
  CREATE_EMBEDDED_APP_COMPLETE = '[RCC:backends] Create embedded app complete',
  CREATE_EMBEDDED_APP_FAILED = '[RCC:backends] Create embedded app failed',
  UPDATE_EMBEDDED_APP = '[RCC:backends] Update embedded app',
  UPDATE_EMBEDDED_APP_COMPLETE = '[RCC:backends] Update embedded app complete',
  UPDATE_EMBEDDED_APP_FAILED = '[RCC:backends] Update embedded app failed',
  REMOVE_EMBEDDED_APP = '[RCC:backends] Remove embedded app',
  REMOVE_EMBEDDED_APP_COMPLETE = '[RCC:backends] Remove embedded app complete',
  REMOVE_EMBEDDED_APP_FAILED = '[RCC:backends] Remove embedded app failed',
  LIST_FIREBASE_PROJECTS = '[RCC:backends] List firebase projects',
  LIST_FIREBASE_PROJECTS_COMPLETE = '[RCC:backends] List firebase projects complete',
  LIST_FIREBASE_PROJECTS_FAILED = '[RCC:backends] List firebase projects failed',
  CREATE_FIREBASE_PROJECT = '[RCC:backends] Create firebase project',
  CREATE_FIREBASE_PROJECT_COMPLETE = '[RCC:backends] Create firebase project complete',
  CREATE_FIREBASE_PROJECT_FAILED = '[RCC:backends] Create firebase project failed',
}

export class GetBackendRogerthatAppsAction implements Action {
  readonly type = BackendsActionTypes.GET_ROGERTHAT_APPS;
}

export class GetBackendRogerthatAppsCompleteAction implements Action {
  readonly type = BackendsActionTypes.GET_ROGERTHAT_APPS_COMPLETE;

  constructor(public payload: RogerthatApp[]) {
  }
}

export class GetBackendRogerthatAppsFailedAction implements Action {
  readonly type = BackendsActionTypes.GET_ROGERTHAT_APPS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class SetDefaultRogerthatAppAction implements Action {
  readonly type = BackendsActionTypes.SET_DEFAULT_ROGERTHAT_APP;

  constructor(public payload: string) {
  }
}

export class SetDefaultRogerthatAppCompleteAction implements Action {
  readonly type = BackendsActionTypes.SET_DEFAULT_ROGERTHAT_APP_COMPLETE;

  constructor(public payload: RogerthatApp) {
  }
}

export class SetDefaultRogerthatAppFailedAction implements Action {
  readonly type = BackendsActionTypes.SET_DEFAULT_ROGERTHAT_APP_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetBackendAppAssetsAction implements Action {
  readonly type = BackendsActionTypes.GET_APP_ASSETS;
}

export class GetBackendAppAssetsCompleteAction implements Action {
  readonly type = BackendsActionTypes.GET_APP_ASSETS_COMPLETE;

  constructor(public payload: AppAsset[]) {
  }
}

export class GetBackendAppAssetsFailedAction implements Action {
  readonly type = BackendsActionTypes.GET_APP_ASSETS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetBackendAppAssetAction implements Action {
  readonly type = BackendsActionTypes.GET_APP_ASSET;

  constructor(public payload: string) {
  }
}

export class ClearBackendAppAssetAction implements Action {
  readonly type = BackendsActionTypes.CLEAR_APP_ASSET;
}

export class GetBackendAppAssetCompleteAction implements Action {
  readonly type = BackendsActionTypes.GET_APP_ASSET_COMPLETE;

  constructor(public payload: AppAsset) {
  }
}

export class GetBackendAppAssetFailedAction implements Action {
  readonly type = BackendsActionTypes.GET_APP_ASSET_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateBackendAppAssetAction implements Action {
  readonly type = BackendsActionTypes.UPDATE_APP_ASSET;

  constructor(public payload: EditAppAssetPayload) {
  }
}

export class UpdateBackendAppAssetCompleteAction implements Action {
  readonly type = BackendsActionTypes.UPDATE_APP_ASSET_COMPLETE;

  constructor(public payload: AppAsset) {
  }
}

export class UpdateBackendAppAssetFailedAction implements Action {
  readonly type = BackendsActionTypes.UPDATE_APP_ASSET_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class CreateBackendAppAssetAction implements Action {
  readonly type = BackendsActionTypes.CREATE_APP_ASSET;

  constructor(public payload: EditAppAssetPayload) {
  }
}

export class CreateBackendAppAssetCompleteAction implements Action {
  readonly type = BackendsActionTypes.CREATE_APP_ASSET_COMPLETE;

  constructor(public payload: AppAsset) {
  }
}

export class CreateBackendAppAssetFailedAction implements Action {
  readonly type = BackendsActionTypes.CREATE_APP_ASSET_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RemoveBackendAppAssetAction implements Action {
  readonly type = BackendsActionTypes.REMOVE_APP_ASSET;

  constructor(public payload: AppAsset) {
  }
}

export class RemoveBackendAppAssetCompleteAction implements Action {
  readonly type = BackendsActionTypes.REMOVE_APP_ASSET_COMPLETE;

  constructor(public payload: AppAsset) {
  }
}

export class RemoveBackendAppAssetFailedAction implements Action {
  readonly type = BackendsActionTypes.REMOVE_APP_ASSET_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetBackendBrandingsAction implements Action {
  readonly type = BackendsActionTypes.GET_BRANDINGS;
}

export class GetBackendBrandingsCompleteAction implements Action {
  readonly type = BackendsActionTypes.GET_BRANDINGS_COMPLETE;

  constructor(public payload: DefaultBranding[]) {
  }
}

export class GetBackendBrandingsFailedAction implements Action {
  readonly type = BackendsActionTypes.GET_BRANDINGS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class ClearBackendBrandingAction implements Action {
  readonly type = BackendsActionTypes.CLEAR_BRANDING;
}

export class GetBackendBrandingAction implements Action {
  readonly type = BackendsActionTypes.GET_BRANDING;

  constructor(public payload: string) {
  }
}

export class GetBackendBrandingCompleteAction implements Action {
  readonly type = BackendsActionTypes.GET_BRANDING_COMPLETE;

  constructor(public payload: DefaultBranding) {
  }
}

export class GetBackendBrandingFailedAction implements Action {
  readonly type = BackendsActionTypes.GET_BRANDING_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class CreateBackendBrandingAction implements Action {
  readonly type = BackendsActionTypes.CREATE_BRANDING;

  constructor(public payload: CreateDefaultBrandingPayload) {
  }
}

export class CreateBackendBrandingCompleteAction implements Action {
  readonly type = BackendsActionTypes.CREATE_BRANDING_COMPLETE;

  constructor(public payload: DefaultBranding) {
  }
}

export class CreateBackendBrandingFailedAction implements Action {
  readonly type = BackendsActionTypes.CREATE_BRANDING_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateBackendBrandingAction implements Action {
  readonly type = BackendsActionTypes.UPDATE_BRANDING;

  constructor(public payload: CreateDefaultBrandingPayload) {
  }
}

export class UpdateBackendBrandingCompleteAction implements Action {
  readonly type = BackendsActionTypes.UPDATE_BRANDING_COMPLETE;

  constructor(public payload: DefaultBranding) {
  }
}

export class UpdateBackendBrandingFailedAction implements Action {
  readonly type = BackendsActionTypes.UPDATE_BRANDING_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RemoveBackendBrandingAction implements Action {
  readonly type = BackendsActionTypes.REMOVE_BRANDING;

  constructor(public payload: DefaultBranding) {
  }
}

export class RemoveBackendBrandingCompleteAction implements Action {
  readonly type = BackendsActionTypes.REMOVE_BRANDING_COMPLETE;

  constructor(public payload: DefaultBranding) {
  }
}

export class RemoveBackendBrandingFailedAction implements Action {
  readonly type = BackendsActionTypes.REMOVE_BRANDING_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetPaymentProvidersAction implements Action {
  readonly type = BackendsActionTypes.GET_PAYMENT_PROVIDERS;
}

export class GetPaymentProvidersCompleteAction implements Action {
  readonly type = BackendsActionTypes.GET_PAYMENT_PROVIDERS_COMPLETE;

  constructor(public payload: PaymentProvider[]) {
  }
}

export class GetPaymentProvidersFailedAction implements Action {
  readonly type = BackendsActionTypes.GET_PAYMENT_PROVIDERS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetPaymentProviderAction implements Action {
  readonly type = BackendsActionTypes.GET_PAYMENT_PROVIDER;

  constructor(public payload: string) {
  }
}

export class GetPaymentProviderCompleteAction implements Action {
  readonly type = BackendsActionTypes.GET_PAYMENT_PROVIDER_COMPLETE;

  constructor(public payload: PaymentProvider) {
  }
}

export class GetPaymentProviderFailedAction implements Action {
  readonly type = BackendsActionTypes.GET_PAYMENT_PROVIDER_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class ClearPaymentProviderAction implements Action {
  readonly type = BackendsActionTypes.CLEAR_PAYMENT_PROVIDER;
}

export class CreatePaymentProviderAction implements Action {
  readonly type = BackendsActionTypes.CREATE_PAYMENT_PROVIDER;

  constructor(public payload: PaymentProvider) {
  }
}

export class CreatePaymentProviderCompleteAction implements Action {
  readonly type = BackendsActionTypes.CREATE_PAYMENT_PROVIDER_COMPLETE;

  constructor(public payload: PaymentProvider) {
  }
}

export class CreatePaymentProviderFailedAction implements Action {
  readonly type = BackendsActionTypes.CREATE_PAYMENT_PROVIDER_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdatePaymentProviderAction implements Action {
  readonly type = BackendsActionTypes.UPDATE_PAYMENT_PROVIDER;

  constructor(public payload: PaymentProvider) {
  }
}

export class UpdatePaymentProviderCompleteAction implements Action {
  readonly type = BackendsActionTypes.UPDATE_PAYMENT_PROVIDER_COMPLETE;

  constructor(public payload: PaymentProvider) {
  }
}

export class UpdatePaymentProviderFailedAction implements Action {
  readonly type = BackendsActionTypes.UPDATE_PAYMENT_PROVIDER_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RemovePaymentProviderAction implements Action {
  readonly type = BackendsActionTypes.REMOVE_PAYMENT_PROVIDER;

  constructor(public payload: PaymentProvider) {
  }
}

export class RemovePaymentProviderCompleteAction implements Action {
  readonly type = BackendsActionTypes.REMOVE_PAYMENT_PROVIDER_COMPLETE;

  constructor(public payload: PaymentProvider) {
  }
}

export class RemovePaymentProviderFailedAction implements Action {
  readonly type = BackendsActionTypes.REMOVE_PAYMENT_PROVIDER_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class ListEmbeddedAppsAction implements Action {
  readonly type = BackendsActionTypes.LIST_EMBEDDED_APPS;

  constructor(public tag?: EmbeddedAppTag) {
  }
}

export class ListEmbeddedAppsCompleteAction implements Action {
  readonly type = BackendsActionTypes.LIST_EMBEDDED_APPS_COMPLETE;

  constructor(public payload: EmbeddedApp[]) {
  }
}

export class ListEmbeddedAppsFailedAction implements Action {
  readonly type = BackendsActionTypes.LIST_EMBEDDED_APPS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class GetEmbeddedAppAction implements Action {
  readonly type = BackendsActionTypes.GET_EMBEDDED_APP;

  constructor(public payload: string) {
  }
}

export class GetEmbeddedAppCompleteAction implements Action {
  readonly type = BackendsActionTypes.GET_EMBEDDED_APP_COMPLETE;

  constructor(public payload: EmbeddedApp) {
  }
}

export class GetEmbeddedAppFailedAction implements Action {
  readonly type = BackendsActionTypes.GET_EMBEDDED_APP_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class CreateEmbeddedAppAction implements Action {
  readonly type = BackendsActionTypes.CREATE_EMBEDDED_APP;

  constructor(public payload: SaveEmbeddedApp) {
  }
}

export class CreateEmbeddedAppCompleteAction implements Action {
  readonly type = BackendsActionTypes.CREATE_EMBEDDED_APP_COMPLETE;

  constructor(public payload: EmbeddedApp) {
  }
}

export class CreateEmbeddedAppFailedAction implements Action {
  readonly type = BackendsActionTypes.CREATE_EMBEDDED_APP_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateEmbeddedAppAction implements Action {
  readonly type = BackendsActionTypes.UPDATE_EMBEDDED_APP;

  constructor(public payload: SaveEmbeddedApp) {
  }
}

export class UpdateEmbeddedAppCompleteAction implements Action {
  readonly type = BackendsActionTypes.UPDATE_EMBEDDED_APP_COMPLETE;

  constructor(public payload: EmbeddedApp) {
  }
}

export class UpdateEmbeddedAppFailedAction implements Action {
  readonly type = BackendsActionTypes.UPDATE_EMBEDDED_APP_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RemoveEmbeddedAppAction implements Action {
  readonly type = BackendsActionTypes.REMOVE_EMBEDDED_APP;

  constructor(public payload: string) {
  }
}

export class RemoveEmbeddedAppCompleteAction implements Action {
  readonly type = BackendsActionTypes.REMOVE_EMBEDDED_APP_COMPLETE;

  constructor(public payload: string) {
  }
}

export class RemoveEmbeddedAppFailedAction implements Action {
  readonly type = BackendsActionTypes.REMOVE_EMBEDDED_APP_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class ListFirebaseProjectsAction implements Action {
  readonly type = BackendsActionTypes.LIST_FIREBASE_PROJECTS;

  constructor() {
  }
}

export class ListFirebaseProjectsCompleteAction implements Action {
  readonly type = BackendsActionTypes.LIST_FIREBASE_PROJECTS_COMPLETE;

  constructor(public payload: FirebaseProject[]) {
  }
}

export class ListFirebaseProjectsFailedAction implements Action {
  readonly type = BackendsActionTypes.LIST_FIREBASE_PROJECTS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class CreateFirebaseProjectAction implements Action {
  readonly type = BackendsActionTypes.CREATE_FIREBASE_PROJECT;

  constructor(public payload: string) {
  }
}

export class CreateFirebaseProjectCompleteAction implements Action {
  readonly type = BackendsActionTypes.CREATE_FIREBASE_PROJECT_COMPLETE;

  constructor(public payload: FirebaseProject) {
  }
}

export class CreateFirebaseProjectFailedAction implements Action {
  readonly type = BackendsActionTypes.CREATE_FIREBASE_PROJECT_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export type BackendsActions = GetBackendRogerthatAppsAction
  | GetBackendRogerthatAppsCompleteAction
  | GetBackendRogerthatAppsFailedAction
  | SetDefaultRogerthatAppAction
  | SetDefaultRogerthatAppCompleteAction
  | SetDefaultRogerthatAppFailedAction
  | ClearBackendAppAssetAction
  | GetBackendAppAssetsAction
  | GetBackendAppAssetsCompleteAction
  | GetBackendAppAssetsFailedAction
  | GetBackendAppAssetAction
  | GetBackendAppAssetCompleteAction
  | GetBackendAppAssetFailedAction
  | CreateBackendAppAssetAction
  | CreateBackendAppAssetCompleteAction
  | CreateBackendAppAssetFailedAction
  | UpdateBackendAppAssetAction
  | UpdateBackendAppAssetCompleteAction
  | UpdateBackendAppAssetFailedAction
  | RemoveBackendAppAssetAction
  | RemoveBackendAppAssetCompleteAction
  | RemoveBackendAppAssetFailedAction
  | ClearBackendBrandingAction
  | GetBackendBrandingsAction
  | GetBackendBrandingsCompleteAction
  | GetBackendBrandingsFailedAction
  | GetBackendBrandingAction
  | GetBackendBrandingCompleteAction
  | GetBackendBrandingFailedAction
  | CreateBackendBrandingAction
  | CreateBackendBrandingCompleteAction
  | CreateBackendBrandingFailedAction
  | UpdateBackendBrandingAction
  | UpdateBackendBrandingCompleteAction
  | UpdateBackendBrandingFailedAction
  | RemoveBackendBrandingAction
  | RemoveBackendBrandingCompleteAction
  | RemoveBackendBrandingFailedAction
  | GetPaymentProvidersAction
  | GetPaymentProvidersCompleteAction
  | GetPaymentProvidersFailedAction
  | ClearPaymentProviderAction
  | GetPaymentProviderAction
  | GetPaymentProviderCompleteAction
  | GetPaymentProviderFailedAction
  | CreatePaymentProviderAction
  | CreatePaymentProviderCompleteAction
  | CreatePaymentProviderFailedAction
  | UpdatePaymentProviderAction
  | UpdatePaymentProviderCompleteAction
  | UpdatePaymentProviderFailedAction
  | RemovePaymentProviderAction
  | RemovePaymentProviderCompleteAction
  | RemovePaymentProviderFailedAction
  | ListEmbeddedAppsAction
  | ListEmbeddedAppsCompleteAction
  | ListEmbeddedAppsFailedAction
  | GetEmbeddedAppAction
  | GetEmbeddedAppCompleteAction
  | GetEmbeddedAppFailedAction
  | CreateEmbeddedAppAction
  | CreateEmbeddedAppCompleteAction
  | CreateEmbeddedAppFailedAction
  | UpdateEmbeddedAppAction
  | UpdateEmbeddedAppCompleteAction
  | UpdateEmbeddedAppFailedAction
  | RemoveEmbeddedAppAction
  | RemoveEmbeddedAppCompleteAction
  | RemoveEmbeddedAppFailedAction
  | ListFirebaseProjectsAction
  | ListFirebaseProjectsCompleteAction
  | ListFirebaseProjectsFailedAction
  | CreateFirebaseProjectAction
  | CreateFirebaseProjectCompleteAction
  | CreateFirebaseProjectFailedAction;
