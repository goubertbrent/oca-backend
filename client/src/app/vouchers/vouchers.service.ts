import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ExportVoucherServices, VoucherProviderId, VoucherService, VouchersServiceList } from './vouchers';

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

  saveProvider(serviceEmail: string, providers: VoucherProviderId[]) {
    return this.http.put<VoucherService>(`/common/vouchers/services/${serviceEmail}`, { providers });
  }

  exportServices() {
    return this.http.get<ExportVoucherServices>(`/common/vouchers/export`);
  }
}
