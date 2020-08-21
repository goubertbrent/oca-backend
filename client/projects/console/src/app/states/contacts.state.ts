import { apiRequestInitial, ApiRequestStatus } from '../../../framework/client/rpc';
import { Contact } from '../interfaces';

export interface IContactsState {
  contacts: Contact[];
  contactsStatus: ApiRequestStatus;
  contact: Contact | null;
  getContactStatus: ApiRequestStatus;
  createContactStatus: ApiRequestStatus;
  updateContactStatus: ApiRequestStatus;
  removeContactStatus: ApiRequestStatus;
}

export const initialContactsState: IContactsState = {
  contacts: [],
  contactsStatus: apiRequestInitial,
  contact: null,
  getContactStatus: apiRequestInitial,
  createContactStatus: apiRequestInitial,
  updateContactStatus: apiRequestInitial,
  removeContactStatus: apiRequestInitial,
};
