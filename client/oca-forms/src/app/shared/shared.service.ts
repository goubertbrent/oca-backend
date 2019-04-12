import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Budget } from './billing/billing';
import { AppStatistics, ServiceIdentityInfo, ServiceMenuDetail } from './rogerthat';

@Injectable({ providedIn: 'root' })
export class SharedService {
  constructor(private http: HttpClient) {
  }

  getMenu() {
    return this.http.get<ServiceMenuDetail>('/common/get_menu');
  }

  getInfo() {
    return this.http.get <ServiceIdentityInfo>('/common/get_info');
  }

  getAppStatistics() {
    return this.http.get <AppStatistics[]>('/common/statistics/apps');
  }

  getBudget() {
    return this.http.get <Budget>('/common/billing/budget');
  }
}
