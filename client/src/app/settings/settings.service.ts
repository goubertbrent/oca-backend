import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ServiceOpeningHours } from '../shared/interfaces/oca';
import { PrivacySettings, PrivacySettingsGroup, ServiceInfo } from './service-info/service-info';

@Injectable({ providedIn: 'root' })
export class SettingsService {
  constructor(private http: HttpClient) {
  }

  getOpeningHours() {
    return this.http.get<ServiceOpeningHours>('/common/settings/opening-hours');
  }

  saveOpeningHours(openingHours: ServiceOpeningHours) {
    return this.http.put<ServiceOpeningHours>('/common/settings/opening-hours', openingHours);
  }

  getServiceInfo(): Observable<ServiceInfo> {
    return this.http.get<ServiceInfo>('/common/service-info');
  }

  updateServiceInfo(info: ServiceInfo) {
    return this.http.put<ServiceInfo>('/common/service-info', info);
  }

  getPrivacySettings() {
    return this.http.get<PrivacySettingsGroup[]>('/common/settings/privacy');
  }

  savePrivacySettings(setting: PrivacySettings) {
    return this.http.put('/common/settings/privacy', setting);
  }
}
