import { ISidebarState, sidebarReducer } from '../../../framework/client/nav/sidebar';
import { IToolbarState, toolbarReducer } from '../../../framework/client/nav/toolbar';
import { IAppsState, IBackendsState, IDeveloperAccountsState, IReviewNotesState } from '../states';
import { IContactsState } from '../states/contacts.state';
import { appsReducer } from './apps.reducer';
import { backendsReducer } from './backends.reducer';
import { contactsReducer } from './contacts.reducer';
import { developerAccountsReducer } from './developer-accounts.reducer';
import { reviewNotesReducer } from './review-notes.reducer';

export interface ConsoleState {
  apps: IAppsState;
  backends: IBackendsState;
  developerAccounts: IDeveloperAccountsState;
  reviewNotes: IReviewNotesState;
  contacts: IContactsState;
  sidebar: ISidebarState;
  toolbar: IToolbarState;
}

export const consoleReducers = {
  apps: appsReducer,
  backends: backendsReducer,
  developerAccounts: developerAccountsReducer,
  reviewNotes: reviewNotesReducer,
  contacts: contactsReducer,
  sidebar: sidebarReducer,
  toolbar: toolbarReducer,
};
