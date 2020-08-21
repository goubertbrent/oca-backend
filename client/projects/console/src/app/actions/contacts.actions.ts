import { Action } from '@ngrx/store';
import { ApiRequestStatus } from '../../../framework/client/rpc';
import { Contact } from '../interfaces';

export const enum ContactsActionTypes {
  GET_CONTACTS = '[RCC:dev accounts] Get contacts',
  GET_CONTACTS_COMPLETE = '[RCC:dev accounts] Get contacts complete',
  GET_CONTACTS_FAILED = '[RCC:dev accounts] Get contacts failed',
  CLEAR_CONTACT = '[RCC:dev accounts] Clear contact',
  GET_CONTACT = '[RCC:dev accounts] Get contact',
  GET_CONTACT_COMPLETE = '[RCC:dev accounts] Get contact complete',
  GET_CONTACT_FAILED = '[RCC:dev accounts] Get contact failed',
  CREATE_CONTACT = '[RCC:dev accounts] Create contact',
  CREATE_CONTACT_COMPLETE = '[RCC:dev accounts] Create contact complete',
  CREATE_CONTACT_FAILED = '[RCC:dev accounts] Create contact failed',
  UPDATE_CONTACT = '[RCC:dev accounts] Update contact',
  UPDATE_CONTACT_COMPLETE = '[RCC:dev accounts] Update contact complete',
  UPDATE_CONTACT_FAILED = '[RCC:dev accounts] Update contact failed',
  REMOVE_CONTACT = '[RCC:dev accounts] Remove contact',
  REMOVE_CONTACT_COMPLETE = '[RCC:dev accounts] Remove contact complete',
  REMOVE_CONTACT_FAILED = '[RCC:dev accounts] Remove contact failed',
}

export class GetContactsAction implements Action {
  readonly type = ContactsActionTypes.GET_CONTACTS;
}

export class GetContactsCompleteAction implements Action {
  readonly type = ContactsActionTypes.GET_CONTACTS_COMPLETE;

  constructor(public payload: Array<Contact>) {
  }
}

export class GetContactsFailedAction implements Action {
  readonly type = ContactsActionTypes.GET_CONTACTS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class ClearContactAction implements Action {
  readonly type = ContactsActionTypes.CLEAR_CONTACT;
}

export class GetContactAction implements Action {
  readonly type = ContactsActionTypes.GET_CONTACT;

  constructor(public payload: number) {
  }
}

export class GetContactCompleteAction implements Action {
  readonly type = ContactsActionTypes.GET_CONTACT_COMPLETE;

  constructor(public payload: Contact) {
  }
}

export class GetContactFailedAction implements Action {
  readonly type = ContactsActionTypes.GET_CONTACT_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class CreateContactAction implements Action {
  readonly type = ContactsActionTypes.CREATE_CONTACT;

  constructor(public payload: Contact) {
  }
}

export class CreateContactCompleteAction implements Action {
  readonly type = ContactsActionTypes.CREATE_CONTACT_COMPLETE;

  constructor(public payload: Contact) {
  }
}

export class CreateContactFailedAction implements Action {
  readonly type = ContactsActionTypes.CREATE_CONTACT_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateContactAction implements Action {
  readonly type = ContactsActionTypes.UPDATE_CONTACT;

  constructor(public payload: Contact) {
  }
}

export class UpdateContactCompleteAction implements Action {
  readonly type = ContactsActionTypes.UPDATE_CONTACT_COMPLETE;

  constructor(public payload: Contact) {
  }
}

export class UpdateContactFailedAction implements Action {
  readonly type = ContactsActionTypes.UPDATE_CONTACT_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RemoveContactAction implements Action {
  readonly type = ContactsActionTypes.REMOVE_CONTACT;

  constructor(public payload: Contact) {
  }
}

export class RemoveContactCompleteAction implements Action {
  readonly type = ContactsActionTypes.REMOVE_CONTACT_COMPLETE;

  constructor(public payload: Contact) {
  }
}

export class RemoveContactFailedAction implements Action {
  readonly type = ContactsActionTypes.REMOVE_CONTACT_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export type ContactsActions
  = GetContactsAction
  | GetContactsCompleteAction
  | GetContactsFailedAction
  | GetContactAction
  | GetContactCompleteAction
  | GetContactFailedAction
  | ClearContactAction
  | CreateContactAction
  | CreateContactCompleteAction
  | CreateContactFailedAction
  | UpdateContactAction
  | UpdateContactCompleteAction
  | UpdateContactFailedAction
  | RemoveContactAction
  | RemoveContactCompleteAction
  | RemoveContactFailedAction;
