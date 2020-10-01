import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map } from 'rxjs/operators';
import { CreateDeveloperAccountPayload, DeveloperAccount } from '../interfaces';
import { ConsoleConfig } from './console-config';

@Injectable()
export class DeveloperAccountsService {

  constructor(private http: HttpClient) {
  }

  baseUrl(developerOrganization: number) {
    return `${ConsoleConfig.BUILDSERVER_API_URL}/developer-accounts/${developerOrganization}`;
  }

  getDeveloperAccounts() {
    return this.http.get<DeveloperAccount[]>(ConsoleConfig.BUILDSERVER_API_URL + '/developer-accounts');
  }

  createDeveloperAccount(payload: CreateDeveloperAccountPayload) {
    return this.http.post<DeveloperAccount>(ConsoleConfig.BUILDSERVER_API_URL + '/developer-accounts', payload);
  }

  getDeveloperAccount(id: number) {
    return this.http.get<DeveloperAccount>(this.baseUrl(id));
  }

  updateDeveloperAccount(payload: DeveloperAccount) {
    const data = {
      ...payload,
      ios_dev_team: payload.ios_dev_team || null,
      iphone_distribution: payload.iphone_distribution || null,
      iphone_developer: payload.iphone_developer || null,
    };
    return this.http.put<DeveloperAccount>(this.baseUrl(payload.id), data);
  }

  removeDeveloperAccount(payload: DeveloperAccount) {
    return this.http.delete<DeveloperAccount>(this.baseUrl(payload.id)).pipe(map(() => payload));
  }
}
