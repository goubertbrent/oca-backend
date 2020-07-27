import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { CirkloSettings, ExportVoucherServices, VoucherProviderId, VoucherService, VouchersServiceList } from './vouchers';

@Injectable({
  providedIn: 'root',
})
export class VouchersService {

  constructor(private http: HttpClient) {
  }

  getServices(organizationType: number, cursor: string | null, pageSize: number, sort: string) {
    let params = new HttpParams({ fromObject: { page_size: pageSize.toString(), sort } });
    if (cursor) {
      params = params.set('cursor', cursor);
    }
    return this.http.get<VouchersServiceList>(`/common/vouchers/services/${organizationType}`, { params });
  }

  saveProvider(serviceEmail: string, provider: VoucherProviderId, enabled: boolean) {
    return this.http.put<VoucherService>(`/common/vouchers/services/${serviceEmail}`, { provider, enabled });
  }

  exportServices() {
    return this.http.get<ExportVoucherServices>(`/common/vouchers/export`);
  }

  getCirkloSettings() {
    return this.http.get<CirkloSettings>(`/common/vouchers/cirklo`);
  }

  saveCirkloSettings(settings: CirkloSettings) {
    return this.http.put<CirkloSettings>(`/common/vouchers/cirklo`, settings);
  }
}
