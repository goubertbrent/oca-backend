import { apiRequestInitial, ApiRequestStatus } from '../../../framework/client/rpc';
import { DeveloperAccount } from '../interfaces';

export interface IDeveloperAccountsState {
  developerAccounts: DeveloperAccount[];
  developerAccountsStatus: ApiRequestStatus;
  developerAccount: DeveloperAccount | null;
  developerAccountStatus: ApiRequestStatus;
  createDeveloperAccountStatus: ApiRequestStatus;
  updateDeveloperAccountStatus: ApiRequestStatus;
  removeDeveloperAccountStatus: ApiRequestStatus;
}

export const initialDeveloperAccountsState: IDeveloperAccountsState = {
  developerAccounts: [],
  developerAccountsStatus: apiRequestInitial,
  developerAccount: null,
  developerAccountStatus: apiRequestInitial,
  createDeveloperAccountStatus: apiRequestInitial,
  updateDeveloperAccountStatus: apiRequestInitial,
  removeDeveloperAccountStatus: apiRequestInitial,
};
