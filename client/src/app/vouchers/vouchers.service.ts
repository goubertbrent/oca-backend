import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { CirkloSettings, VoucherService, VouchersServiceList } from './vouchers';

@Injectable({
  providedIn: 'root',
})
export class VouchersService {

  constructor(private http: HttpClient) {
  }

  getServices() {
    return this.http.get<VouchersServiceList>(`/common/vouchers/services`);
  }

  whitelistVoucherService(id: string, email: string, accepted: boolean) {
    return this.http.put<VoucherService>(`/common/vouchers/services/whitelist`, { id, email, accepted });
  }

  getCirkloSettings() {
    return this.http.get<CirkloSettings>(`/common/vouchers/cirklo`);
  }

  saveCirkloSettings(settings: CirkloSettings) {
    return this.http.put<CirkloSettings>(`/common/vouchers/cirklo`, settings);
  }
}
