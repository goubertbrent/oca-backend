import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map } from 'rxjs/operators';
import { Contact } from '../interfaces';
import { ConsoleConfig } from './console-config';

@Injectable()
export class ContactsService {

  constructor(private http: HttpClient) {
  }

  getContacts() {
    return this.http.get<Contact[]>(`${ConsoleConfig.BUILDSERVER_API_URL}/contacts`);
  }

  createContact(payload: Contact) {
    return this.http.post<Contact>(`${ConsoleConfig.BUILDSERVER_API_URL}/contacts`, payload);
  }

  getContact(contactId: number) {
    return this.http.get<Contact>(`${ConsoleConfig.BUILDSERVER_API_URL}/contacts/${contactId}`);
  }

  updateContact(payload: Contact) {
    return this.http.put<Contact>(`${ConsoleConfig.BUILDSERVER_API_URL}/contacts/${payload.id}`, payload);
  }

  removeContact(payload: Contact) {
    return this.http.delete<Contact>(`${ConsoleConfig.BUILDSERVER_API_URL}/contacts/${payload.id}`)
      .pipe(map(() => payload));
  }
}
