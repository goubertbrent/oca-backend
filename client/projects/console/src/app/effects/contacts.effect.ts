import { Injectable } from '@angular/core';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { catchError, map, switchMap } from 'rxjs/operators';
import { handleApiError } from '../../../framework/client/rpc';
import * as actions from '../actions/contacts.actions';
import { ContactsService } from '../services';
import { IContactsState } from '../states';

@Injectable()
export class ContactsEffects {
  @Effect() getContacts$ = this.actions$.pipe(
      ofType<actions.GetContactsAction>(actions.ContactsActionTypes.GET_CONTACTS),
      switchMap(() => this.contactsService.getContacts().pipe(
        map(payload => new actions.GetContactsCompleteAction(payload)),
        catchError(error => handleApiError(actions.GetContactsFailedAction, error)),
      )));

  @Effect() addContact$ = this.actions$.pipe(
      ofType<actions.CreateContactAction>(actions.ContactsActionTypes.CREATE_CONTACT),
      switchMap(action => this.contactsService.createContact(action.payload).pipe(
        map(payload => new actions.CreateContactCompleteAction(payload)),
        catchError(error => handleApiError(actions.CreateContactFailedAction, error)),
      )));

  @Effect() getContact$ = this.actions$.pipe(
      ofType<actions.GetContactAction>(actions.ContactsActionTypes.GET_CONTACT),
      switchMap(action => this.contactsService.getContact(action.payload).pipe(
        map(payload => new actions.GetContactCompleteAction(payload)),
        catchError(error => handleApiError(actions.GetContactFailedAction, error)),
      )));

  @Effect() updateContact$ = this.actions$.pipe(
      ofType<actions.UpdateContactAction>(actions.ContactsActionTypes.UPDATE_CONTACT),
      switchMap(action => this.contactsService.updateContact(action.payload).pipe(
        map(payload => new actions.UpdateContactCompleteAction(payload)),
        catchError(error => handleApiError(actions.UpdateContactFailedAction, error)),
      )));

  @Effect() removeContact$ = this.actions$.pipe(
      ofType<actions.RemoveContactAction>(actions.ContactsActionTypes.REMOVE_CONTACT),
      switchMap(action => this.contactsService.removeContact(action.payload).pipe(
        map(payload => new actions.RemoveContactCompleteAction(payload)),
        catchError(error => handleApiError(actions.RemoveContactFailedAction, error)),
      )));

  constructor(private actions$: Actions<actions.ContactsActions>,
              private store: Store<IContactsState>,
              private contactsService: ContactsService) {
  }
}
