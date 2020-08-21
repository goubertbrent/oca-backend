import { insertItem, removeItem, updateItem } from '../ngrx';
import { apiRequestLoading, apiRequestSuccess } from '../../../framework/client/rpc';
import { ContactsActions, ContactsActionTypes } from '../actions';
import { IContactsState, initialContactsState } from '../states/contacts.state';

export function contactsReducer(state: IContactsState = initialContactsState,
                                action: ContactsActions): IContactsState {
  switch (action.type) {
    case ContactsActionTypes.GET_CONTACTS:
      return {
        ...state,
        contactsStatus: apiRequestLoading,
      };
    case ContactsActionTypes.GET_CONTACTS_COMPLETE:
      return {
        ...state,
        contacts: action.payload,
        contactsStatus: apiRequestSuccess,
      };

    case ContactsActionTypes.GET_CONTACT:
      return {
        ...state,
        getContactStatus: apiRequestLoading,
      };
    case ContactsActionTypes.GET_CONTACT_COMPLETE:
      return {
        ...state,
        contact: action.payload,
        getContactStatus: apiRequestSuccess,
      };
    case ContactsActionTypes.GET_CONTACT_FAILED:
      return {
        ...state,
        getContactStatus: action.payload,
      };
    case ContactsActionTypes.CREATE_CONTACT:
      return {
        ...state,
        createContactStatus: apiRequestLoading,
      };
    case ContactsActionTypes.CREATE_CONTACT_COMPLETE:
      return {
        ...state,
        contact: action.payload,
        createContactStatus: apiRequestSuccess,
        contacts: insertItem(state.contacts, action.payload),
      };
    case ContactsActionTypes.CREATE_CONTACT_FAILED:
      return {
        ...state,
        createContactStatus: action.payload,
      };
    case ContactsActionTypes.UPDATE_CONTACT:
      return {
        ...state,
        updateContactStatus: apiRequestLoading,
      };
    case ContactsActionTypes.UPDATE_CONTACT_COMPLETE:
      return {
        ...state,
        contact: action.payload,
        updateContactStatus: apiRequestSuccess,
        contacts: updateItem(state.contacts, action.payload, 'id'),
      };
    case ContactsActionTypes.UPDATE_CONTACT_FAILED:
      return {
        ...state,
        updateContactStatus: action.payload,
      };
    case ContactsActionTypes.REMOVE_CONTACT:
      return {
        ...state,
        removeContactStatus: apiRequestLoading,
      };
    case ContactsActionTypes.REMOVE_CONTACT_COMPLETE:
      return {
        ...state,
        contact: null,
        removeContactStatus: apiRequestSuccess,
        contacts: removeItem(state.contacts, action.payload, 'id'),
      };
    case ContactsActionTypes.REMOVE_CONTACT_FAILED:
      return {
        ...state,
        removeContactStatus: action.payload,
      };
    case ContactsActionTypes.CLEAR_CONTACT:
      return {
        ...state,
        contact: initialContactsState.contact,
        createContactStatus: initialContactsState.createContactStatus,
        updateContactStatus: initialContactsState.updateContactStatus,
        removeContactStatus: initialContactsState.removeContactStatus,
      };
    default:
      return state;
  }
}
