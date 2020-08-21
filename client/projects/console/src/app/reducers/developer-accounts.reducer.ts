import { insertItem, removeItem, updateItem } from '../ngrx';
import { apiRequestLoading, apiRequestSuccess } from '../../../framework/client/rpc';
import { DeveloperAccountsActions, DeveloperAccountsActionTypes } from '../actions';
import { IDeveloperAccountsState, initialDeveloperAccountsState } from '../states';

export function developerAccountsReducer(state: IDeveloperAccountsState = initialDeveloperAccountsState,
                                         action: DeveloperAccountsActions): IDeveloperAccountsState {
  switch (action.type) {
    case DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNTS:
      return {
        ...state,
        developerAccountsStatus: apiRequestLoading,
      };
    case DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNTS_COMPLETE:
      return {
        ...state,
        developerAccounts: action.payload,
        developerAccountsStatus: apiRequestSuccess,
      };

    case DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNT:
      return {
        ...state,
        developerAccountStatus: apiRequestLoading,
      };
    case DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNT_COMPLETE:
      return {
        ...state,
        developerAccount: action.payload,
        developerAccountStatus: apiRequestSuccess,
      };
    case DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNT_FAILED:
      return {
        ...state,
        developerAccountStatus: action.payload,
      };
    case DeveloperAccountsActionTypes.CREATE_DEVELOPER_ACCOUNT:
      return {
        ...state,
        createDeveloperAccountStatus: apiRequestLoading,
      };
    case DeveloperAccountsActionTypes.CREATE_DEVELOPER_ACCOUNT_COMPLETE:
      return {
        ...state,
        developerAccount: action.payload,
        createDeveloperAccountStatus: apiRequestSuccess,
        developerAccounts: insertItem(state.developerAccounts, action.payload),
      };
    case DeveloperAccountsActionTypes.CREATE_DEVELOPER_ACCOUNT_FAILED:
      return {
        ...state,
        createDeveloperAccountStatus: action.payload,
      };
    case DeveloperAccountsActionTypes.UPDATE_DEVELOPER_ACCOUNT:
      return {
        ...state,
        updateDeveloperAccountStatus: apiRequestLoading,
      };
    case DeveloperAccountsActionTypes.UPDATE_DEVELOPER_ACCOUNT_COMPLETE:
      return {
        ...state,
        developerAccount: action.payload,
        updateDeveloperAccountStatus: apiRequestSuccess,
        developerAccounts: updateItem(state.developerAccounts, action.payload, 'id'),
      };
    case DeveloperAccountsActionTypes.UPDATE_DEVELOPER_ACCOUNT_FAILED:
      return {
        ...state,
        updateDeveloperAccountStatus: action.payload,
      };
    case DeveloperAccountsActionTypes.REMOVE_DEVELOPER_ACCOUNT:
      return { ...state, removeDeveloperAccountStatus: apiRequestLoading };
    case DeveloperAccountsActionTypes.REMOVE_DEVELOPER_ACCOUNT_COMPLETE:
      return {
        ...state,
        developerAccount: null,
        removeDeveloperAccountStatus: apiRequestSuccess,
        developerAccounts: removeItem(state.developerAccounts, action.payload, 'id'),
      };
    case DeveloperAccountsActionTypes.REMOVE_DEVELOPER_ACCOUNT_FAILED:
      return { ...state, removeDeveloperAccountStatus: action.payload };
    case DeveloperAccountsActionTypes.CLEAR_DEVELOPER_ACCOUNT:
      return {
        ...state,
        developerAccount: initialDeveloperAccountsState.developerAccount,
        createDeveloperAccountStatus: initialDeveloperAccountsState.createDeveloperAccountStatus,
        updateDeveloperAccountStatus: initialDeveloperAccountsState.updateDeveloperAccountStatus,
        removeDeveloperAccountStatus: initialDeveloperAccountsState.removeDeveloperAccountStatus,
      };
    default:
      return state;
  }
}
