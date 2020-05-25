import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { OpeningHours, PlaceType } from '../shared/interfaces/oca';
import { Country, PrivacySettings, ServiceInfo } from './service-info/service-info';

@Injectable({ providedIn: 'root' })
export class SettingsService {
  constructor(private http: HttpClient) {
  }

  getOpeningHours() {
    return this.http.get<OpeningHours>('/common/settings/opening-hours');
  }

  saveOpeningHours(openingHours: OpeningHours) {
    return this.http.put<OpeningHours>('/common/settings/opening-hours', openingHours);
  }

  getServiceInfo(): Observable<ServiceInfo> {
    return this.http.get<ServiceInfo>('/common/service-info');
  }

  updateServiceInfo(info: ServiceInfo) {
    return this.http.put<ServiceInfo>('/common/service-info', info);
  }

  getAvailablePlaceTypes() {
    return this.http.get<{ results: PlaceType[] }>('/common/available-place-types');
  }

  getCountries(): Observable<Country[]> {
    return this.http.get<{ countries: [string, string][] }>('/common/countries').pipe(
      map(results => results.countries.map(([code, name]) => ({ code, name }))),
    );
  }

  getPrivacySettings(): Observable<PrivacySettings[]> {
    return this.http.get<PrivacySettings[]>('/common/settings/privacy');
  }

  savePrivacySettings(setting: PrivacySettings) {
    return this.http.put('/common/settings/privacy', setting);
  }
}
