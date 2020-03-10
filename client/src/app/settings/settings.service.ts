import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { AvailablePlaceType, OpeningHours } from '../shared/interfaces/oca';
import { ServiceInfo } from './service-info/service-info';

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
    return this.http.get<AvailablePlaceType[]>('/common/available-place-types');
  }
}
