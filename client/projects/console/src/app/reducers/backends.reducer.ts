import { insertItem, removeItem, updateItem } from '../ngrx';
import { apiRequestLoading, apiRequestSuccess } from '../../../framework/client/rpc';
import { BackendsActions, BackendsActionTypes } from '../actions';
import { IBackendsState, initialBackendsState } from '../states';

export function backendsReducer(state: IBackendsState = initialBackendsState, action: BackendsActions): IBackendsState {
  switch (action.type) {
    case BackendsActionTypes.GET_ROGERTHAT_APPS_COMPLETE:
      return {
        ...state,
        apps: action.payload,
      };
    case BackendsActionTypes.SET_DEFAULT_ROGERTHAT_APP_COMPLETE:
      return {
        ...state,
        apps: [ ...state.apps
          .map(a => ({ ...a, is_default: false }))
          .filter(a => a.id !== action.payload.id),
          action.payload ],
      };
    case BackendsActionTypes.CLEAR_APP_ASSET:
      return {
        ...state,
        appAsset: initialBackendsState.appAsset,
        appAssetEditStatus: initialBackendsState.appAssetEditStatus,
      };
    case BackendsActionTypes.GET_APP_ASSETS:
      return {
        ...state,
        appAssets: [],
        appAssetsStatus: apiRequestLoading,
        appAssetEditStatus: initialBackendsState.appAssetEditStatus,
      };
    case BackendsActionTypes.GET_APP_ASSETS_COMPLETE:
      return {
        ...state,
        appAssets: action.payload,
        appAssetsStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.GET_APP_ASSETS_FAILED:
      return {
        ...state,
        appAssetsStatus: action.payload,
      };
    case BackendsActionTypes.GET_APP_ASSET:
      return {
        ...state,
        appAsset: initialBackendsState.appAsset,
        appAssetStatus: apiRequestLoading,
      };
    case BackendsActionTypes.GET_APP_ASSET_COMPLETE:
      return {
        ...state,
        appAsset: action.payload,
        appAssetStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.GET_APP_ASSET_FAILED:
      return {
        ...state,
        appAssetStatus: action.payload,
      };
    case BackendsActionTypes.CREATE_APP_ASSET:
    case BackendsActionTypes.UPDATE_APP_ASSET:
      return {
        ...state,
        appAssetEditStatus: apiRequestLoading,
      };
    case BackendsActionTypes.CREATE_APP_ASSET_COMPLETE:
      return {
        ...state,
        appAssets: insertItem(state.appAssets, action.payload),
        appAssetEditStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.CREATE_APP_ASSET_FAILED:
    case BackendsActionTypes.UPDATE_APP_ASSET_FAILED:
      return {
        ...state,
        appAssetEditStatus: action.payload,
      };
    case BackendsActionTypes.UPDATE_APP_ASSET_COMPLETE:
      return {
        ...state,
        appAsset: action.payload,
        appAssets: updateItem(state.appAssets, action.payload, 'id'),
        appAssetEditStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.REMOVE_APP_ASSET_COMPLETE:
      return {
        ...state,
        appAsset: initialBackendsState.appAsset,
        appAssets: removeItem(state.appAssets, action.payload, 'id'),
      };
    case BackendsActionTypes.GET_BRANDINGS:
      return {
        ...state,
        brandings: [],
        brandingsStatus: apiRequestLoading,
      };
    case BackendsActionTypes.GET_BRANDINGS_COMPLETE:
      return {
        ...state,
        brandings: action.payload,
        brandingsStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.GET_BRANDINGS_FAILED:
      return {
        ...state,
        brandingsStatus: action.payload,
      };
    case BackendsActionTypes.GET_BRANDING:
      return {
        ...state,
        branding: initialBackendsState.branding,
        brandingEditStatus: initialBackendsState.brandingEditStatus,
      };
    case BackendsActionTypes.CLEAR_BRANDING:
      return {
        ...state,
        branding: initialBackendsState.branding,
        brandingEditStatus: initialBackendsState.brandingEditStatus,
      };
    case BackendsActionTypes.GET_BRANDING_COMPLETE:
      return {
        ...state,
        branding: action.payload,
      };
    case BackendsActionTypes.CREATE_BRANDING:
    case BackendsActionTypes.UPDATE_BRANDING:
      return {
        ...state,
        brandingEditStatus: apiRequestLoading,
      };
    case BackendsActionTypes.CREATE_BRANDING_COMPLETE:
    case BackendsActionTypes.UPDATE_BRANDING_COMPLETE:
      return {
        ...state,
        branding: action.payload,
        brandings: updateItem(state.brandings, action.payload, 'id'),
        brandingEditStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.CREATE_BRANDING_FAILED:
    case BackendsActionTypes.UPDATE_BRANDING_FAILED:
      return {
        ...state,
        brandingEditStatus: action.payload,
      };
    case BackendsActionTypes.REMOVE_BRANDING_COMPLETE:
      return {
        ...state,
        branding: initialBackendsState.branding,
        brandings: removeItem(state.brandings, action.payload, 'id'),
      };
    case BackendsActionTypes.GET_PAYMENT_PROVIDERS:
      return {
        ...state,
        paymentProviders: [],
        paymentProvidersStatus: apiRequestLoading,
      };
    case BackendsActionTypes.GET_PAYMENT_PROVIDERS_COMPLETE:
      return {
        ...state,
        paymentProviders: action.payload,
        paymentProvidersStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.GET_PAYMENT_PROVIDERS_FAILED:
      return {
        ...state,
        paymentProvidersStatus: action.payload,
      };
    case BackendsActionTypes.GET_PAYMENT_PROVIDER:
      return {
        ...state,
        paymentProvider: initialBackendsState.paymentProvider,
        paymentProviderEditStatus: initialBackendsState.paymentProviderEditStatus,
      };
    case BackendsActionTypes.CLEAR_PAYMENT_PROVIDER:
      return {
        ...state,
        paymentProvider: initialBackendsState.paymentProvider,
        paymentProviderEditStatus: initialBackendsState.paymentProviderEditStatus,
      };
    case BackendsActionTypes.GET_PAYMENT_PROVIDER_COMPLETE:
      return {
        ...state,
        paymentProvider: action.payload,
      };
    case BackendsActionTypes.CREATE_PAYMENT_PROVIDER:
    case BackendsActionTypes.UPDATE_PAYMENT_PROVIDER:
      return {
        ...state,
        paymentProviderEditStatus: apiRequestLoading,
      };
    case BackendsActionTypes.CREATE_PAYMENT_PROVIDER_COMPLETE:
    case BackendsActionTypes.UPDATE_PAYMENT_PROVIDER_COMPLETE:
      return {
        ...state,
        paymentProvider: action.payload,
        paymentProviders: updateItem(state.paymentProviders, action.payload, 'id'),
        paymentProviderEditStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.CREATE_PAYMENT_PROVIDER_FAILED:
    case BackendsActionTypes.UPDATE_PAYMENT_PROVIDER_FAILED:
      return {
        ...state,
        paymentProviderEditStatus: action.payload,
      };
    case BackendsActionTypes.REMOVE_PAYMENT_PROVIDER_COMPLETE:
      return {
        ...state,
        paymentProvider: initialBackendsState.paymentProvider,
        paymentProviders: removeItem(state.paymentProviders, action.payload, 'id'),
      };
    case BackendsActionTypes.LIST_EMBEDDED_APPS:
      return { ...state, listEmbeddedAppsStatus: apiRequestLoading };
    case BackendsActionTypes.LIST_EMBEDDED_APPS_COMPLETE:
      return {
        ...state,
        embeddedApps: action.payload,
        listEmbeddedAppsStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.LIST_EMBEDDED_APPS_FAILED:
      return { ...state, listEmbeddedAppsStatus: action.payload };
    case BackendsActionTypes.GET_EMBEDDED_APP:
      return {
        ...state,
        embeddedApp: initialBackendsState.embeddedApp,
        getEmbeddedAppStatus: apiRequestLoading,
      };
    case BackendsActionTypes.GET_EMBEDDED_APP_COMPLETE:
      return {
        ...state,
        embeddedApp: action.payload,
        getEmbeddedAppStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.GET_EMBEDDED_APP_FAILED:
      return { ...state, getEmbeddedAppStatus: action.payload };
    case BackendsActionTypes.CREATE_EMBEDDED_APP:
      return {
        ...state,
        embeddedApp: initialBackendsState.embeddedApp,
        createEmbeddedAppStatus: apiRequestLoading,
      };
    case BackendsActionTypes.CREATE_EMBEDDED_APP_COMPLETE:
      return {
        ...state,
        embeddedApp: action.payload,
        embeddedApps: insertItem(state.embeddedApps, action.payload),
        createEmbeddedAppStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.CREATE_EMBEDDED_APP_FAILED:
      return { ...state, createEmbeddedAppStatus: action.payload };
    case BackendsActionTypes.UPDATE_EMBEDDED_APP:
      return {
        ...state,
        updateEmbeddedAppStatus: apiRequestLoading,
      };
    case BackendsActionTypes.UPDATE_EMBEDDED_APP_COMPLETE:
      return {
        ...state,
        embeddedApp: action.payload,
        embeddedApps: updateItem(state.embeddedApps, action.payload, 'name'),
        updateEmbeddedAppStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.UPDATE_EMBEDDED_APP_FAILED:
      return { ...state, updateEmbeddedAppStatus: action.payload };
    case BackendsActionTypes.REMOVE_EMBEDDED_APP:
      return { ...state, deleteEmbeddedAppStatus: apiRequestLoading };
    case BackendsActionTypes.REMOVE_EMBEDDED_APP_COMPLETE:
      return {
        ...state,
        embeddedApp: initialBackendsState.embeddedApp,
        embeddedApps: removeItem(state.embeddedApps, action.payload, 'name'),
        deleteEmbeddedAppStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.REMOVE_EMBEDDED_APP_FAILED:
      return { ...state, deleteEmbeddedAppStatus: action.payload };
    case BackendsActionTypes.LIST_FIREBASE_PROJECTS:
      return { ...state, listFirebaseProjectsStatus: apiRequestLoading };
    case BackendsActionTypes.LIST_FIREBASE_PROJECTS_COMPLETE:
      return {
        ...state,
        firebaseProjects: action.payload,
        listFirebaseProjectsStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.LIST_FIREBASE_PROJECTS_FAILED:
      return { ...state, listFirebaseProjectsStatus: action.payload };
    case BackendsActionTypes.CREATE_FIREBASE_PROJECT:
      return { ...state, listFirebaseProjectsStatus: apiRequestLoading };
    case BackendsActionTypes.CREATE_FIREBASE_PROJECT_COMPLETE:
      return {
        ...state,
        firebaseProjects: insertItem(state.firebaseProjects, action.payload),
        createFirebaseProjectStatus: apiRequestSuccess,
      };
    case BackendsActionTypes.CREATE_FIREBASE_PROJECT_FAILED:
      return { ...state, createFirebaseProjectStatus: action.payload };
    default:
      return state;
  }
}
